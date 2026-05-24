# Welcome to $100M Business OS

You just opened a folder that becomes a senior business strategist when you talk to it in Claude Code. The strategist knows your business (once you tell it) and knows the $100M methodology cold (already indexed).

## If this is your first time

Run setup once from your terminal:

```bash
./setup.sh
```

Then start a Claude Code session in this folder and type:

```
/onboard
```

That kicks off an 8-stage intake (~15 minutes). Answer the questions. The strategist writes your business profile to `profile.yaml`, and you are ready to use everything else.

## The six workflows

After onboarding, you have:

| Command | When | What it does |
|---|---|---|
| `/onboard` | First time only | Captures your business in `profile.yaml`. |
| `/audit` | Quarterly | Scores 15 dimensions, writes `audit/findings.md`. |
| `/plan` | After audit | Picks 5 fixes, sequences over 30 days, writes `plan/actions.md`. |
| `/checkin` | Weekly | Walks the plan, marks done, surfaces stuck items. |
| `/advise` | Anytime | Default for any business question. |
| `/update` | When something changes | Patches `profile.yaml`. |
| `/check` | If something feels off | Runs a diagnostic to verify the system is healthy. |

You can also just talk in plain English. "Should I raise my prices?" routes to `/advise`. "I just raised prices to R20k" routes to `/update`.

## What is in this folder

```
.
├── CLAUDE.md                 strategist personality (loaded every session)
├── README.md                 longer setup + reference
├── LICENSE.md                personal use only
├── setup.sh                  one-command install
├── profile.yaml              YOUR business (created by /onboard)
├── audit/                    your dated 15-dimension diagnostics
├── plan/                     your dated 30-day action plans
├── conversations/            daily Q&A log
├── brain/
│   ├── index.npz             pre-built vector index (the corpus)
│   ├── chunks.jsonl          the source text for each indexed chunk
│   ├── ingest.py             rebuild the index from source files
│   ├── query.py              semantic retrieval
│   └── watcher.py            optional daily YouTube watcher
└── .claude/skills/           the workflows
```

## Privacy

Your `profile.yaml`, audits, plans, and conversations stay on your machine. The vector index is local. The embedding model runs on your CPU.

The only network traffic this system generates is your normal Claude Code conversation with Anthropic, which you already use.

## Voice you can expect

Direct. Blunt. Action-first. If your business model is broken, the strategist says so on sentence one. If you are pricing for free what should cost R20,000, it says so. This is the point.

If you want softer feedback, you have ChatGPT. This is for operators who want the truth.

## Stuck

- `setup.sh` failed? Open `README.md` for manual install instructions.
- Brain not loading? Run `/check` inside Claude Code.
- Anything else? Ask Claude. That's the system.
