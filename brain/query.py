#!/usr/bin/env python3
"""Hybrid retrieval over the local brain.

Combines dense semantic search (BGE embeddings + cosine similarity) with
keyword search (BM25) using Reciprocal Rank Fusion, then re-ranks the fused
candidates with Maximal Marginal Relevance for diversity.

Loads three files:
  brain/index.npz     dense embeddings (required)
  brain/chunks.jsonl  source text + metadata per chunk (required)
  brain/bm25.pkl      keyword index, built by brain/build_bm25.py (optional;
                      if absent, retrieval falls back to dense-only mode)

Usage:
  python brain/query.py "should I raise prices?"
  python brain/query.py "objection: too expensive" --top-k 8
  python brain/query.py "lead capture" --format text

Batch (one model load, many queries; used by /audit's 15 dimensions):
  python brain/query.py --batch "raise prices" "value equation" "guarantees"

Flags:
  --top-k N             how many results (default 5)
  --candidate-pool N    how many candidates to fuse before re-rank (default 30)
  --mmr-lambda 0.0-1.0  diversity vs relevance balance (default 0.7)
  --no-mmr              disable MMR (pure ranking)
  --no-bm25             disable BM25 fusion (dense-only mode)
  --format json|text    output shape (default json)
"""
from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
from pathlib import Path

import numpy as np

try:
    from fastembed import TextEmbedding
except ImportError:
    sys.exit("fastembed missing. Install with: pip3 install fastembed (or run ./setup.sh)")


HERE = Path(__file__).resolve().parent
INDEX_PATH = HERE / "index.npz"
CHUNKS_PATH = HERE / "chunks.jsonl"
BM25_PATH = HERE / "bm25.pkl"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _die(msg: str, hint: str | None = None) -> None:
    print(f"error: {msg}", file=sys.stderr)
    if hint:
        print(f"  fix: {hint}", file=sys.stderr)
    sys.exit(1)


def load_index() -> tuple[np.ndarray, list[dict]]:
    """Load dense embeddings and chunks. Validates shape and integrity."""
    if not INDEX_PATH.exists():
        _die(
            "brain/index.npz missing",
            "Re-clone the repo (index ships pre-built), or rebuild via "
            "`python3 brain/ingest.py --source <dir>`.",
        )
    if not CHUNKS_PATH.exists():
        _die(
            "brain/chunks.jsonl missing",
            "Re-clone the repo, or rebuild via `python3 brain/ingest.py --source <dir>`.",
        )

    try:
        embeddings = np.load(INDEX_PATH)["embeddings"]
    except Exception as exc:
        _die(f"failed to load brain/index.npz: {exc}", "Re-clone the repo.")

    if embeddings.ndim != 2 or embeddings.shape[1] != EMBED_DIM:
        _die(
            f"brain/index.npz has shape {embeddings.shape}; expected (N, {EMBED_DIM})",
            "Rebuild the index with the current ingest.py.",
        )

    chunks: list[dict] = []
    try:
        with CHUNKS_PATH.open() as fh:
            for i, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    _die(f"chunks.jsonl line {i} is invalid JSON: {exc}", "Re-clone the repo.")
    except OSError as exc:
        _die(f"could not read chunks.jsonl: {exc}", None)

    if len(chunks) != embeddings.shape[0]:
        _die(
            f"index/chunks size mismatch: {embeddings.shape[0]} vectors vs {len(chunks)} chunks",
            "Rebuild the index: `python3 brain/ingest.py --source <dir>`.",
        )

    return embeddings, chunks


def load_bm25():
    """Load the BM25 keyword index if present. Returns None if missing or unusable."""
    if not BM25_PATH.exists():
        return None
    try:
        with BM25_PATH.open("rb") as fh:
            payload = pickle.load(fh)
        return payload.get("bm25")
    except Exception:
        # corrupted bm25 file: degrade gracefully to dense-only
        return None


def mmr_rerank(query_vec, candidate_vecs, candidate_scores, top_k, lambda_param=0.7):
    """Maximal Marginal Relevance re-ranking. Balances relevance with diversity."""
    n = candidate_vecs.shape[0]
    if n <= top_k:
        return list(range(n))

    with np.errstate(all="ignore"):
        pairwise = candidate_vecs @ candidate_vecs.T
    pairwise = np.nan_to_num(pairwise, nan=0.0, posinf=0.0, neginf=0.0)

    selected = [int(np.argmax(candidate_scores))]
    remaining = set(range(n)) - {selected[0]}

    while len(selected) < top_k and remaining:
        best_idx, best_mmr = None, -np.inf
        for idx in remaining:
            relevance = float(candidate_scores[idx])
            diversity_penalty = float(max(pairwise[idx, s] for s in selected))
            mmr = lambda_param * relevance - (1.0 - lambda_param) * diversity_penalty
            if mmr > best_mmr:
                best_mmr, best_idx = mmr, idx
        selected.append(best_idx)
        remaining.remove(best_idx)
    return selected


def reciprocal_rank_fusion(
    dense_ranking: list[int], bm25_ranking: list[int], k: int = 60
) -> list[tuple[int, float]]:
    """RRF: combine two rankings into a single score per document.
    Higher score = better. Returns list of (doc_idx, score) sorted descending."""
    scores: dict[int, float] = {}
    for rank, idx in enumerate(dense_ranking, 1):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    for rank, idx in enumerate(bm25_ranking, 1):
        scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


