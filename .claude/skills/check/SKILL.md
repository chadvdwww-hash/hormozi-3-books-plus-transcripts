---
name: check
description: Use when the operator types /check, asks "is everything working", reports something broken, or when /audit or /advise fails unexpectedly. Runs a system diagnostic verifying Python dependencies, the brain index, the profile, the skills, and the corpus health. Reports pass/fail per check and the one fix for the first failure.
---

# Check

You are running a system diagnostic. Verify every load-bearing piece of the OS. Report each check as pass / fail / warn. For the first failure, tell the operator the one command that fixes it.

## When this fires

- Operator types `/check`.
- Operator says "is everything working", "something feels off", "did it break", "is the brain ok", or similar.
- Another workflow has failed unexpectedly and you want to diagnose before retrying.

## The diagnostic checklist

Run these in order, via Bash where appropriate. Print each result as you go (real-time feedback matters).

### 1. Python and packages

```bash
python3 --version
python3 -c "import fastembed, fitz, numpy; print('packages ok')" 2>&1
```

Expected: Python 3.9 or higher; `packages ok` printed.
On failure: `./setup.sh` (or `pip3 install fastembed pymupdf numpy` if no setup.sh).

### 2. Brain index integrity

```bash
ls -lh brain/index.npz brain/chunks.jsonl
```

Expected: both files present. `index.npz` >= 1 MB. `chunks.jsonl` >= 1 MB.
On failure: the clone is incomplete OR they need to ingest. Tell them to re-clone or run `python3 brain/ingest.py --source <path>`.

### 3. Brain loads cleanly

```bash
python3 -c "
import sys; sys.path.insert(0, 'brain')
from query import load_index
e, c = load_index()
print(f'loaded: {e.shape[0]} chunks, {e.shape[1]}-dim')
"
```

Expected: prints a chunk count and 384-dim. Failure means the index file is corrupted.
On failure: `python3 brain/ingest.py --source <path>` to rebuild.

### 4. Profile present

Check whether `profile.yaml` exists.

- If present and non-empty: pass.
- If missing: the operator has not onboarded yet. Not an error, just a state. Tell them `/onboard` is the next step.

### 5. Workflows registered

Check that the six skill folders exist:

```bash
ls .claude/skills/ | sort
```

Expected: `advise`, `audit`, `check`, `checkin`, `onboard`, `plan`, `update` (7 entries with /check).
On failure: the install is broken. Re-clone.

### 6. Quick retrieval smoke test

Run a sample query to verify retrieval works end-to-end:

```bash
python3 brain/query.py "should I raise prices" --top-k 2 --format text 2>&1 | head -20
```

Expected: 2 chunks returned with score and source name.
On failure: same as check 3.

## Output shape

After every check, print a one-line status. At the end, summarize:

```
═══════════════════════════════════════
  System check
═══════════════════════════════════════
  [✓] Python 3.11.4
  [✓] Packages: fastembed, pymupdf, numpy
  [✓] Brain: 9,558 chunks × 384-dim
  [✗] profile.yaml missing: run /onboard
  [✓] Skills: 7 workflows registered
  [✓] Retrieval test: top score 0.81 (Pricing Playbook)

  Status: 1 issue: run /onboard to fix.
```

## Output rules

- Use the box-drawing characters above for the summary.
- One line per check.
- For failures, the line below the summary names the single command to run.
- Do not lecture. If they need to run a command, give the command and stop.

## Voice rules

- No em-dashes.
- No preambles. Skip "Let me check everything for you": just start running checks.
- Skip cheerleading. "All checks passed" is enough.

## Common mistakes

- Running all checks silently then dumping a wall of text. Print each as you go.
- Recommending generic "try reinstalling" without identifying which dep is missing. Be specific.
- Failing the diagnostic because `profile.yaml` is missing. Not having a profile is a state, not an error. Just flag it.

## Red flags

- All 6 checks fail. The clone is broken or the operator is in the wrong directory. Tell them: "Verify you are in the project folder, then re-clone if needed."
- Python is missing entirely. Tell them: "Install Python 3.9+ from python.org, then run ./setup.sh."
- The brain loads but retrieval returns empty results. The chunks.jsonl is desynced from index.npz: rebuild via ingest.py.
