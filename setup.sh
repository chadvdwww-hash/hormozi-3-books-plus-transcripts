#!/usr/bin/env bash
# $100M Business OS — one-command setup
# Run this once after cloning. Verifies Python, installs dependencies, tests the brain.
# Re-run anytime you suspect something is off.
#
#   chmod +x setup.sh && ./setup.sh

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
DIM='\033[2m'
NC='\033[0m'

step() { printf "${DIM}[%s]${NC} %s\n" "$1" "$2"; }
ok()   { printf "${GREEN}✓${NC} %s\n" "$1"; }
err()  { printf "${RED}✗${NC} %s\n" "$1"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$1"; }

echo
echo "════════════════════════════════════════════"
echo "  \$100M Business OS — setup"
echo "════════════════════════════════════════════"
echo

# ────────────────────────────────────────────────
# 1. Python check
# ────────────────────────────────────────────────
step "1/4" "Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
  err "python3 not found."
  echo "    Install Python 3.9+ from https://www.python.org/downloads/"
  exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
  err "Python $PY_VER found, need 3.9 or higher."
  exit 1
fi
ok "Python $PY_VER"

# ────────────────────────────────────────────────
# 2. Install Python packages
# ────────────────────────────────────────────────
step "2/4" "Installing dependencies (fastembed, pymupdf, numpy, youtube-transcript-api)..."
if pip3 install --quiet --upgrade fastembed pymupdf numpy youtube-transcript-api 2>/dev/null; then
  ok "Dependencies installed"
else
  warn "pip install failed at system scope. Retrying with --user..."
  pip3 install --quiet --user --upgrade fastembed pymupdf numpy youtube-transcript-api
  ok "Dependencies installed (--user)"
fi

# ────────────────────────────────────────────────
# 3. Verify brain index exists
# ────────────────────────────────────────────────
step "3/4" "Verifying brain index..."
if [ ! -f "brain/index.npz" ] || [ ! -f "brain/chunks.jsonl" ]; then
  err "brain/index.npz or brain/chunks.jsonl missing."
  echo "    Either the clone is incomplete (re-clone), or you need to ingest from source."
  exit 1
fi

# Size sanity check
INDEX_BYTES=$(wc -c < brain/index.npz | tr -d ' ')
if [ "$INDEX_BYTES" -lt 100000 ]; then
  err "brain/index.npz is suspiciously small ($INDEX_BYTES bytes)."
  exit 1
fi
ok "Index file present"

# ────────────────────────────────────────────────
# 4. Load test — actually query the brain once
# ────────────────────────────────────────────────
step "4/4" "Loading and querying the brain..."
python3 - <<'PY'
import sys, os
sys.path.insert(0, "brain")
try:
    from query import load_index, EMBED_MODEL
    embeddings, chunks = load_index()
    n, dim = embeddings.shape
    if n != len(chunks):
        print(f"✗ Mismatch: {n} vectors vs {len(chunks)} chunks")
        sys.exit(1)
    print(f"  Index: {n:,} chunks × {dim}-dim embeddings")
    print(f"  Model: {EMBED_MODEL}")
except Exception as e:
    print(f"✗ Brain failed to load: {e}")
    sys.exit(1)
PY
ok "Brain loaded successfully"

# ────────────────────────────────────────────────
# Next steps
# ────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════"
echo "  Setup complete."
echo "════════════════════════════════════════════"
echo
echo "  Next:"
echo "    1. Make sure Claude Code is installed:"
echo "       https://docs.claude.com/claude-code"
echo "    2. Open this folder in Claude Code:"
echo "       claude"
echo "    3. In the Claude session, type:"
echo "       /onboard"
echo
echo "  Need help? Type /check inside Claude Code to diagnose."
echo
