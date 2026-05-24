#!/usr/bin/env python3
"""Ingest Hormozi corpus into a local vector index.

Reads from one or more source directories. Handles .md (preferred), .pdf, and .txt
(YouTube transcript format with `# Title:` / `# Video ID:` headers). Chunks each
document, embeds chunks with fastembed (BAAI/bge-small-en-v1.5, 384 dim), and
writes:

  brain/index.npz       compressed numpy array of all embeddings, shape (N, 384)
  brain/chunks.jsonl    one JSON object per line: {id, text, source, kind, ...}

Usage:
  python brain/ingest.py --source /path/to/dir1 --source /path/to/dir2
  python brain/ingest.py --source /path/to/markdowns --chunk-size 400 --overlap 80

Re-run to rebuild from scratch. Idempotent.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None  # PDF support optional

try:
    from fastembed import TextEmbedding
except ImportError:
    sys.exit("fastembed missing. Install with: pip install fastembed")


HERE = Path(__file__).resolve().parent
INDEX_PATH = HERE / "index.npz"
CHUNKS_PATH = HERE / "chunks.jsonl"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
TIMESTAMP_RE = re.compile(r"^\s*\[\s*[\d.:]+\s*\]\s*")
TRANSCRIPT_HEADER_RE = re.compile(r"^#\s+(\w[\w ]*?):\s*(.+)$")


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[​‌‍﻿]", "", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Word-based chunking. chunk_size and overlap are in words."""
    words = text.split()
    if not words:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + chunk_size])
        if len(piece.split()) < 30:
            continue
        chunks.append(piece)
        if start + chunk_size >= len(words):
            break
    return chunks


def read_markdown(path: Path) -> tuple[str, dict]:
    raw = path.read_text(errors="ignore")
    # Strip markdown image lines and excessive heading markers; preserve prose.
    raw = re.sub(r"!\[.*?\]\(.*?\)", "", raw)
    raw = re.sub(r"^#+\s+", "", raw, flags=re.MULTILINE)
    return clean(raw), {"kind": "markdown"}


def read_pdf(path: Path) -> tuple[str, dict]:
    if fitz is None:
        return "", {"kind": "pdf", "skipped": "pymupdf not installed"}
    parts = []
    with fitz.open(path) as doc:
        for page in doc:
            txt = clean(page.get_text("text"))
            if len(txt) > 100:
                parts.append(txt)
    return " ".join(parts), {"kind": "pdf"}


def read_transcript(path: Path) -> tuple[str, dict]:
    """YouTube transcript .txt files with `# Title: ...` / `# Video ID: ...` headers
    and `[ 12.34] text` lines. Strip timestamps, capture metadata."""
    raw = path.read_text(errors="ignore")
    meta: dict = {"kind": "transcript"}
    body_lines = []
    for line in raw.splitlines():
        if line.startswith("#"):
            m = TRANSCRIPT_HEADER_RE.match(line)
            if m:
                key = m.group(1).strip().lower().replace(" ", "_")
                meta[key] = m.group(2).strip()
            continue
        clean_line = TIMESTAMP_RE.sub("", line).strip()
        if clean_line:
            body_lines.append(clean_line)
    return clean(" ".join(body_lines)), meta


def read_text(path: Path) -> tuple[str, dict]:
    """Plain text fallback. Detects transcript format by presence of `# Video ID:`."""
    head = path.read_text(errors="ignore")[:500]
    if "# Video ID:" in head or "# Title:" in head:
        return read_transcript(path)
    return clean(path.read_text(errors="ignore")), {"kind": "text"}


READERS = {
    ".md": read_markdown,
    ".pdf": read_pdf,
    ".txt": read_text,
}


def build_corpus(source_dirs: list[Path], chunk_size: int, overlap: int) -> list[dict]:
    records: list[dict] = []
    for source_dir in source_dirs:
        files = []
        for ext in READERS:
            files.extend(source_dir.rglob(f"*{ext}"))
        files = sorted(files)
        print(f"\n[{source_dir.name}] {len(files)} files", flush=True)
        for path in files:
            reader = READERS[path.suffix.lower()]
            try:
                text, meta = reader(path)
            except Exception as exc:
                print(f"  skipped {path.name}: {exc}", flush=True)
                continue
            if not text:
                continue
            source_name = path.stem.lstrip("_").strip()
            chunks = chunk_text(text, chunk_size, overlap)
            for idx, chunk in enumerate(chunks):
                record = {
                    "id": f"{meta['kind']}::{source_name}::{idx:04d}",
                    "text": chunk,
                    "source": source_name,
                    "chunk_idx": idx,
                    **meta,
                }
                records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", action="append", required=True, type=Path,
                        help="source directory (can be specified multiple times)")
    parser.add_argument("--chunk-size", type=int, default=400, help="words per chunk")
    parser.add_argument("--overlap", type=int, default=80, help="word overlap between chunks")
    parser.add_argument("--batch-size", type=int, default=64)
    args = parser.parse_args()

    for src in args.source:
        if not src.exists():
            sys.exit(f"source not found: {src}")

    t0 = time.time()
    records = build_corpus(args.source, args.chunk_size, args.overlap)
    print(f"\nBuilt {len(records)} chunks in {time.time()-t0:.1f}s", flush=True)
    if not records:
        sys.exit("no chunks produced; aborting")

    print(f"Loading embedding model {EMBED_MODEL} ...", flush=True)
    embedder = TextEmbedding(model_name=EMBED_MODEL)

    print(f"Embedding {len(records)} chunks in batches of {args.batch_size} ...", flush=True)
    texts = [r["text"] for r in records]
    embeddings = np.zeros((len(records), EMBED_DIM), dtype=np.float32)

    t1 = time.time()
    cursor = 0
    for vec in embedder.embed(texts, batch_size=args.batch_size):
        embeddings[cursor] = vec
        cursor += 1
        if cursor % 1000 == 0:
            elapsed = time.time() - t1
            rate = cursor / elapsed if elapsed > 0 else 0
            eta = (len(records) - cursor) / rate if rate > 0 else 0
            print(f"  {cursor}/{len(records)} ({rate:.1f}/s, ETA {eta:.0f}s)", flush=True)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    np.savez_compressed(INDEX_PATH, embeddings=embeddings)
    with CHUNKS_PATH.open("w") as fh:
        for record in records:
            fh.write(json.dumps(record) + "\n")

    print(f"\nWrote {INDEX_PATH} ({embeddings.nbytes/1e6:.1f} MB raw, compressed on disk)", flush=True)
    print(f"Wrote {CHUNKS_PATH} ({CHUNKS_PATH.stat().st_size/1e6:.1f} MB)", flush=True)
    print(f"Total time: {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