def search(
    embeddings: np.ndarray,
    chunks: list[dict],
    query_text: str,
    query_vec: np.ndarray,
    top_k: int = 5,
    mmr_lambda: float = 0.7,
    candidate_pool: int = 30,
    bm25=None,
) -> list[dict]:
    """Hybrid retrieval: dense + BM25 + RRF + MMR re-rank.

    Returns top_k chunks with combined score and metadata. Gracefully degrades
    to dense-only mode if bm25 is None.
    """
    if not query_text or not query_text.strip():
        return []

    # --- Dense retrieval ---
    query_vec = np.nan_to_num(query_vec, nan=0.0, posinf=0.0, neginf=0.0)
    norm = float(np.linalg.norm(query_vec))
    if norm > 0:
        query_vec = query_vec / norm

    with np.errstate(all="ignore"):
        dense_scores = embeddings @ query_vec
    dense_scores = np.nan_to_num(dense_scores, nan=-1.0, posinf=-1.0, neginf=-1.0)
    pool_size = min(candidate_pool, embeddings.shape[0])
    dense_top = np.argsort(-dense_scores)[:pool_size].tolist()

    # --- BM25 retrieval (optional) ---
    fused: list[int]
    if bm25 is not None:
        try:
            bm25_scores = bm25.get_scores(tokenize(query_text))
            bm25_top = np.argsort(-bm25_scores)[:pool_size].tolist()
            rrf = reciprocal_rank_fusion(dense_top, bm25_top)
            fused = [idx for idx, _ in rrf[:pool_size]]
        except Exception:
            # any BM25 failure: fall back to dense-only
            fused = dense_top
    else:
        fused = dense_top

    # --- MMR re-rank ---
    fused_vecs = embeddings[fused]
    fused_dense_scores = dense_scores[fused]
    if mmr_lambda < 1.0 and len(fused) > top_k:
        selected = mmr_rerank(query_vec, fused_vecs, fused_dense_scores, top_k, mmr_lambda)
        final_indices = [int(fused[s]) for s in selected]
    else:
        final_indices = [int(i) for i in fused[:top_k]]

    return [
        {
            "rank": rank,
            "score": float(dense_scores[idx]),
            "source": chunks[idx].get("source", ""),
            "kind": chunks[idx].get("kind", ""),
            "id": chunks[idx].get("id", ""),
            "url": chunks[idx].get("url", ""),
            "text": chunks[idx]["text"],
        }
        for rank, idx in enumerate(final_indices, 1)
    ]


def main():
    parser = argparse.ArgumentParser(description="Hybrid retrieval over the local brain.")
    parser.add_argument("queries", nargs="+", help="one or more natural-language queries")
    parser.add_argument("--top-k", type=int, default=5, help="how many results per query (default 5)")
    parser.add_argument("--candidate-pool", type=int, default=30,
                        help="candidate pool size before MMR re-rank (default 30)")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--batch", action="store_true",
                        help="explicit batch mode (multiple queries returned as dict)")
    parser.add_argument("--mmr-lambda", type=float, default=0.7,
                        help="MMR balance: 1.0=pure relevance, 0.0=pure diversity (default 0.7)")
    parser.add_argument("--no-mmr", action="store_true", help="disable MMR re-ranking")
    parser.add_argument("--no-bm25", action="store_true", help="dense-only retrieval (skip BM25)")
    args = parser.parse_args()

    if any(not q.strip() for q in args.queries):
        _die("one or more queries are empty", "Quote your query: python3 brain/query.py \"...\"")

    embeddings, chunks = load_index()
    embeddings = np.nan_to_num(embeddings, nan=0.0, posinf=0.0, neginf=0.0)
    mmr_lambda = 1.0 if args.no_mmr else args.mmr_lambda
    bm25 = None if args.no_bm25 else load_bm25()

    try:
        embedder = TextEmbedding(model_name=EMBED_MODEL)
    except Exception as exc:
        _die(
            f"could not load embedding model: {exc}",
            "Run `./setup.sh` or check your internet connection (model is cached after first download).",
        )

    query_vecs = list(embedder.embed(args.queries))

    if len(args.queries) == 1 and not args.batch:
        results = search(
            embeddings, chunks, args.queries[0], query_vecs[0],
            top_k=args.top_k, mmr_lambda=mmr_lambda,
            candidate_pool=args.candidate_pool, bm25=bm25,
        )
        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            mode = "hybrid (dense + bm25)" if bm25 is not None else "dense-only"
            print(f"# retrieval mode: {mode}")
            for r in results:
                kind = r.get("kind", "")
                print(f"\n--- #{r['rank']}  score={r['score']:.3f}  source={r['source']} ({kind}) ---")
                print(r["text"])
        return

    batch = {}
    for query, vec in zip(args.queries, query_vecs):
        batch[query] = search(
            embeddings, chunks, query, vec,
            top_k=args.top_k, mmr_lambda=mmr_lambda,
            candidate_pool=args.candidate_pool, bm25=bm25,
        )

    if args.format == "json":
        print(json.dumps(batch, indent=2))
    else:
        mode = "hybrid (dense + bm25)" if bm25 is not None else "dense-only"
        print(f"# retrieval mode: {mode}")
        for query, results in batch.items():
            print(f"\n=== query: {query} ===")
            for r in results:
                print(f"--- #{r['rank']}  score={r['score']:.3f}  source={r['source']} ---")
                print(r["text"][:300] + ("..." if len(r["text"]) > 300 else ""))


if __name__ == "__main__":
    main()
