# Welcome to $100M Business OS

You opened a folder that becomes a senior business strategist when you talk to it in Claude Code. The strategist knows your business (once you tell it) and knows the $100M methodology cold (already indexed).

This 3-minute read gets you to your first conversation with the strategist.

## If you have not run setup yet

From your terminal, in this folder:

```bash
./setup.sh
```

`setup.sh` checks your Python version, installs three Python packages (~100 MB total), verifies the brain index loads, and runs a real retrieval. If anything is missing, it tells you the exact fix. Takes about 90 seconds.

If `./setup.sh` says "Permission denied," run `chmod +x setup.sh` first.

When setup finishes, open Claude Code:

```bash
claude
```

The strategist greets you. Type `/onboard` to start the 8-stage intake.

## The seven workflows

After onboarding, you can type a slash command or describe what you want in plain English:

| Command | When | What it does |
|---|---|---|
| `/onboard` | First time only | Captures your business in `profile.yaml` (~15 min) |
| `/audit` | Quarterly | Scores 15 dimensions, writes `audit/findings.md` |
| `/plan` | After every audit | Picks 5 fixes, sequences over 30 days, writes `plan/actions.md` |
| `/checkin` | Weekly | Walks the plan, marks done, surfaces stuck items |
| `/advise` | Anytime | Default for any business question |
| `/update` | When something changes | Patches `profile.yaml` (with a diff confirmation) |
| `/check` | If something feels off | Runs a system diagnostic |

"Should I raise my prices?" routes to `/advise`. "I just raised prices to $20k" routes to `/update`. You do not need to memorize the commands.

## What is in this folder

```
.
├── README.md                 longer setup + reference
├── WELCOME.md                this file
├── CLAUDE.md                 strategist personality (loaded every session)
├── LICENSE.md                personal use only
├── setup.sh                  one-command install
├── profile.yaml              YOUR business (created by /onboard)
├── audit/                    your dated 15-dimension diagnostics
├── plan/                     your dated 30-day action plans
├── conversations/            daily Q&A log
├── brain/
│   ├── index.npz             pre-built vector index (the corpus)
│   ├── chunks.jsonl          source text for each indexed chunk
│   ├── ingest.py             rebuild the index from source files
│   └── query.py              semantic retrieval (cosine + MMR)
└── .claude/skills/           the seven workflows
```

## Privacy

Your `profile.yaml`, audits, plans, and conversations stay on your machine. The vector index is local. The embedding model runs on your CPU.

The only network traffic this system generates is your normal Claude Code conversation with Anthropic, which you already use.

## Voice you can expect

Direct. Blunt. Action-first. If your business model is broken, the strategist says so on sentence one. If you are pricing for free what should cost $20,000, it says so. This is the point.

If you want softer feedback, use ChatGPT. This is for operators who want the truth.

## If something does not work

- `./setup.sh` failed at step X? Open `README.md` for the troubleshooting section.
- Brain not loading? Type `/check` inside Claude Code, it diagnoses in 6 steps.
- Anything else? Type `/check` first, then ask Claude.
