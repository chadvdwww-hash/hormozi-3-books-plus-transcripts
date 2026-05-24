#!/usr/bin/env python3
"""Query the Hormozi vector index.

Loads brain/index.npz and brain/chunks.jsonl, embeds the query (or queries),
and returns the top-k semantically similar chunks as JSON.

Single query:
  python brain/query.py "should I raise prices?"
  python brain/query.py "objection: too expensive" --top-k 8
  python brain/query.py "lead capture" --format text

Batch (one model load, many queries — use for /audit's 15 dimensions):
  python brain/query.py --batch "raise prices" "value equation" "guarantees"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

try:
    from fastembed import TextEmbedding
except ImportError:
    sys.exit("fastembed missing. Install with: pip install fastembed")


HERE = Path(__file__).resolve().parent
INDEX_PATH = HERE / "index.npz"
CHUNKS_PATH = HERE / "chunks.jsonl"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


def load_index() -> tuple[np.ndarray, list[dict]]:
    if not INDEX_PATH.exists() or not CHUNKS_PATH.exists():
        sys.exit(
            "Index not built. Run: python brain/ingest.py --source /path/to/hormozi-pdfs"
        )
    embeddings = np.load(INDEX_PATH)["embeddings"]
    chunks = []
    with CHUNKS_PATH.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    if len(chunks) != embeddings.shape[0]:
        sys.exit(
            f"index/chunks mismatch: {embeddings.shape[0]} vectors vs {len(chunks)} chunks"
        )
    return embeddings, chunks


def mmr_rerank(query_vec, candidate_vecs, candidate_scores, top_k, lambda_param=0.7):
    """Maximal Marginal Relevance re-ranking.

    Balances relevance to query (similarity to query_vec) with diversity from
    already-selected results. lambda=1.0 reduces to pure cosine; lambda=0.0
    maximizes diversity. Default 0.7 leans toward relevance.
    """
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


def search(embeddings, chunks, query_vec, top_k, mmr_lambda=0.7, candidate_pool=4):
    query_vec = np.nan_to_num(query_vec, nan=0.0, posinf=0.0, neginf=0.0)
    norm = float(np.linalg.norm(query_vec))
    if norm > 0:
        query_vec = query_vec / norm
    with np.errstate(all="ignore"):
        scores = embeddings @ query_vec
    scores = np.nan_to_num(scores, nan=-1.0, posinf=-1.0, neginf=-1.0)

    # Pull top (candidate_pool * top_k) by cosine, then MMR-rerank down to top_k.
    pool_size = min(top_k * candidate_pool, embeddings.shape[0])
    pool_indices = np.argsort(-scores)[:pool_size]
    pool_vecs = embeddings[pool_indices]
    pool_scores = scores[pool_indices]

    if mmr_lambda < 1.0 and pool_size > top_k:
        selected = mmr_rerank(query_vec, pool_vecs, pool_scores, top_k, mmr_lambda)
        final_indices = [int(pool_indices[s]) for s in selected]
    else:
        final_indices = [int(i) for i in pool_indices[:top_k]]

    return [
        {
            "rank": rank,
            "score": float(scores[idx]),
            "source": chunks[idx].get("source", ""),
            "kind": chunks[idx].get("kind", ""),
            "id": chunks[idx].get("id", ""),
            "text": chunks[idx]["text"],
        }
        for rank, idx in enumerate(final_indices, 1)
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("queries", nargs="+", help="one or more queries")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--batch", action="store_true", help="explicit batch mode (multiple queries)")
    parser.add_argument("--mmr-lambda", type=float, default=0.7,
                        help="MMR balance: 1.0=pure relevance, 0.0=pure diversity (default 0.7)")
    parser.add_argument("--no-mmr", action="store_true", help="disable MMR re-ranking")
    args = parser.parse_args()

    embeddings, chunks = load_index()
    embeddings = np.nan_to_num(embeddings, nan=0.0, posinf=0.0, neginf=0.0)
    mmr_lambda = 1.0 if args.no_mmr else args.mmr_lambda

    embedder = TextEmbedding(model_name=EMBED_MODEL)
    query_vecs = list(embedder.embed(args.queries))

    if len(args.queries) == 1 and not args.batch:
        results = search(embeddings, chunks, query_vecs[0], args.top_k, mmr_lambda=mmr_lambda)
        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            for r in results:
                kind = r.get("kind", "")
                print(f"\n--- #{r['rank']}  score={r['score']:.3f}  source={r['source']} ({kind}) ---")
                print(r["text"])
        return

    batch = {}
    for query, vec in zip(args.queries, query_vecs):
        batch[query] = search(embeddings, chunks, vec, args.top_k, mmr_lambda=mmr_lambda)

    if args.format == "json":
        print(json.dumps(batch, indent=2))
    else:
        for query, results in batch.items():
            print(f"\n=== query: {query} ===")
            for r in results:
                print(f"--- #{r['rank']}  score={r['score']:.3f}  source={r['source']} ---")
                print(r["text"][:300] + ("..." if len(r["text"]) > 300 else ""))


if __name__ == "__main__":
    main()
