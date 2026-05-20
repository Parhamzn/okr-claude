# OKR file schema

Every file in `okrs/teams/` follows this format. Stick to it &mdash; the
slash commands parse these files line by line.

## Frontmatter

```yaml
---
team: growth                # kebab-case; matches the filename
owner: alice@embodyne.ai
quarter: 2026-Q2
status_date: 2026-05-13     # last refresh; auto-updated
parent: company             # which file's Os this team rolls up to
---
```

## Objectives

One `## O<n>:` heading per objective. Keep them qualitative and
inspirational; the measurement happens in the KRs below.

```markdown
## O1: Become the default brand for embodied AI data
```

## Key results

One `### KR<n>:` heading per KR, followed by a YAML-ish block of fields.

```markdown
### KR1: Inbound qualified leads 8/mo → 30/mo
- baseline: 8
- target: 30
- current: 14
- direction: up                              # up | down (down for latency, churn, cost)
- source: hubspot.deals[stage=qualified,quarter=2026-Q2]
- trajectory: yellow                         # green | yellow | red — recomputed on refresh
- confidence: 0.5                            # 0..1, human-owned
- depends_on:                                # cross-team KR refs
    - data-ops:O1.KR2
    - eng:O2.KR1
- last_human_update: 2026-05-12
- last_human_note: |
    Paused the LinkedIn campaign mid-April after creative fatigue.
    Restarting next Tuesday with new variants. Expect rebound by week 6.
- unwritten_risks: |
    Legal review of the new vendor contract is the silent gate; no ETA.
    Berlin sublease unsigned — affects collector throughput if Q3 budget slips.
```

The `depends_on` field captures *declared* cross-team coupling that the
dependency graph can render. `unwritten_risks` captures the dependencies the
team is silently betting on — vendor commitments, legal turnarounds, hiring,
infrastructure — that the graph cannot infer. Naming them keeps the
"interdependency illusion" honest: the graph is a starting point, not the map.

### Field rules

| Field | Owner | Notes |
|---|---|---|
| `baseline` | human, set once | Don't change after Q starts |
| `target` | human, set once | Same |
| `current` | Claude, refresh | Pulled from `source` |
| `direction` | human, optional | Defaults to `up` |
| `source` | human | A query Claude can resolve via MCP |
| `trajectory` | Claude, refresh | Computed from current vs linear pace |
| `confidence` | human | Gut check; Claude must not infer this |
| `depends_on` | human | `<team>:O<n>.KR<n>` references |
| `last_human_update` | human | Auto-warned if >3 weeks stale |
| `last_human_note` | human | The narrative; what the numbers don't show |
| `unwritten_risks` | human, optional | Tacit dependencies the dependency graph cannot see (e.g. "legal review timing", "vendor ship date", "key hire pending"). Free-form block scalar. Surfaced on team pages and in check-in drafts; agent never writes this field |

## Reserved sources

`source:` values use a `<provider>.<query>` convention. The provider must
match an entry in `.mcp.json`. Examples:

- `hubspot.deals[stage=qualified,quarter=2026-Q2]`
- `linear.cycles[team=growth].velocity`
- `ga4.event[name=signup_complete,range=q]`
- `warehouse.dim_users.weekly_active`
- `manual` &mdash; for KRs that aren't auto-pullable; `current:` stays
  human-owned and refreshes are no-ops.

Sources are not a real query language; they're hints. Claude parses
them, calls the appropriate MCP tool with reasonable inferred arguments,
and falls back to asking when ambiguous.
