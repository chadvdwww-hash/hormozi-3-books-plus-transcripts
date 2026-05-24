---
name: update
description: Use when the operator types /update, or when /advise detects that something they said contradicts or extends profile.yaml. Captures a change to the business (new price, new hire, new offer, new numbers, new channel) and patches profile.yaml accordingly, then re-renders profile.md. Closes the staleness loop.
---

# Update

You are patching `profile.yaml` (the canonical store) to reflect a change in the operator's business. Confirm before writing. Append a Changelog entry. Re-render `profile.md` from the updated yaml.

## Preconditions

1. `profile.yaml` must exist. If only `profile.md` exists from a pre-v1 onboard, fall back to parsing it, then write the corresponding `profile.yaml` before patching. If neither exists, tell the operator, verbatim: "Nothing to update yet. Run /onboard first."

## When this skill fires

Two paths in:

**Direct.** Operator types `/update` or says "my numbers changed," "we just hired," "I dropped that offer," "new website is live," etc.

**Detected during /advise.** The operator stated something that contradicts `profile.yaml`. The /advise skill offered "Want me to update?" and they said yes.

## The update flow

### Step 1. Identify what changed

If the operator already told you, restate it for confirmation.

If they just typed `/update` without specifying, ask: "What changed?"

Listen for which yaml path(s) this touches. Common updates:

| Operator says | YAML path(s) affected |
|---|---|
| "We raised to $20k" | `money.current_price_range` |
| "I hired two people" | `operations.team_size`, `operations.team_roles`, `operations.hours_in_vs_on_business` |
| "We dropped X offer" | `offer.core_offer_description`, `money.pricing_model` |
| "We're at $200k/mo now" | `money.revenue_stage` |
| "New website launched" | `reach.website_url`, `reach.website_purpose`, `reach.funnel_description` |
| "Added a continuity tier" | `money.pricing_model` |
| "Switched to monthly retainer" | `money.pricing_model`, `money.payment_terms` |

If the change does not map to any yaml field, ask one clarifying question.

### Step 2. Confirm before writing

State the change as a diff, verbatim:

> Updating profile.yaml:
> - `{yaml.path}`: `{old value}` → `{new value}`
> {repeat for each field if multiple}
>
> Right?

Wait for explicit confirmation. Hard cap: 2 confirmation rounds, then abort and ask them to re-state.

### Step 3. Patch profile.yaml

1. Read the current `profile.yaml`.
2. Update the targeted leaf field(s) only. Do not touch other keys.
3. Update `last_updated: {YYYY-MM-DD}` to today.
4. Append a new entry to `changelog:`:
   ```yaml
   - date: {YYYY-MM-DD}
     path: {yaml.path}
     from: {old value}
     to: {new value}
     note: {optional one-line context if the operator gave any}
   ```
5. Write the yaml back, preserving the schema order from `/onboard`.

### Step 4. Re-render profile.md from the updated yaml

Use the same markdown template that `/onboard` uses. Replace each section's content with the new yaml values. Re-write the entire `profile.md` file from the yaml. Do not try to surgically edit the markdown; render it fresh.

If the change is material, add a flag near the top of `profile.md` under the date:

`> Material change since last audit. Re-run /audit before next /plan.`

What counts as material: price change over 20%, new revenue stage, team size doubled, primary channel changed, offer rewritten or dropped, money model archetype added or removed, runway_pressure changed.

### Step 5. Append to conversations log

Append one line to `conversations/{YYYY-MM-DD}.md`:

`- Profile updated. {yaml.path}: {old} → {new}.`

### Step 6. Confirm to operator

Tell them, verbatim or close to it:

> Updated. {yaml.path} is now {new value}.
>
> {If you flagged material change:} Your last audit is now partly stale on this dimension. Re-run /audit before the next /plan.
>
> Anything else?

## Voice rules

- Terse. The operator is mid-thought. Get out of their way.
- No em-dashes.
- State the diff clearly. Numbers should be numbers, not paraphrased.
- Currency from `profile.yaml` (`identity.currency`).

## Common mistakes

- Editing profile.md directly. The markdown is derived. Always patch the yaml first and re-render md from it.
- Writing the change without confirming. Always confirm the diff before patching.
- Overwriting fields the operator did not actually change.
- Skipping the Changelog. The Changelog is the audit trail.
- Forgetting `last_updated`. Every patch updates the date.
- Inventing a value the operator did not give. If unclear, ask.

## Red flags

- Operator asks to update profile.yaml with something contradicted by recent /advise answers. Surface it: "You told me on {date} that {X}. Now you are saying {Y}. Which is current?"
- Operator wants to wipe a field. Confirm: "Setting {path} to null. You are sure?" Then do it.
- Operator wants to rewrite the entire profile. Decline: "That is /onboard, not /update. Run /onboard again. I can back up the current profile.yaml to profile-{YYYY-MM-DD}.yaml.bak first if you want."

## Edge: yaml path does not exist yet

If the operator updates something the original /onboard did not capture (a new field like `affiliate_program`, `partnership_status`), add it under the most fitting section in `profile.yaml`. Use the same key conventions (snake_case, lowercase). Log the addition in the changelog with `note: + added field`.
