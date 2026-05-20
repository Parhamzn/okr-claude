# Cross-team OKR dependencies

_Generated 2026-05-13. Do not hand-edit; regenerate with `/dependency-graph`._

## Schema errors

none

## Graph

```mermaid
graph LR
    company_O1_KR1["company:O1.KR1<br/>3 signed pilots"]:::yellow
    company_O1_KR2["company:O1.KR2<br/>500k validated demos"]:::red
    company_O2_KR1["company:O2.KR1<br/>Median quality > 0.85"]:::yellow
    company_O2_KR2["company:O2.KR2<br/>QA pipeline < 2h/10k"]:::yellow

    growth_O1_KR1["growth:O1.KR1<br/>Inbound qualified leads"]:::yellow
    growth_O1_KR2["growth:O1.KR2<br/>Organic search traffic"]:::yellow
    growth_O1_KR3["growth:O1.KR3<br/>Brand recall"]:::red
    growth_O2_KR1["growth:O2.KR1<br/>MQL → pilot cycle time"]:::green

    data_ops_O1_KR1["data-ops:O1.KR1<br/>Active collectors/wk"]:::yellow
    data_ops_O1_KR2["data-ops:O1.KR2<br/>Demo collection rate"]:::yellow
    data_ops_O2_KR1["data-ops:O2.KR1<br/>Equipment turnaround"]:::yellow
    data_ops_O2_KR2["data-ops:O2.KR2<br/>New-collector ramp"]:::yellow

    eng_O1_KR1["eng:O1.KR1<br/>Collector app NPS"]:::green
    eng_O1_KR2["eng:O1.KR2<br/>QA throughput"]:::red
    eng_O2_KR1["eng:O2.KR1<br/>In-app tutorial"]:::red
    eng_O2_KR2["eng:O2.KR2<br/>API rate-limit headroom"]:::green
    eng_O2_KR3["eng:O2.KR3<br/>Site IA refactor"]:::yellow

    data_ops_O1_KR2 --> growth_O1_KR1
    data_ops_O1_KR1 --> company_O1_KR2
    data_ops_O1_KR2 --> company_O1_KR2
    eng_O1_KR1 --> data_ops_O1_KR2
    eng_O2_KR1 --> data_ops_O2_KR2
    eng_O2_KR3 --> growth_O1_KR2
    eng_O1_KR1 --> company_O2_KR1
    eng_O1_KR2 --> company_O2_KR2

    classDef green fill:#86efac,stroke:#16a34a
    classDef yellow fill:#fde68a,stroke:#ca8a04
    classDef red fill:#fca5a5,stroke:#dc2626
```

## Critical chains

- `eng:O2.KR1` (red, in-app tutorial) → `data-ops:O2.KR2` (yellow, new-collector ramp)
- `eng:O1.KR2` (red, QA throughput) → `company:O2.KR2` (yellow, QA pipeline < 2h/10k)
- `eng:O2.KR3` (yellow, site IA) → `growth:O1.KR2` (yellow, organic traffic)
- `data-ops:O1.KR1` (yellow, active collectors) → `company:O1.KR2` (red, 500k validated demos)
- `data-ops:O1.KR2` (yellow, collection rate) → `company:O1.KR2` (red, 500k validated demos)

The cleanest signal in this graph: `company:O1.KR2` is red and its two
direct upstreams are both yellow. Either the upstream targets are too
soft, or the company-level target is too aggressive. Worth a founder
conversation before the midpoint review.
