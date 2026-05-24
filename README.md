# $100M Business OS — Lean

A strategic operating system for your business, grounded in the three core $100M books and the source YouTube corpus. Runs in Claude Code on your machine. Your business lives in files in this folder.

This is the **lean** edition: source corpus is just the three books plus the full video and shorts transcript archive. No supplementary playbooks. If you want the full library (22 books + playbooks + 2,275 videos), use the `hormozi-business-os` repo instead.

## What this is

A folder. Not an app. You open it in Claude Code and you have a business strategist trained on the $100M methodology and your specific business. After onboarding, you can run a full audit, get an action plan, and ask any business question.

Your data never leaves your machine.

## What you need

1. Claude Code installed: https://docs.claude.com/claude-code
2. Python 3.9 or higher
3. This folder
4. About 15 minutes for onboarding the first time

## Quick start (one command)

```bash
./setup.sh
```

That checks your Python version, installs the four dependencies (`fastembed`, `pymupdf`, `numpy`, `youtube-transcript-api`), verifies the brain index loads, and runs a smoke test.

Then:

```bash
claude
```

And type `/onboard` to start. If anything feels off later, `/check` runs a diagnostic.

## Optional dependency: the daily watcher

The watcher checks YouTube every morning and appends new videos to your index. Requires one extra package:

```bash
brew install yt-dlp
```

macOS only currently (uses `launchd`); Linux/Windows users can run `python3 brain/watcher.py run` manually or wire it into their own scheduler.

## One-time setup (build the brain)

The strategist queries a local vector index over the three books plus the video transcript archive. The index ships pre-built. To rebuild from source:

```bash
python3 brain/ingest.py \
  --source /path/to/books-markdown \
  --source /path/to/transcripts/videos \
  --source /path/to/transcripts/shorts
```

Books should be markdown files for the three source titles. Transcripts should be YouTube-format `.txt` files. Markdown is preferred because text extraction is cleaner. One-time, then forget about it.

## Optional: daily watcher for new videos

The folder includes `brain/watcher.py`. When enabled, it scans the source YouTube channel each morning, fetches transcripts for any new videos, and appends them to your local index. Pure client-side. No API keys.

To enable on macOS:

```bash
python3 brain/watcher.py install     # installs a launchd job that runs daily at 08:00
python3 brain/watcher.py run         # run it now without waiting
python3 brain/watcher.py status      # see last run, videos seen, schedule state
python3 brain/watcher.py uninstall   # remove the schedule
```

Opt-in. If you skip this, the index stays static.

## How to start

```bash
cd /path/to/hormozi-3-books-plus-transcripts
claude
```

Then in the Claude session:

```
/onboard
```

That kicks off the intake. Answer the questions. Claude writes your business profile to `profile.yaml` and `profile.md`.

When onboarding is done, you have six workflows:

- **`/onboard`** — intake (run this first). Also offers to install the daily watcher.
- **`/audit`** — full 15-dimension business diagnostic. Versioned (dated snapshot + latest pointer). Compares to prior audit.
- **`/plan`** — prioritized 30-day action plan from the latest audit. Versioned.
- **`/checkin`** — walk the current plan, mark actions done, dig into stuck items, decide on-pace vs re-plan.
- **`/advise`** — any business question, anytime. Auto-detects profile drift mid-answer.
- **`/update`** — patch the profile when something changes. Touches `profile.yaml` (canonical), re-renders `profile.md`.

You can also just talk. "Why isn't my landing page converting?" Claude reads your profile, pulls the relevant chunks from the corpus, and tells you the highest-leverage move.

## What is in the folder

```
hormozi-3-books-plus-transcripts/
├── CLAUDE.md                 the strategist personality (loaded every session)
├── README.md                 this file
├── LICENSE.md                personal use, no redistribution
├── profile.yaml              YOUR business, structured (canonical, written by /onboard)
├── profile.md                YOUR business, readable view (re-rendered from yaml)
├── audit/
│   ├── findings.md           latest 15-dimension diagnostic (pointer)
│   └── findings-YYYY-MM-DD.md  dated snapshots
├── plan/
│   ├── actions.md            latest action plan (pointer)
│   ├── actions-YYYY-MM-DD.md  dated snapshots
│   └── checkins/             checkin history
├── conversations/
│   └── YYYY-MM-DD.md         daily Q&A log
├── _qa/
│   ├── eval-queries.json     retrieval quality eval set
│   └── eval.py               run after every re-ingestion
├── brain/
│   ├── ingest.py             corpus indexer (md, pdf, transcript txt)
│   ├── query.py              runtime retrieval interface
│   ├── watcher.py            optional daily YouTube watcher
│   ├── index.npz             vector index (embeddings)
│   ├── chunks.jsonl          source text chunks
│   ├── _audit-dimensions.md  15-dimension rubric (used by /audit)
│   └── _plan-algorithm.md    prioritization algorithm (used by /plan)
└── .claude/skills/           the workflows
```

## What the brain contains

A local vector index over the **lean** corpus:

- **3 markdown books** ($100M Offers, $100M Leads, $100M Money Models)
- **173 long-form YouTube transcripts** (videos and streams over the last 2+ years)
- **2,102 YouTube Shorts transcripts**

If the daily watcher is enabled, the corpus grows automatically.

The strategist queries the index semantically every time it needs reasoning. No flat-file reading, no hardcoded categories. Synthesis crosses the three books and the video archive transparently. A pricing question can pull from $100M Offers AND a video where the same idea is stated differently AND a Short that ties it to retention, in one retrieval.

## Why the lean edition

The full edition ships 22 books and playbooks. This one ships only the three source books that the playbooks were distilled from, plus the full video corpus. Two reasons to prefer lean:

1. You want the source material in its original form, not condensed.
2. You want to integrate the corpus into another system (a different RAG pipeline, a knowledge graph, fine-tuning) and need a clean, well-bounded dataset.

If you want the full surface area (every playbook by topic, plus journals and supplementary material), use the full repo.

## Privacy

This is your folder on your machine. Nothing is sent anywhere except your normal Claude Code traffic to Anthropic. No backend, no analytics, no telemetry from this OS.

Your `profile.md`, audits, plans, and conversations stay local. If you want them shared (e.g., with a co-founder), share the folder yourself.

## Voice

The system speaks like a $100M-trained strategist. Direct. Blunt. Action-first. If your business model is broken, it will tell you on sentence one. If you are pricing for free that should cost R20,000, it will tell you. This is the point.

If you want softer feedback, you have ChatGPT. This is for operators who want the truth.

## A note on the source

The framework files are a strategist's distillation of publicly available source material. They are not verbatim copies. If you want the originals, the books are available wherever books are sold.

## Questions

Ask Claude. That's the system.
