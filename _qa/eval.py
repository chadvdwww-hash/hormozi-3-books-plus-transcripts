#!/usr/bin/env python3
"""Retrieval quality eval.

Loads _qa/eval-queries.json, runs each query against the vector index, and
checks whether at least one of the expected_sources appears in the top-k.

Reports:
  - per-query pass/fail
  - overall pass rate
  - mean reciprocal rank (where 1.0 = expected source was rank #1)

Run after every re-ingestion to catch retrieval drift.

Usage:
  python3 _qa/eval.py
  python3 _qa/eval.py --verbose       # show retrieved sources for failures
  python3 _qa/eval.py --no-mmr        # disable MMR re-ranking for the eval
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BRAIN = ROOT / "brain"
EVAL_PATH = HERE / "eval-queries.json"

sys.path.insert(0, str(BRAIN))
try:
    from query import load_index, load_bm25, search, EMBED_MODEL
except ImportError as exc:
    sys.exit(f"could not import brain/query.py: {exc}")

try:
    from fastembed import TextEmbedding
except ImportError:
    sys.exit("fastembed missing. pip3 install fastembed")


def normalize_source(s: str) -> str:
    """Loose match: strip $ prefix, lowercase, collapse whitespace."""
    return s.lstrip("$").lower().strip()


def reciprocal_rank(results: list[dict], expected_sources: list[str]) -> float:
    expected_norm = {normalize_source(s) for s in expected_sources}
    for r in results:
        if normalize_source(r["source"]) in expected_norm:
            return 1.0 / r["rank"]
    return 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--no-mmr", action="store_true")
    parser.add_argument("--no-bm25", action="store_true", help="dense-only baseline")
    args = parser.parse_args()

    if not EVAL_PATH.exists():
        sys.exit(f"missing: {EVAL_PATH}")

    spec = json.loads(EVAL_PATH.read_text())
    queries = spec["queries"]
    top_k = spec.get("top_k", 5)
    mmr_lambda = 1.0 if args.no_mmr else 0.7

    print(f"Loading index ...", flush=True)
    embeddings, chunks = load_index()
    embeddings = np.nan_to_num(embeddings, nan=0.0, posinf=0.0, neginf=0.0)
    bm25 = None if args.no_bm25 else load_bm25()
    mode = "hybrid (dense + bm25)" if bm25 is not None else "dense-only"
    embedder = TextEmbedding(model_name=EMBED_MODEL)

    print(f"Running {len(queries)} queries (top_k={top_k}, mmr_lambda={mmr_lambda}, mode={mode}) ...", flush=True)
    query_texts = [q["query"] for q in queries]
    query_vecs = list(embedder.embed(query_texts))

    passes = 0
    rr_sum = 0.0
    failures: list[dict] = []

    for q, vec in zip(queries, query_vecs):
        results = search(
            embeddings, chunks, q["query"], vec,
            top_k=top_k, mmr_lambda=mmr_lambda, bm25=bm25,
        )
        rr = reciprocal_rank(results, q["expected_sources"])
        rr_sum += rr
        passed = rr > 0
        if passed:
            passes += 1
        else:
            failures.append({"q": q, "results": results})
        mark = "PASS" if passed else "FAIL"
        topline = f"  [{mark}] rr={rr:.2f}  {q['topic']:<22} -> {q['query'][:60]}"
        print(topline, flush=True)

    n = len(queries)
    pass_rate = 100.0 * passes / n if n else 0.0
    mrr = rr_sum / n if n else 0.0
    print()
    print(f"Pass rate: {passes}/{n} ({pass_rate:.1f}%)")
    print(f"MRR:       {mrr:.3f}  (1.0 = expected source always at rank #1)")

    if args.verbose and failures:
        print()
        print("=== Failures (retrieved top sources) ===")
        for f in failures:
            q = f["q"]
            print(f"\nFAILED: {q['query']}")
            print(f"  Expected one of: {q['expected_sources']}")
            print(f"  Got:")
            for r in f["results"]:
                kind = r.get("kind", "")
                print(f"    #{r['rank']} ({r['score']:.3f}) {r['source']} [{kind}]")


if __name__ == "__main__":
    main()
