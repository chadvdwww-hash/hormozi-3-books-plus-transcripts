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


TS_INLINE_RE = re.compile(r"<<TS:([\d.]+)>>")


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


def chunk_with_timestamps(text: str, chunk_size: int, overlap: int) -> list[tuple[str, float | None]]:
    """Word-based chunking that preserves the first timestamp of each chunk.

    Input text has inline <<TS:NN.NN>> markers from read_transcript_with_timestamps.
    For each chunk, finds the first timestamp marker and records its seconds,
    then strips all markers from the chunk text.

    Returns list of (clean_text, start_seconds_or_None).
    """
    words = text.split()
    if not words:
        return []
    chunks: list[tuple[str, float | None]] = []
    step = max(1, chunk_size - overlap)
    for start in range(0, len(words), step):
        raw_piece = " ".join(words[start : start + chunk_size])
        # First timestamp in this chunk:
        first_ts = None
        m = TS_INLINE_RE.search(raw_piece)
        if m:
            try:
                first_ts = float(m.group(1))
            except ValueError:
                first_ts = None
        # Strip all timestamp markers:
        clean_piece = TS_INLINE_RE.sub("", raw_piece)
        clean_piece = re.sub(r"\s+", " ", clean_piece).strip()
        if len(clean_piece.split()) < 30:
            continue
        chunks.append((clean_piece, first_ts))
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


TIMESTAMP_LINE_RE = re.compile(r"^\s*\[\s*([\d.:]+)\s*\]\s*(.*)$")


def read_transcript(path: Path) -> tuple[str, dict]:
    """YouTube transcript .txt files with `# Title: ...` / `# Video ID: ...` headers
    and `[ 12.34] text` lines.

    Embeds timestamps as `<<TS:NN.NN>>` markers inline so chunk_with_timestamps
    can extract the first timestamp per chunk. Header metadata captured separately.
    """
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
        ts_match = TIMESTAMP_LINE_RE.match(line)
        if ts_match:
            ts_str, content = ts_match.group(1), ts_match.group(2).strip()
            # Convert HH:MM:SS or MM:SS or SS.ss to seconds
            try:
                if ":" in ts_str:
                    parts = ts_str.split(":")
                    total = 0.0
                    for p in parts:
                        total = total * 60 + float(p)
                    ts_seconds = total
                else:
                    ts_seconds = float(ts_str)
                if content:
                    body_lines.append(f"<<TS:{ts_seconds:.2f}>>{content}")
            except ValueError:
                if content:
                    body_lines.append(content)
        else:
            stripped = line.strip()
            if stripped:
                body_lines.append(stripped)
    # Don't run clean() here because it would collapse the timestamp markers' formatting
    # The markers will be stripped during chunking.
    body = " ".join(body_lines)
    body = re.sub(r"[​‌‍﻿]", "", body)
    return body, meta


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

            if meta.get("kind") == "transcript":
                # Transcript: preserve first-timestamp per chunk + build a deep-link URL
                ts_chunks = chunk_with_timestamps(text, chunk_size, overlap)
                video_id = meta.get("video_id")
                base_url = meta.get("url", "")
                for idx, (chunk_text_str, start_seconds) in enumerate(ts_chunks):
                    record = {
                        "id": f"{meta['kind']}::{source_name}::{idx:04d}",
                        "text": chunk_text_str,
                        "source": source_name,
                        "chunk_idx": idx,
                        **meta,
                    }
                    if start_seconds is not None:
                        record["start_seconds"] = round(start_seconds, 2)
                        # YouTube deep link: ?t=NNNs (integer seconds for cleaner URL)
                        if video_id:
                            record["deep_link"] = f"https://www.youtube.com/watch?v={video_id}&t={int(start_seconds)}s"
                        elif base_url:
                            sep = "&" if "?" in base_url else "?"
                            record["deep_link"] = f"{base_url}{sep}t={int(start_seconds)}s"
                    records.append(record)
            else:
                # Books, PDFs, plain text: no timestamps
                # Run clean() here since transcript path skipped it
                clean_text = clean(text)
                chunks = chunk_text(clean_text, chunk_size, overlap)
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
