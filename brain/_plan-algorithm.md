# Plan Algorithm

The `/plan` skill reads `audit/findings.md` and produces a 30-day action plan in `plan/actions.md`. This doc defines the prioritization algorithm so plans are consistent across operators and re-runs.

## Inputs

- `audit/findings.md`: 15 dimension scores (0 to 4) with evidence and proposed next moves.
- `profile.md`: business context, especially `revenue_stage` and `runway_pressure`.

## Step 1. Filter

Take every dimension scored 0 (broken) or 1 (weak). These are the candidates.
Ignore dimensions scored 2+. They are not where the leverage is right now.

## Step 2. Score each candidate on three axes

For each candidate dimension, score 1 to 3 on each axis:

**Impact.** If fixed, how much does this move revenue, margin, or close rate within 90 days?
- 1 = small lift (5 to 15%)
- 2 = meaningful lift (15 to 40%)
- 3 = step change (40%+ or unlocks a new revenue mode)

**Cheapness.** What does it cost to ship the fix in time, money, complexity?
- 1 = needs a process change, hire, or new build (weeks)
- 2 = needs an offer, copy, or systems change (days)
- 3 = pure copy fix, surface a proof element, raise a price (hours)

**Urgency.** Is this bleeding cash or compounding pain right now?
- 1 = nice to fix this quarter
- 2 = costing money every week
- 3 = existential or runway pressure

Total = Impact × Cheapness × Urgency. Range 1 to 27.

## Step 3. Rank and select

Sort candidates by total, descending. Pick the top 5.

**Runway override:** if `profile.md` says `runway_pressure` is `tight` or `urgent`, at least three of the top five must have Cheapness = 3. Operators in cash crunch need fast wins, not 90-day projects. If fewer than three score Cheapness = 3, swap lower-total candidates that do score Cheapness = 3 into the top five until the constraint is satisfied.

## Step 4. Sequence over 30 days

Distribute the five fixes across four weeks:

- **Week 1 (days 1-7):** the two cheapest plus most urgent. The operator needs a win in the first seven days or trust in the plan collapses.
- **Week 2 (days 8-14):** one medium-effort fix.
- **Week 3 (days 15-21):** the remaining medium fix.
- **Week 4 (days 22-30):** the highest-impact fix, even if harder. By now the operator has momentum and three wins on the board.

## Step 5. Write plan/actions.md

Use this template:

````markdown
# 30-Day Action Plan
Generated: {YYYY-MM-DD}
Source: audit/findings.md ({audit date})

## The 5 fixes, ranked

For each fix:
- **Dimension:** {name}
- **Current score:** {0 or 1}
- **Target score by day 30:** {2 or 3}
- **Why this one:** {one sentence on impact × cheapness × urgency}
- **Brain reference:** {file name}
- **Concrete action:** {imperative sentence}

## Week-by-week

### Week 1 (days 1-7)
- [ ] {action 1}
- [ ] {action 2}

### Week 2 (days 8-14)
- [ ] {action 3}

### Week 3 (days 15-21)
- [ ] {action 4}

### Week 4 (days 22-30)
- [ ] {action 5}

## Re-audit trigger

Run `/audit` again on day 31. Score the same 15 dimensions and measure movement. If three or more targeted dimensions moved up, repeat the plan loop. If fewer than three moved, run `/advise` before re-planning to diagnose what blocked execution. Plans without re-audits are theatre.
````

After writing, append one line to `conversations/{today}.md`: "Plan written. Top 5: {list of dimensions}."
