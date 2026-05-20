---
team: company
owner: founders@embodyne.ai
quarter: 2026-Q2
status_date: 2026-05-13
parent: null
---

# Company OKRs &mdash; 2026 Q2

## O1: Become the default supplier of multimodal demonstration data for embodied AI labs

### KR1: Three signed pilots with frontier embodied AI labs
- baseline: 0
- target: 3
- current: 1
- direction: up
- source: manual
- trajectory: yellow
- confidence: 0.6
- depends_on: []
- last_human_update: 2026-05-12
- last_human_note: |
    One pilot signed (Lab A). Two LOIs in negotiation (Lab B, Lab C);
    legal is the gating factor on both.

### KR2: 500k validated demonstrations in the library, up from 80k
- baseline: 80000
- target: 500000
- current: 142000
- direction: up
- source: warehouse.dim_demonstrations.validated_count
- trajectory: red
- confidence: 0.6
- depends_on:
    - data-ops:O1.KR1
    - data-ops:O2.KR2
- last_human_update: 2026-05-20
- last_human_note: |
    Collection ramp is slower than planned. Berlin studio onboarding
    took 5 weeks instead of 2 (visa + lease delays). Discussing whether
    to descope to 350k or push hard on contractor throughput.

## O2: Establish a defensible technical moat in data quality

### KR1: Median demonstration quality score > 0.85 (internal rubric)
- baseline: 0.72
- target: 0.85
- current: 0.79
- direction: up
- source: warehouse.fact_quality_scores.weekly_median
- trajectory: yellow
- confidence: 0.7
- depends_on:
    - eng:O1.KR1
- last_human_update: 2026-05-13
- last_human_note: ""

### KR2: Quality QA pipeline runs in <2h per 10k demonstrations
- baseline: 9
- target: 2
- current: 5.5
- direction: down
- source: linear.issues[label=qa-pipeline].cycle_time_hours
- trajectory: yellow
- confidence: 0.55
- depends_on:
    - eng:O1.KR2
- last_human_update: 2026-05-20
- last_human_note: |
    GPU bottleneck in the dedup stage. New batched implementation
    landing in week 7.
