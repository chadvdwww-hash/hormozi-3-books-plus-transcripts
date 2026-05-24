# $100M Business OS

A strategic operating system for your business, grounded in the three core $100M books and the source YouTube corpus. Runs in Claude Code on your machine. Your business lives in files in this folder.

## What this is

A folder. Not an app. You open it in Claude Code and you have a senior business strategist on your screen. The strategist knows your business (once you tell it) and knows the $100M methodology cold (already indexed locally). You can:

- Get audited across 15 dimensions and scored 0 to 4 on each.
- Get a prioritized 30-day action plan from the audit.
- Walk that plan week by week with structured check-ins.
- Ask any business question, anytime, and get a grounded answer with a real source citation.

Your data never leaves your machine.

## How it actually works (in depth)

The system is two things bolted together: a **structured operating framework** (workflows that capture your business and turn diagnostics into actions) and a **local retrieval-augmented strategist** (a small vector database over $100M material that the strategist consults at the moment you ask).

**1. Ingestion (already done; ships pre-built).**
Source documents (3 books in markdown plus 2,275 video and shorts transcripts) are split into ~400-word overlapping chunks. Each chunk is converted into a 384-dimensional numerical fingerprint by a small open-source embedding model (`BAAI/bge-small-en-v1.5`, runs locally on CPU). All fingerprints are stacked into `brain/index.npz`. The matching source text plus metadata is saved to `brain/chunks.jsonl`. The full index is about 13 MB on disk. This step happens once. The repo ships the pre-built index so you do not need source PDFs.

**2. Onboarding (you do this once).**
`/onboard` walks you through eight stages of intake (about 15 minutes): identity, offer, customer, pricing and money, reach and marketing, sales, operations, goals. The strategist writes your structured profile to `profile.yaml` (canonical) and a readable view to `profile.md`. Mid-stage micro-observations call out patterns as they show up so it does not feel like a form.

**3. Retrieval-augmented advice (every session).**
When you ask the strategist anything, it converts your question into a 384-dim fingerprint using the same model. It computes cosine similarity against all chunk fingerprints in `brain/index.npz` (one numpy matrix multiplication, ~200 ms on CPU). It pulls the top 5 most relevant chunks, re-ranks them for diversity (MMR), and synthesizes an answer grounded in those chunks plus your `profile.yaml`. Every answer cites the source by name. Nothing leaves your machine; the strategist's responses route through your normal Claude Code session.

**4. The diagnostic loop.**
`/audit` scores 15 dimensions of your business (4 Offer, 3 Leads, 3 Sales, 2 Money Model, 3 Retention and Growth). Each score cites a profile field and a source chunk. `/plan` filters dimensions scored 0 or 1, ranks them by Impact times Cheapness times Urgency, picks the top 5, and sequences them across four weeks. `/checkin` walks that plan, marks what is done, surfaces what is stuck, and decides whether you are on pace, have an execution problem, or need to re-plan. `/update` patches your profile when something changes. `/check` runs a system diagnostic.

**5. Optional daily watcher.**
The folder includes `brain/watcher.py`. When enabled, it scans the source YouTube channel every morning, fetches transcripts for any new videos, embeds them, and appends to your local index. Pure client-side. No API keys. macOS only currently (uses `launchd`).

## What you need

1. Claude Code installed: https://docs.claude.com/claude-code
2. Python 3.9 or higher
3. This folder
4. About 15 minutes for onboarding the first time

## Quick start (one command)

```bash
./setup.sh
```

That checks your Python version, installs the four dependencies (`fastembed`, `pymupdf`, `numpy`, `youtube-transcript-api`), verifies the brain index loads, and runs a smoke test. If anything is wrong, it tells you the fix.

Then open the folder in Claude Code:

```bash
claude
```

And type `/onboard` to start. The strategist greets you and walks you through. If anything feels off later, type `/check` inside Claude Code for a diagnostic.

## The seven workflows

| Command | When | What it does |
|---|---|---|
| `/onboard` | First-time only | Captures your business in `profile.yaml`. |
| `/audit` | Quarterly | Scores 15 dimensions, writes `audit/findings.md`. |
| `/plan` | After every audit | Picks 5 fixes, sequences over 30 days, writes `plan/actions.md`. |
| `/checkin` | Weekly | Walks the plan, marks done, surfaces stuck. |
| `/advise` | Anytime | Default for any business question. |
| `/update` | When something changes | Patches `profile.yaml`. |
| `/check` | If something feels off | Runs a diagnostic. |

You can also just talk in plain English. "Should I raise my prices?" routes to `/advise`. "I just raised prices to $20k" routes to `/update`.

## What is in the folder

```
.
├── CLAUDE.md                 strategist personality (loaded every session)
├── README.md                 this file
├── LICENSE.md                personal use, no redistribution
├── WELCOME.md                first-read intro
├── setup.sh                  one-command install
├── profile.yaml              YOUR business (created by /onboard)
├── profile.md                readable view of the same
├── audit/                    dated 15-dimension diagnostics
├── plan/                     dated 30-day action plans + checkins
├── conversations/            daily Q&A log
├── _qa/                      retrieval quality eval set
├── brain/
│   ├── index.npz             pre-built vector index (the corpus)
│   ├── chunks.jsonl          source text per chunk
│   ├── ingest.py             rebuild index from source
│   ├── query.py              semantic retrieval (cosine + MMR)
│   ├── watcher.py            optional daily YouTube watcher
│   ├── _audit-dimensions.md  15-dimension rubric
│   └── _plan-algorithm.md    prioritization spec
└── .claude/skills/           the workflows
```

## What the brain contains

A local vector index over:

- **3 markdown books** ($100M Offers, $100M Leads, $100M Money Models)
- **173 long-form YouTube transcripts** (videos and streams over the last 2+ years)
- **2,102 YouTube Shorts transcripts**

If the daily watcher is enabled, the corpus grows automatically as new videos appear.

## Privacy

This is your folder on your machine. Nothing is sent anywhere except your normal Claude Code traffic to Anthropic. No backend, no analytics, no telemetry from this OS.

Your `profile.yaml`, audits, plans, and conversations stay local. If you want them shared (for example, with a co-founder), share the folder yourself.

## Voice

The strategist speaks like a $100M-trained operator. Direct. Blunt. Action-first. If your business model is broken, it says so on sentence one. If you are pricing for free what should cost $20,000, it says so. This is the point.

If you want softer feedback, use ChatGPT. This is for operators who want the truth.

## License

Personal use only. See `LICENSE.md`.

## Questions

Ask Claude. That's the system.
