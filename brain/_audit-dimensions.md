# Audit Dimensions

The 15-dimension business diagnostic. Read at the start of `/audit`. Each dimension has: what it measures, the retrieval focus the strategist should query, the 5-point rubric, and the profile fields it pulls.

The 15 dimensions are organized into the five Hormozi pillars: Offer, Leads, Sales, Money Model, Retention & Growth. These mirror the structure of the $100M playbook series (Offers, Leads, Money Models, plus retention and scaling).

Hormozi knowledge is retrieved from `brain/query.py` (vector index over the $100M playbooks). For each dimension below, the `Retrieval focus:` line names the topic the strategist should query against the index. Run 2 to 3 angle queries per dimension when the question is broad.

## Scoring rubric (0 to 4)

| Score | Label | Meaning |
|---|---|---|
| 0 | Broken | Actively destroying the business. Fix this week. |
| 1 | Weak | Leaking value. Fix this month. |
| 2 | Functional | Doing its job, room to grow. Improve when capacity allows. |
| 3 | Strong | Competitive edge. Maintain. |
| 4 | Great | Leveraged and compounding. Document and copy this pattern into the weaker dimensions. |

Score whole numbers only. Round down on ties. Cite at least one piece of evidence from `profile.md` per score and at least one source (playbook name) from the retrieved chunks. If profile data is missing for a dimension, score `?` and flag the missing field.

## The 15 dimensions

### Pillar A. Offer (4 dimensions)

**1. Offer Strength**
*Measures:* Value Equation health. Are all four drivers (Dream Outcome, Perceived Likelihood, Time Delay, Effort and Sacrifice) firing in the operator's offer?
*Retrieval focus:* "value equation four drivers", "perceived likelihood of achievement", "dream outcome positioning"
*Profile pulls:* `one_line_pitch`, `core_offer_description`, `customer_aspiration`, `customer_pain_top3`
*Score 0:* leads with features, no proof, no timeline, customer does most of the work.
*Score 4:* outcome stated in customer's words, named-result proof on the page, week-1 visible progress, done-for-you delivery.

**2. Offer Differentiation**
*Measures:* Grand Slam Offer construction. Is this the "feel stupid to say no" offer, or one of many?
*Retrieval focus:* "grand slam offer", "stacking bonuses", "MAGIC offer naming framework"
*Profile pulls:* `core_offer_description`, `customer_alternative`
*Score 0:* identical to 3+ competitors, no bonuses, name describes the mechanism not the outcome.
*Score 4:* positioned uniquely in category, stacked with relevant bonuses, outcome-named.

**3. Pricing Position**
*Measures:* Are they charging enough, and is the model right?
*Retrieval focus:* "premium pricing strategy", "when to raise prices", "value-based pricing vs cost-plus"
*Profile pulls:* `current_price_range`, `pricing_model`, `unit_economics`, `payment_terms`, `currency`
*Score 0:* hourly, undercutting competitors, no premium tier, last raise over 18 months ago.
*Score 4:* priced 3-10x cost, value-based or tiered, upfront/deposit, raised in last 12 months.

**4. Risk Reversal**
*Measures:* Guarantees plus urgency. Is the "what if it does not work?" objection answered before it lands?
*Retrieval focus:* "conditional vs unconditional guarantees", "urgency and scarcity mechanisms"
*Profile pulls:* `guarantee_in_market`, `payment_terms`
*Score 0:* no guarantee, no urgency, no scarcity. Buying is pure trust.
*Score 4:* conditional or unconditional guarantee tied to the dream outcome, plus a real urgency mechanism live in market.

### Pillar B. Leads (3 dimensions)

**5. Lead Volume**
*Measures:* Daily activity bar. Are they hitting Rule of 100 on at least one Core Four channel?
*Retrieval focus:* "core four lead channels", "rule of 100 daily activity", "warm cold content paid outreach"
*Profile pulls:* `primary_channels`, `social_presence`
*Score 0:* no channel worked daily. Leads are sporadic.
*Score 4:* at least one Core Four channel hits Rule of 100 daily, tracked.

**6. Hook Quality**
*Measures:* Are hooks pulling attention across content, ads, outreach?
*Retrieval focus:* "hook construction", "callout curiosity contrast claim", "ad copy openers"
*Profile pulls:* `social_presence`, `website_purpose`, `funnel_description`
*Score 0:* opens with "we" or "I", no curiosity, no contrast, no specific claim.
*Score 4:* hooks use callout / curiosity / contrast / claim, variants tested, winners documented.

**7. Lead Capture**
*Measures:* On-ramp from attention to lead. Magnet, opt-in, low-friction handoff.
*Retrieval focus:* "lead magnets MAGIC framework", "opt-in conversion", "magnet to sequence"
*Profile pulls:* `website_url`, `website_purpose`, `funnel_description`
*Score 0:* traffic exits without capture. No magnet.
*Score 4:* relevant magnet, high-conversion landing, opt-in routed to follow-up sequence.

