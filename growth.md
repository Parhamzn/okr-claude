---
team: growth
owner: bea@embodyne.ai
quarter: 2026-Q2
status_date: 2026-05-13
parent: company
---

# Growth team OKRs &mdash; 2026 Q2

## O1: Make the brand impossible to miss for embodied AI buyers

### KR1: Inbound qualified leads 8/mo → 30/mo
- baseline: 8
- target: 30
- current: 14
- direction: up
- source: hubspot.deals[stage=qualified,quarter=2026-Q2]
- trajectory: yellow
- confidence: 0.5
- depends_on:
    - data-ops:O1.KR2
- last_human_update: 2026-05-12
- last_human_note: |
    Paused the LinkedIn campaign mid-April after creative fatigue.
    Restarting next Tuesday with three new variants. Expect rebound
    by week 6.

### KR2: Organic search traffic 3k → 12k monthly visitors
- baseline: 3000
- target: 12000
- current: 5400
- direction: up
- source: ga4.metric[name=sessions,segment=organic,range=q]
- trajectory: yellow
- confidence: 0.55
- depends_on:
    - eng:O2.KR3
- last_human_update: 2026-05-13
- last_human_note: |
    Content cadence is on track (6 of 9 long-form pieces shipped).
    Blocked on the new landing-page IA from eng &mdash; current pages
    don't rank well for the comparison-shopper queries.

### KR3: Unaided brand recall in ICP from 4% to 18%
- baseline: 4
- target: 18
- current: 4
- direction: up
- source: manual
- trajectory: red
- confidence: 0.3
- depends_on: []
- last_human_update: 2026-04-30
- last_human_note: |
    Q1 survey was the baseline; Q2 survey scheduled for week 10. No
    new signal yet. Honest read: ambitious target for a single
    quarter; revisiting at midpoint.

## O2: Build a repeatable pipeline from first-touch to signed contract

### KR1: Cycle time from MQL to signed pilot under 45 days
- baseline: 78
- target: 45
- current: 64
- direction: down
- source: hubspot.deals[stage=closed_won,quarter=2026-Q2].avg_cycle_days
- trajectory: green
- confidence: 0.7
- depends_on: []
- last_human_update: 2026-05-13
- last_human_note: ""
