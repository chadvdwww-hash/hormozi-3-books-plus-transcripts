#!/usr/bin/env bash
# $100M Business OS: one-command setup.
# Run this once after cloning. Re-run anytime to verify everything still works.
#
#   chmod +x setup.sh && ./setup.sh
#
# What this does:
#   1. Verifies Python 3.9+ is available
#   2. Detects pip3 (falls back to python3 -m pip)
#   3. Installs four Python packages
#   4. Confirms the brain index files are present and valid
#   5. Runs a real retrieval smoke test
#   6. Tells you the exact next command

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

step()    { printf "${DIM}[%s/6]${NC} %s\n" "$1" "$2"; }
ok()      { printf "      ${GREEN}OK${NC}    %s\n" "$1"; }
warn()    { printf "      ${YELLOW}WARN${NC}  %s\n" "$1"; }
fail()    { printf "      ${RED}FAIL${NC}  %s\n" "$1"; }
hint()    { printf "      ${DIM}fix:${NC}  %s\n" "$1"; }
bigfail() { printf "\n${RED}${BOLD}Setup did not complete.${NC} See the FAIL line above for the fix.\n\n"; exit 1; }

echo
printf "${BOLD}═══════════════════════════════════════════════${NC}\n"
printf "${BOLD}  \$100M Business OS - setup${NC}\n"
printf "${BOLD}═══════════════════════════════════════════════${NC}\n"
echo

# ────────────────────────────────────────────────
# 1. Operating system note
# ────────────────────────────────────────────────
step 1 "Detecting platform..."
OS_NAME="$(uname -s 2>/dev/null || echo unknown)"
case "$OS_NAME" in
  Darwin)  ok "macOS detected" ;;
  Linux)   ok "Linux detected (watcher install will be manual; see README)" ;;
  MINGW*|MSYS*|CYGWIN*)
           warn "Windows detected. Setup may not work directly: use WSL or Git Bash."
           hint "Ubuntu via WSL is the smoothest path on Windows." ;;
  *)       warn "Unknown OS ($OS_NAME). Continuing anyway." ;;
esac

# ────────────────────────────────────────────────
# 2. Python check
# ────────────────────────────────────────────────
step 2 "Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 not found"
  hint "Install Python 3.9+ from https://www.python.org/downloads/ (or 'brew install python3' on macOS)"
  bigfail
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
  fail "Python $PY_VER found; this system needs 3.9 or higher"
  hint "Install Python 3.9+ from https://www.python.org/downloads/"
  bigfail
fi
ok "Python $PY_VER"

# ────────────────────────────────────────────────
# 3. pip availability (with fallback)
# ────────────────────────────────────────────────
step 3 "Locating pip..."
PIP_CMD=""
if command -v pip3 >/dev/null 2>&1; then
  PIP_CMD="pip3"
  ok "pip3 found"
elif python3 -m pip --version >/dev/null 2>&1; then
  PIP_CMD="python3 -m pip"
  ok "using 'python3 -m pip' (pip3 binary not in PATH)"
else
  fail "pip not available"
  hint "Re-install Python from python.org (pip ships with the official installer)"
  bigfail
fi

# ────────────────────────────────────────────────
# 4. Install Python packages
# ────────────────────────────────────────────────
step 4 "Installing four Python packages (~100 MB; first run may take a minute)..."
if $PIP_CMD install --quiet --upgrade fastembed pymupdf numpy youtube-transcript-api 2>/dev/null; then
  ok "Packages installed"
else
  warn "System-wide install failed; retrying with --user scope"
  if $PIP_CMD install --quiet --upgrade --user fastembed pymupdf numpy youtube-transcript-api 2>/dev/null; then
    ok "Packages installed (user scope)"
  else
    fail "Package install failed"
    hint "Try: $PIP_CMD install fastembed pymupdf numpy youtube-transcript-api"
    bigfail
  fi
fi

# ────────────────────────────────────────────────
# 5. Brain index integrity
# ────────────────────────────────────────────────
step 5 "Verifying brain index..."
if [ ! -f "brain/index.npz" ] || [ ! -f "brain/chunks.jsonl" ]; then
  fail "brain/index.npz or brain/chunks.jsonl missing"
  hint "Re-clone the repo (the index ships pre-built)"
  bigfail
fi
INDEX_BYTES=$(wc -c < brain/index.npz | tr -d ' ')
if [ "$INDEX_BYTES" -lt 1000000 ]; then
  fail "brain/index.npz is suspiciously small ($INDEX_BYTES bytes); the clone is incomplete"
  hint "Delete the folder and re-clone"
  bigfail
fi
ok "Index files present (index: $((INDEX_BYTES / 1024 / 1024)) MB)"

# ────────────────────────────────────────────────
# 6. Smoke retrieval (real query against the brain)
# ────────────────────────────────────────────────
step 6 "Running a smoke retrieval (first run downloads the embedding model, ~80 MB)..."
if python3 - <<'PY' 2>&1
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "brain")
try:
    from query import load_index, search, EMBED_MODEL
    from fastembed import TextEmbedding
    import numpy as np
    embeddings, chunks = load_index()
    n, dim = embeddings.shape
    embedder = TextEmbedding(model_name=EMBED_MODEL)
    qvec = next(iter(embedder.embed(["should I raise prices"])))
    results = search(embeddings, chunks, qvec, top_k=1, mmr_lambda=1.0)
    if not results or results[0]["score"] < 0.3:
        print(f"Retrieval returned weak results (top score {results[0]['score'] if results else 'none'})")
        sys.exit(1)
    print(f"  brain: {n:,} chunks x {dim}-dim")
    print(f"  model: {EMBED_MODEL}")
    print(f"  test query: 'should I raise prices' -> top score {results[0]['score']:.2f}, source: {results[0]['source']}")
except Exception as e:
    print(f"Retrieval failed: {e}")
    sys.exit(1)
PY
then
  ok "Brain loaded and retrieval works"
else
  fail "Brain failed to load or retrieve cleanly"
  hint "Inside Claude Code, type /check to diagnose"
  bigfail
fi

# ────────────────────────────────────────────────
# Optional: Claude Code presence check
# ────────────────────────────────────────────────
echo
if ! command -v claude >/dev/null 2>&1; then
  warn "Claude Code CLI ('claude') not found in PATH"
  hint "Install from https://docs.claude.com/claude-code, then run 'claude' from this folder"
fi

# ────────────────────────────────────────────────
# Success message
# ────────────────────────────────────────────────
echo
printf "${BOLD}═══════════════════════════════════════════════${NC}\n"
printf "${GREEN}${BOLD}  Setup complete.${NC}\n"
printf "${BOLD}═══════════════════════════════════════════════${NC}\n"
echo
printf "  ${BOLD}Next:${NC}\n"
printf "    ${DIM}1.${NC} Open this folder in Claude Code:\n"
printf "         ${GREEN}claude${NC}\n"
printf "    ${DIM}2.${NC} In the Claude session, type:\n"
printf "         ${GREEN}/onboard${NC}\n"
printf "    ${DIM}3.${NC} Answer the 8-stage intake (~15 minutes).\n"
echo
printf "  ${DIM}If anything feels off later, type ${GREEN}/check${NC}${DIM} inside Claude Code.${NC}\n"
echo
