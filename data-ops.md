---
team: data-ops
owner: chen@embodyne.ai
quarter: 2026-Q2
status_date: 2026-05-13
parent: company
---

# Data operations team OKRs &mdash; 2026 Q2

## O1: Scale the data-collection footprint without losing quality

### KR1: Active demonstration collectors per week 40 → 180
- baseline: 40
- target: 180
- current: 95
- direction: up
- source: warehouse.dim_collectors.weekly_active
- trajectory: yellow
- confidence: 0.6
- depends_on: []
- last_human_update: 2026-05-13
- last_human_note: |
    Berlin studio came online week 4. Munich studio onboarding starts
    week 7. Contractor pipeline healthy; bottleneck is now equipment
    provisioning.

### KR2: Demonstration collection rate 8k/wk → 35k/wk
- baseline: 8000
- target: 35000
- current: 17500
- direction: up
- source: warehouse.fact_demonstrations.weekly_count
- trajectory: yellow
- confidence: 0.65
- depends_on:
    - eng:O1.KR1
- last_human_update: 2026-05-13
- last_human_note: |
    Per-collector throughput up 30% since the new task UI shipped.
    Volume is gated on collector count, not per-collector rate.

## O2: Build the supply-side infrastructure for the next 10x

### KR1: Equipment turnaround time (order to in-hand) under 5 days
- baseline: 14
- target: 5
- current: 9
- direction: down
- source: manual
- trajectory: yellow
- confidence: 0.6
- depends_on: []
- last_human_update: 2026-05-10
- last_human_note: |
    Switched to a regional logistics partner in week 3. Working on
    pre-positioned inventory in Berlin and Zurich.

### KR2: New-collector ramp time (signup to first validated batch) under 7 days
- baseline: 21
- target: 7
- current: 12
- direction: down
- source: warehouse.fact_collectors.median_ramp_days
- trajectory: yellow
- confidence: 0.65
- depends_on:
    - eng:O2.KR1
- last_human_update: 2026-05-13
- last_human_note: |
    New onboarding flow live since week 5. Awaiting the in-app
    tutorial from eng to close the last 3 days.
