#!/usr/bin/env python3
"""Build a BM25 keyword index over the existing chunks.

Reads brain/chunks.jsonl, tokenizes each chunk, and saves a BM25 model to
brain/bm25.pkl. Pair this with the dense vector index in brain/index.npz for
hybrid retrieval in query.py (semantic + keyword, fused via reciprocal rank).

Run once after ingest.py, or any time chunks.jsonl changes.

Usage:
  python3 brain/build_bm25.py
"""
from __future__ import annotations

import json
import pickle
import re
import sys
import time
from pathlib import Path

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    sys.exit(
        "rank_bm25 missing. Install with: pip3 install rank-bm25\n"
        "Or just re-run ./setup.sh which now installs it."
    )


HERE = Path(__file__).resolve().parent
CHUNKS_PATH = HERE / "chunks.jsonl"
BM25_PATH = HERE / "bm25.pkl"

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenization, lowercased."""
    return TOKEN_RE.findall(text.lower())


def main():
    if not CHUNKS_PATH.exists():
        sys.exit(f"missing: {CHUNKS_PATH}. Run brain/ingest.py first.")

    print(f"Loading chunks from {CHUNKS_PATH.name} ...", flush=True)
    chunks = []
    with CHUNKS_PATH.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    print(f"  {len(chunks):,} chunks loaded", flush=True)

    print("Tokenizing ...", flush=True)
    t0 = time.time()
    tokenized = [tokenize(c["text"]) for c in chunks]
    print(f"  done in {time.time() - t0:.1f}s", flush=True)

    print("Building BM25 index ...", flush=True)
    t0 = time.time()
    bm25 = BM25Okapi(tokenized)
    print(f"  done in {time.time() - t0:.1f}s", flush=True)

    print(f"Saving to {BM25_PATH.name} ...", flush=True)
    with BM25_PATH.open("wb") as fh:
        pickle.dump({"bm25": bm25, "n_chunks": len(chunks)}, fh, protocol=pickle.HIGHEST_PROTOCOL)
    size_mb = BM25_PATH.stat().st_size / (1024 * 1024)
    print(f"  wrote {BM25_PATH} ({size_mb:.1f} MB)", flush=True)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
