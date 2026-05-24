#!/usr/bin/env bash
# One-command launcher. Runs setup if needed, then opens Claude Code.
#
#   chmod +x start.sh && ./start.sh
#
# On first run: installs dependencies, builds the BM25 index, verifies the brain.
# On every run: opens Claude Code in this folder.

set -e

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Step 1: Check if setup looks complete. If not, run it.
need_setup=0

if ! python3 -c "import fastembed, fitz, numpy, rank_bm25" >/dev/null 2>&1; then
  need_setup=1
fi

if [ ! -f "brain/bm25.pkl" ]; then
  need_setup=1
fi

if [ "$need_setup" = "1" ]; then
  printf "${DIM}First-time setup required. Running setup.sh...${NC}\n\n"
  ./setup.sh
  echo
  printf "${DIM}─────────────────────────────────────────────${NC}\n"
fi

# Step 2: Check Claude Code is installed
if ! command -v claude >/dev/null 2>&1; then
  printf "\n${RED}Claude Code is not installed.${NC}\n"
  printf "  Install from: ${GREEN}https://docs.claude.com/claude-code${NC}\n"
  printf "  Then run ${GREEN}./start.sh${NC} again.\n\n"
  exit 1
fi

# Step 3: Open Claude Code with a friendly preview of what to type
echo
printf "${BOLD}═══════════════════════════════════════════════${NC}\n"
printf "${BOLD}  Opening Claude Code...${NC}\n"
printf "${BOLD}═══════════════════════════════════════════════${NC}\n"
echo
if [ ! -f "profile.yaml" ]; then
  printf "  ${BOLD}First time?${NC} Type ${GREEN}/onboard${NC} (~15 min intake)\n"
else
  printf "  ${BOLD}Welcome back.${NC} Try any of:\n"
  printf "    ${GREEN}/audit${NC}     score 15 dimensions\n"
  printf "    ${GREEN}/plan${NC}      30-day action plan from latest audit\n"
  printf "    ${GREEN}/checkin${NC}   walk this week's plan\n"
  printf "    ${GREEN}/advise${NC}    or just ask a question\n"
fi
printf "  ${DIM}Other commands:${NC} ${GREEN}/update${NC}, ${GREEN}/check${NC}\n"
echo

exec claude
