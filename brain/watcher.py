#!/usr/bin/env python3
"""Daily watcher for new Alex Hormozi YouTube videos.

Subcommands:
  run        Check the channel for new videos, fetch transcripts, embed, append to index.
  install    Install a macOS launchd job that runs `run` every morning at 08:00.
  uninstall  Remove the launchd job.
  status     Show last run time, number of videos tracked, whether the job is loaded.

State lives in brain/.watcher-state.json. Logs to brain/.watcher.log.

Opt-in. The folder ships with this script but does not auto-install the schedule.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    from fastembed import TextEmbedding
except ImportError:
    sys.exit("fastembed missing. Install with: pip3 install fastembed")

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
except ImportError:
    sys.exit("youtube-transcript-api missing. Install with: pip3 install youtube-transcript-api")


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
INDEX_PATH = HERE / "index.npz"
CHUNKS_PATH = HERE / "chunks.jsonl"
STATE_PATH = HERE / ".watcher-state.json"
LOG_PATH = HERE / ".watcher.log"
CHANNEL_URL = "https://www.youtube.com/@AlexHormozi/videos"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
EMBED_DIM = 384
LAUNCH_AGENT_ID = "com.hormoziBusinessOS.watcher"
LAUNCH_AGENT_PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCH_AGENT_ID}.plist"


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as fh:
        fh.write(line + "\n")


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {"seen_video_ids": [], "last_check": None, "last_added": []}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2))


def list_channel_videos(limit: int = 30) -> list[dict]:
    """Return the most recent N videos as [{id, title, upload_date}, ...]."""
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(limit),
        "--print", "%(id)s\t%(title)s\t%(upload_date)s",
        CHANNEL_URL,
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
    except subprocess.CalledProcessError as exc:
        log(f"yt-dlp failed: {exc.stderr.strip()[:200]}")
        return []
    except subprocess.TimeoutExpired:
        log("yt-dlp timed out after 120s")
        return []
    except FileNotFoundError:
        log("yt-dlp not installed. brew install yt-dlp")
        return []

    videos = []
    for line in out.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 1 and parts[0]:
            videos.append({
                "id": parts[0],
                "title": parts[1] if len(parts) > 1 else "",
                "upload_date": parts[2] if len(parts) > 2 else "",
            })
    return videos


def fetch_transcript(video_id: str) -> str | None:
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
        log(f"  no transcript for {video_id}: {type(exc).__name__}")
        return None
    except Exception as exc:
        log(f"  transcript error for {video_id}: {exc}")
        return None
    return " ".join(seg["text"] for seg in segments if seg.get("text")).strip()


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
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


def append_to_index(new_chunks: list[dict]) -> None:
    """Append new chunks to chunks.jsonl and new embeddings to index.npz."""
    if not new_chunks:
        return

    log(f"Embedding {len(new_chunks)} new chunks ...")
    embedder = TextEmbedding(model_name=EMBED_MODEL)
    new_vecs = np.zeros((len(new_chunks), EMBED_DIM), dtype=np.float32)
    for i, vec in enumerate(embedder.embed([c["text"] for c in new_chunks])):
        new_vecs[i] = vec
    norms = np.linalg.norm(new_vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    new_vecs = new_vecs / norms

    if INDEX_PATH.exists():
        existing = np.load(INDEX_PATH)["embeddings"]
        combined = np.vstack([existing, new_vecs])
    else:
        combined = new_vecs
    np.savez_compressed(INDEX_PATH, embeddings=combined)

    with CHUNKS_PATH.open("a") as fh:
        for chunk in new_chunks:
            fh.write(json.dumps(chunk) + "\n")

    log(f"Index now has {combined.shape[0]} vectors")


def cmd_run(args) -> None:
    log(f"Watcher run started")
    state = load_state()
    seen = set(state.get("seen_video_ids", []))

    videos = list_channel_videos(limit=args.limit)
    if not videos:
        log("No videos returned. Aborting.")
        return

    new_videos = [v for v in videos if v["id"] not in seen]
    log(f"Channel returned {len(videos)} recent videos, {len(new_videos)} new")

    new_chunks = []
    added_videos = []
    for v in new_videos:
        log(f"Fetching transcript: {v['id']} ({v['title'][:60]})")
        transcript = fetch_transcript(v["id"])
        if not transcript:
            seen.add(v["id"])
            continue
        chunks = chunk_text(transcript)
        for idx, chunk in enumerate(chunks):
            new_chunks.append({
                "id": f"transcript::{v['id']}::{idx:04d}",
                "text": chunk,
                "source": v["title"],
                "kind": "transcript",
                "video_id": v["id"],
                "url": f"https://www.youtube.com/watch?v={v['id']}",
                "upload_date": v.get("upload_date", ""),
                "chunk_idx": idx,
            })
        seen.add(v["id"])
        added_videos.append(v)
        log(f"  + {len(chunks)} chunks from {v['id']}")

    if new_chunks:
        append_to_index(new_chunks)

    state["seen_video_ids"] = sorted(seen)
    state["last_check"] = datetime.now().isoformat(timespec="seconds")
    state["last_added"] = [{"id": v["id"], "title": v["title"]} for v in added_videos]
    save_state(state)

    log(f"Watcher run complete. {len(added_videos)} new videos, {len(new_chunks)} new chunks.\n")


def plist_xml() -> str:
    python_path = sys.executable
    script_path = str(HERE / "watcher.py")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{LAUNCH_AGENT_ID}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_path}</string>
    <string>{script_path}</string>
    <string>run</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key><integer>8</integer>
    <key>Minute</key><integer>0</integer>
  </dict>
  <key>WorkingDirectory</key>
  <string>{ROOT}</string>
  <key>StandardOutPath</key>
  <string>{LOG_PATH}</string>
  <key>StandardErrorPath</key>
  <string>{LOG_PATH}</string>
  <key>RunAtLoad</key>
  <false/>
</dict>
</plist>
"""