### Pillar C. Sales (3 dimensions)

**8. Sales Process**
*Measures:* Discovery to close. Is there a defined, repeatable structure?
*Retrieval focus:* "CLOSER framework", "discovery call structure", "sales process"
*Profile pulls:* `sales_process`, `current_conversion_rate`, `who_sells`
*Score 0:* ad hoc, founder-improvised, no script. Win rate unknown.
*Score 4:* defined process (CLOSER or equivalent), step-by-step conversion tracked, replicable by a non-founder.

**9. Objection Handling**
*Measures:* Top objections plus tested replies. Surfaced proactively in copy?
*Retrieval focus:* "objection handling formulas", "price time trust fit objections"
*Profile pulls:* `objections_top3`
*Score 0:* objections kill deals. Operator cannot name top three.
*Score 4:* top three named, each with a tested reply, surfaced in copy before they land in conversation.

**10. Sales Cadence**
*Measures:* Speed-to-lead plus follow-up math.
*Retrieval focus:* "speed to lead conversion", "follow-up sequence touches", "sales cadence"
*Profile pulls:* `sales_process`, `who_sells`, `funnel_description`
*Score 0:* leads sit for days. Single touch. No multi-channel follow-up.
*Score 4:* under 15 min speed-to-lead, 7+ touch follow-up, multi-channel.

### Pillar D. Money Model (2 dimensions)

**11. Money Model Design**
*Measures:* Revenue archetype mix. Continuity? Upsell? Win-back?
*Retrieval focus:* "money model archetypes", "attraction offer upsell continuity", "win-back offer"
*Profile pulls:* `pricing_model`, `revenue_stage`, `core_offer_description`
*Score 0:* single one-off offer. No upsell, continuity, or win-back.
*Score 4:* at least three of five archetypes live (attraction, upsell, downsell, continuity, win-back).

**12. Unit Economics**
*Measures:* LTV/CAC ratio, payback period, gross margin.
*Retrieval focus:* "LTV to CAC ratio", "30 day payback period", "fast cash mechanisms"
*Profile pulls:* `current_price_range`, `unit_economics`, `revenue_stage`
*Score 0:* LTV/CAC under 1, or operator does not know it. Burning cash to grow.
*Score 4:* LTV/CAC over 3, payback under 30 days, gross margin known and protected.

### Pillar E. Retention & Growth (3 dimensions)

**13. Retention & LTV**
*Measures:* Onboarding, milestone moments, churn triggers.
*Retrieval focus:* "onboarding first week milestone", "churn triggers retention", "lifetime value extension"
*Profile pulls:* `customer_proof_status`, `core_offer_description`
*Score 0:* no onboarding, no milestone tracking, churn unmeasured.
*Score 4:* defined onboarding with a week-1 milestone, retention measured monthly, win-back path exists.

**14. Brand & Proof**
*Measures:* Stacking proof. Named results. Credibility flywheel.
*Retrieval focus:* "proof stacking case studies", "brand recognition association", "content volume variance value"
*Profile pulls:* `customer_proof_status`, `social_presence`
*Score 0:* zero published proof. Operator invisible in the category.
*Score 4:* 10+ named-result case studies, regular content cadence, recognized in the niche.

**15. Operator Leverage**
*Measures:* Hours in vs on the business, scaling stage, role of founder.
*Retrieval focus:* "scaling roadmap founder stages", "operator leverage tools team content", "narrow niche wedge"
*Profile pulls:* `hours_in_vs_on_business`, `team_size`, `team_roles`, `biggest_bottleneck`
*Score 0:* founder is the entire business. 80%+ hours in delivery.
*Score 4:* founder spends 50%+ on the business, delegated delivery, leverage in tools/team/content.

## How /audit uses this

1. Read `profile.md`. Always. If missing, abort and redirect to `/onboard`.
2. Read this file (`_audit-dimensions.md`) for the rubric.
3. For each dimension in order (1 through 15):
   - Pull the `Retrieval focus:` queries.
   - Run `python3 brain/query.py "<query>" --top-k 5` via Bash. Run 2 to 3 queries per dimension when the focus has multiple angles.
   - Reason from the retrieved chunks plus the operator's profile.
4. Score 0 to 4 using the rubric. Cite profile evidence and at least one retrieved source.
5. Write one paragraph per dimension to `audit/findings.md`:
   - Score and label.
   - One sentence citing the profile evidence.
   - One sentence applying the retrieved Hormozi material (named source: which playbook).
   - One next move (cheapest action that would raise the score by one).
6. End `findings.md` with the five lowest-scored dimensions ranked, plus a one-paragraph Strategist's Read.
7. Append one line to `conversations/{today}.md`: "Audit complete. Lowest dimensions: {list}."

## How /plan uses this

See `brain/_plan-algorithm.md`.
