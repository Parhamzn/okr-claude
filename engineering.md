---
team: eng
owner: dmitri@embodyne.ai
quarter: 2026-Q2
status_date: 2026-05-13
parent: company
---

# Engineering team OKRs &mdash; 2026 Q2

## O1: Ship a quality-first data platform

### KR1: Collector app rated 4.5+ in median weekly NPS
- baseline: 3.6
- target: 4.5
- current: 4.1
- direction: up
- source: warehouse.fact_collector_nps.weekly_median
- trajectory: green
- confidence: 0.75
- depends_on: []
- last_human_update: 2026-05-13
- last_human_note: ""

### KR2: QA pipeline throughput 1k → 5k demonstrations per hour
- baseline: 1000
- target: 5000
- current: 1800
- direction: up
- source: linear.cycles[team=eng,label=qa].throughput_per_hour
- trajectory: red
- confidence: 0.5
- depends_on: []
- last_human_update: 2026-05-13
- last_human_note: |
    Dedup stage is the bottleneck. Batched implementation is in
    review; expecting 2.5x once merged in week 7.

## O2: Build the surface area the rest of the company depends on

### KR1: In-app collector onboarding tutorial shipped
- baseline: 0
- target: 1
- current: 0
- direction: up
- source: manual
- trajectory: red
- confidence: 0.7
- depends_on: []
- last_human_update: 2026-05-09
- last_human_note: |
    Slipped by 2 weeks from original plan. New estimate: end of
    week 8. This is a binary KR; risk for data-ops:O2.KR2.

### KR2: Public API rate-limit headroom for partner integrations
- baseline: 100
- target: 1000
- current: 450
- direction: up
- source: warehouse.fact_api_capacity.peak_rps
- trajectory: green
- confidence: 0.8
- depends_on: []
- last_human_update: 2026-05-11
- last_human_note: ""

### KR3: Public-facing site IA refactor live with comparison-shopper paths
- baseline: 0
- target: 1
- current: 0
- direction: up
- source: manual
- trajectory: yellow
- confidence: 0.6
- depends_on: []
- last_human_update: 2026-05-13
- last_human_note: |
    Design approved; implementation starts week 7. Should be live
    end of week 9.
