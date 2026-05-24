# $100M Business OS

A folder that becomes a senior business strategist on your machine. Grounded in the $100M methodology. Your business profile lives in this folder. The strategist's knowledge of the methodology lives in a local vector index. Nothing leaves your machine.

> **Live site:** https://hormozi-3-books-guide.vercel.app

---

## 60-second install

You need three things on your machine first:

1. **Claude Code** — install from https://docs.claude.com/claude-code
2. **Python 3.9 or higher** — most Macs and Linux already have it. Test: `python3 --version`
3. **Git** — most machines already have it. Test: `git --version`

Then, from a terminal:

```bash
git clone https://github.com/chadvdwww-hash/hormozi-3-books-plus-transcripts.git
cd hormozi-3-books-plus-transcripts
./setup.sh
```

`setup.sh` checks your Python version, installs three Python packages (~100 MB total), verifies the brain index loads, and runs a smoke test. It tells you the exact fix if anything trips. Takes about 90 seconds.

When `setup.sh` finishes, open the folder in Claude Code:

```bash
claude
```

Then type:

```
/onboard
```

The strategist walks you through an 8-stage intake (~15 minutes), writes your business profile, and tells you the next move.

---

## What you get

A strategist with seven workflows. Type the slash command or describe what you want in plain English:

| Command | When to use | What it does |
|---|---|---|
| `/onboard` | First time | Captures your business in `profile.yaml` (~15 min) |
| `/audit` | Quarterly | Scores your business across 15 dimensions, writes `audit/findings.md` |
| `/plan` | After every audit | Picks your 5 highest-leverage fixes, sequences them across 30 days |
| `/checkin` | Weekly | Walks the plan, marks what is done, surfaces what is stuck |
| `/advise` | Anytime | Default for any business question. Auto-detects profile drift |
| `/update` | When something changes | Patches `profile.yaml`. Confirms the diff before writing |
| `/check` | If something feels off | Runs a system diagnostic |

You can also just talk in plain English. "Should I raise my prices?" routes to `/advise`. "I just raised prices to $20k" routes to `/update`.

---

## What the brain contains

A local vector index over:

- **3 markdown books** — $100M Offers, $100M Leads, $100M Money Models
- **173 long-form YouTube transcripts** (videos and streams, last 2+ years)
- **2,102 YouTube Shorts transcripts**

Total: 8,923 chunks, 13 MB on disk. The strategist queries this index semantically every time it needs reasoning. Every answer cites the source by name.

---

## How it actually works

The system has two parts: a **structured operating framework** (the seven workflows that capture your business and turn diagnostics into action) and a **local retrieval-augmented strategist** (a small vector database the strategist consults at the moment you ask).

**Ingestion** (already done; the index ships pre-built).
The 3 books and 2,275 transcripts were split into ~400-word overlapping chunks. Each chunk was converted to a 384-dimensional numerical fingerprint by a small open-source embedding model (`BAAI/bge-small-en-v1.5`). All fingerprints stack into `brain/index.npz`. Source text plus metadata lives in `brain/chunks.jsonl`. You never need to do this yourself; the repo includes the pre-built index.

**Onboarding** (you do this once).
`/onboard` walks you through eight stages of intake: identity, offer, customer, pricing, reach, sales, operations, goals. The strategist writes your structured profile to `profile.yaml` plus a readable view to `profile.md`. Mid-stage micro-observations call out patterns as they show up.

**Retrieval-augmented advice** (every session).
When you ask anything, the strategist turns your question into the same kind of fingerprint, computes cosine similarity against all chunk fingerprints (one numpy matrix multiplication, ~200 ms on CPU), pulls the top 5, re-ranks for diversity (Maximal Marginal Relevance), and synthesizes an answer grounded in those chunks plus your profile. Every answer cites the source by name.

**The diagnostic loop.**
`/audit` scores 15 dimensions. `/plan` picks the top 5 fixes by Impact × Cheapness × Urgency and sequences them across 4 weeks. `/checkin` walks the plan and decides whether you are on pace, have an execution problem, or need to re-plan. `/update` patches your profile when something changes.

---

## Troubleshooting

**`./setup.sh: Permission denied`**
Run `chmod +x setup.sh` then try again.

**`command not found: python3`**
Install Python 3.9+ from https://www.python.org/downloads/. On macOS you can also run `brew install python3`.

**`command not found: pip3`**
Use `python3 -m pip install fastembed pymupdf numpy` instead, then re-run `./setup.sh`.

**`command not found: claude`**
Install Claude Code from https://docs.claude.com/claude-code. Once installed, run `claude` from inside this folder.

**The strategist does not respond, or seems lost**
Inside Claude Code, type `/check`. It runs a 6-step diagnostic and tells you the one command that fixes the first failure.

**Anything else**
Open an issue on the repo or type `/check` inside Claude Code.

---

## What is in the folder

```
.
├── README.md                 this file
├── WELCOME.md                first-read overview (~3 min read)
├── CLAUDE.md                 strategist personality (loaded every session)
├── LICENSE.md                personal use, no redistribution
├── setup.sh                  one-command install + verification
├── profile.yaml              YOUR business (created by /onboard)
├── profile.md                readable view of the same
├── audit/                    dated 15-dimension diagnostics
├── plan/                     dated 30-day action plans + checkins
├── conversations/            daily Q&A log
├── _qa/                      retrieval quality eval set
├── brain/
│   ├── index.npz             pre-built vector index
│   ├── chunks.jsonl          source text per chunk
│   ├── ingest.py             rebuild the index from source
│   ├── query.py              semantic retrieval (cosine + MMR)
│   ├── _audit-dimensions.md  15-dimension rubric
│   └── _plan-algorithm.md    prioritization spec
└── .claude/skills/           the seven workflows
```

---

## Privacy

This is your folder on your machine. Nothing is sent anywhere except your normal Claude Code traffic to Anthropic. No backend, no analytics, no telemetry from this OS.

Your `profile.yaml`, audits, plans, and conversations stay local. If you want them shared (for example, with a co-founder), share the folder yourself.

The embedding model runs on your CPU. The vector index is a local file.

---

## Voice

The strategist speaks like a $100M-trained operator. Direct. Blunt. Action-first. If your business model is broken, it says so on sentence one. If you are pricing for free what should cost $20,000, it says so. This is the point.

If you want softer feedback, use ChatGPT. This is for operators who want the truth.

---

## License

Personal use only. See `LICENSE.md`.

---

## Questions

Ask Claude. That's the system.