def cmd_install(args) -> None:
    LAUNCH_AGENT_PLIST.parent.mkdir(parents=True, exist_ok=True)
    LAUNCH_AGENT_PLIST.write_text(plist_xml())
    uid = os.getuid()
    target = f"gui/{uid}"
    # Tear down any existing version, then bootstrap fresh.
    subprocess.run(["launchctl", "bootout", f"{target}/{LAUNCH_AGENT_ID}"],
                   capture_output=True, text=True)
    result = subprocess.run(
        ["launchctl", "bootstrap", target, str(LAUNCH_AGENT_PLIST)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print(f"Installed. Will run daily at 08:00.")
        print(f"Plist:   {LAUNCH_AGENT_PLIST}")
        print(f"Logs:    {LOG_PATH}")
        print(f"State:   {STATE_PATH}")
        print(f"To run now without waiting: python3 brain/watcher.py run")
    else:
        print(f"launchctl bootstrap failed: {result.stderr.strip()}")


def cmd_uninstall(args) -> None:
    uid = os.getuid()
    target = f"gui/{uid}"
    subprocess.run(["launchctl", "bootout", f"{target}/{LAUNCH_AGENT_ID}"],
                   capture_output=True, text=True)
    if LAUNCH_AGENT_PLIST.exists():
        LAUNCH_AGENT_PLIST.unlink()
    print(f"Uninstalled. {LAUNCH_AGENT_PLIST} removed and launchd job booted out.")


def cmd_status(args) -> None:
    state = load_state()
    print(f"Last check:    {state.get('last_check', 'never')}")
    print(f"Videos seen:   {len(state.get('seen_video_ids', []))}")
    last_added = state.get("last_added", [])
    if last_added:
        print(f"Last run added:")
        for v in last_added:
            print(f"  - {v['id']}  {v['title'][:70]}")
    else:
        print(f"Last run added: none")
    installed = LAUNCH_AGENT_PLIST.exists()
    print(f"launchd plist: {'INSTALLED' if installed else 'not installed'} ({LAUNCH_AGENT_PLIST})")
    if installed:
        uid = os.getuid()
        result = subprocess.run(
            ["launchctl", "print", f"gui/{uid}/{LAUNCH_AGENT_ID}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"launchd job:   LOADED")
        else:
            print(f"launchd job:   NOT LOADED (plist exists but launchctl does not see it)")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="check channel and ingest new videos")
    p_run.add_argument("--limit", type=int, default=30,
                       help="how many recent videos to scan (default 30)")
    p_run.set_defaults(func=cmd_run)

    p_install = sub.add_parser("install", help="install daily launchd job (macOS)")
    p_install.set_defaults(func=cmd_install)

    p_uninstall = sub.add_parser("uninstall", help="remove the launchd job")
    p_uninstall.set_defaults(func=cmd_uninstall)

    p_status = sub.add_parser("status", help="show watcher state and schedule")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
