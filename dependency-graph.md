---
description: Produce a Mermaid graph of cross-team KR dependencies
allowed-tools: Read, Write, Glob
model: claude-sonnet-4-5
---

Scan every team OKR file and produce a Mermaid graph of cross-team KR
dependencies. Write the result to `dependency-graph.md` at the repo root.

## Procedure

1. Read every `okrs/teams/*.md` and `okrs/company.md`. Parse all
   `### KR<n>:` blocks. For each, capture:
   - canonical id: `<team>:O<n>.KR<n>`
   - short label (the heading text after the KR number)
   - trajectory (green / yellow / red)
   - depends_on list (canonical ids of upstream KRs)

2. Verify every `depends_on:` reference resolves to a real KR. If any
   are dangling, list them at the top of the output file under a
   `## Schema errors` heading and proceed.

3. Build a Mermaid `graph LR` directed graph:
   - Nodes use the canonical id as the node id and the short label
     in the display.
   - Style nodes by trajectory: green = `fill:#86efac`,
     yellow = `fill:#fde68a`, red = `fill:#fca5a5`.
   - Edges go upstream &rarr; downstream.

4. After the graph, write a "Critical chains" section listing every
   path where a red or yellow upstream feeds into a red or yellow
   downstream. Format each as a one-liner:
   `eng:O2.KR1 (red) -> data-ops:O2.KR2 (yellow) -> company:O1.KR2 (red)`

## Output template

```markdown
# Cross-team OKR dependencies

_Generated <date>. Do not hand-edit; regenerate with `/dependency-graph`._

## Schema errors

<list dangling refs, or "none">

## Graph

\`\`\`mermaid
graph LR
    growth_O1_KR1["growth:O1.KR1<br/>Inbound leads"]:::yellow
    data_ops_O1_KR2["data-ops:O1.KR2<br/>Collection rate"]:::yellow
    data_ops_O1_KR2 --> growth_O1_KR1
    ...
    classDef green fill:#86efac,stroke:#16a34a
    classDef yellow fill:#fde68a,stroke:#ca8a04
    classDef red fill:#fca5a5,stroke:#dc2626
\`\`\`

## Critical chains

- eng:O2.KR1 (red, "in-app tutorial") -> data-ops:O2.KR2 (yellow, "new-collector ramp") -> company:O1.KR2 (red, "demonstrations validated")
- ...
```

Mermaid node ids can't contain colons or dots; substitute underscores
(`growth:O1.KR1` &rarr; `growth_O1_KR1`).
