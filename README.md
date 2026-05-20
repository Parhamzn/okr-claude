# okr-claude

A working scaffold for treating OKRs as a thin, agent-mediated alignment
layer instead of a managed process.

## Why this exists

The standard OKR ritual — quarterly drafting, a polished Notion doc,
weekly status updates manually written and rarely read — fails for the
same reason most coordination rituals fail at scale: it asks humans to
be the relay layer between *what teams are actually doing* and *what
leadership thinks they're doing*. The relay distorts. Drift compounds
silently. By the time it shows up in a quarterly review, it's already
the company's trajectory.

This scaffold is a small attempt at a different model. Team OKRs live
as version-controlled markdown. A Claude Code agent loop, scheduled via
CI, pulls current metric values from connected MCP servers, recomputes
trajectory, surfaces cross-team dependency drift, and produces weekly
check-in drafts that teams react to instead of write from scratch. The
human layer keeps the *judgment* — confidence calls, narrative,
trade-off decisions — and offloads the *plumbing*: metric collection,
draft generation, dependency graphing, consistency checks across team
files.

The principle: keep the alignment layer thin enough that drift surfaces
before it compounds.

## What's in the repo

```
okrs/
  SCHEMA.md          canonical file format
  company.md         company-level OKRs
  teams/
    growth.md
    data-ops.md
    engineering.md
checkins/
  2026-Q2/
    week-19-growth.md   sample generated check-in
dependency-graph.md       sample generated cross-team graph
.claude/
  commands/
    refresh-metrics.md    pull current values, recompute trajectory
    weekly-checkin.md     generate per-team check-in drafts
    dependency-graph.md   regenerate the cross-team graph
    draft-quarter.md      end-of-Q planning input doc
  settings.json
.mcp.json                  MCP server wiring (Linear, HubSpot, GA4, warehouse)
.github/
  workflows/
    weekly-refresh.yml     scheduled refresh + PR
CLAUDE.md                  persistent agent context
```

The example data is tailored to a hypothetical embodied-AI data company
— I chose that domain because it has the operational complexity
(cross-border contractor ops, multi-stack data pipelines, the coupling
between research and data operations) that genuinely stress-tests the
system. The scaffold works for any domain.

## The four slash commands

Each command lives in `.claude/commands/<name>.md` and is invoked from
inside a Claude Code session with `/<name>`.

- **`/refresh-metrics`** &mdash; reads every team OKR file, parses each KR's
  `source:` field, calls the matching MCP server, updates `current:`
  and recomputes `trajectory:` per the formula in `CLAUDE.md`. Leaves
  human-owned fields (`confidence`, `last_human_note`) untouched.
  Outputs a summary plus a `git diff --stat` so changes are reviewable.

- **`/weekly-checkin <team>`** &mdash; generates a check-in draft for the
  named team, scanning every other team file for upstream and
  downstream dependencies that are off-track. Writes to
  `checkins/<quarter>/week-<NN>-<team>.md`. Leaves the "For human
  input" section blank.

- **`/dependency-graph`** &mdash; scans every team file, builds a Mermaid
  directed graph of cross-team KR dependencies colored by trajectory,
  and identifies critical chains where red or yellow upstreams feed
  into red or yellow downstreams.

- **`/draft-quarter <team>`** &mdash; end-of-quarter planning input.
  Categorizes current KRs as carryover, promotion, or demotion
  candidates, then drafts two to three candidate objectives for next
  quarter aligned with the company-level OKRs.

## How the human and agent split work

The single most important design choice in this scaffold is what the
agent is *not* allowed to do.

- The agent **may** update `current:`, `status_date:`, and
  `trajectory:` during a refresh, regenerate check-in drafts, and
  regenerate the dependency graph.
- The agent **may not** modify objectives, key results, baselines,
  targets, `confidence:`, `last_human_update:`, or `last_human_note:`.
  Those fields belong to the people doing the work.
- The agent **escalates** rather than guessing when a team file is
  malformed, when a `depends_on:` reference points to a KR that
  doesn't exist, when an MCP source returns wildly off-trend data, or
  when a human note has been stale for more than three weeks.

The point is not to automate alignment. The point is to remove enough
plumbing that humans can actually have the conversation alignment
requires. Generate the situational read; leave the decisions.

## Running it

```bash
# install Claude Code
npm install -g @anthropic-ai/claude-code

# clone, then from inside the repo
claude                                    # interactive; try /weekly-checkin growth

# or headless
claude --print "/refresh-metrics"
claude --print "/weekly-checkin growth"
claude --print "/dependency-graph"
```

For automation, `.github/workflows/weekly-refresh.yml` runs the three
commands every Monday morning and opens a PR with the diff for human
review.

## Hosting the web UI

`okr-ui/` is a small Flask app that reads (and surgically edits) the OKR
markdown files. Three realistic deployment shapes:

### A. Local per-user (simplest)

Each team member clones the repo and runs the UI on their own laptop.
The OKR data is the same git repo they're editing; the UI is just a
nicer editor than a text editor.

```bash
git clone <repo-url>
cd <repo-name>
pip install -r okr-ui/requirements.txt
python okr-ui/app.py
open http://localhost:5050
```

No auth needed (it's localhost). Changes get committed and pushed via
git like normal. The weekly GitHub Action still runs the agent loop.

### B. One shared instance for the team

Deploy the Dockerfile in `okr-ui/Dockerfile` to any container host —
Render, Fly.io, Railway, or your own server. The image bakes in the
demo OKR markdown files at `/data` so a fresh container is immediately
usable; mount a persistent volume at `/data` later to use your team's
real OKRs and keep edits across restarts.

Locally:

```bash
docker build -t okr-ui -f okr-ui/Dockerfile .       # build context = repo root
docker run -p 5050:5050 \
  -e OKR_UI_USER=team \
  -e OKR_UI_PASSWORD='change-me' \
  okr-ui
```

On Render: connect the GitHub repo, choose **Docker** as the runtime,
set **Dockerfile Path** to `okr-ui/Dockerfile`, leave the build context
on its default (repo root). Add the two `OKR_UI_*` env vars and you're
done. Free tier is enough for a small team; cold start after idle is
~30 s. For persistent edits, add a Render Persistent Disk mounted at
`/data` and seed it once via Render's shell.

### C. SaaS for any company

Out of scope for this scaffold. Would need multi-tenant auth, per-org
data isolation, billing, and the markdown-as-source-of-truth assumption
breaks down once you're not a single git repo. A different project.

## What this scaffold is not

It's not an OKR tool replacement (yet). It's not a substitute for the
conversations OKRs are supposed to force. If your team starts reading
the generated check-ins without editing the "For human input" sections,
you've automated the ritual and lost the substance. The right response
then is to delete the system, not double down on it.

It's also not the only design that solves this problem. The same
pattern — operational artifacts as markdown plus an agent for the
plumbing — would work for monthly investor updates, hiring pipeline
reviews, vendor renewals, board prep, and incident retros. OKRs are
the demo because they're the most obviously broken existing artifact.

The unifying claim: a startup's operating system is mostly
semi-structured prose with embedded numbers and cross-references.
That's exactly the substrate that LLMs handle well, and the build cost
of wiring it up has just dropped by an order of magnitude.

## Open questions I haven't resolved

A working scaffold is not the same as a working system. Honest open
items:

- *The adoption problem.* Engineering teams will edit YAML in git.
  Most non-eng teams will not. A real version of this needs a thin web
  UI or Slack bot that writes to the markdown files.
- *Implicit dependencies.* The graph only sees what's in `depends_on:`
  fields. The most damaging dependencies are usually unwritten. The
  scaffold should over time surface candidate dependencies it infers
  from the data, but the trust calibration on that is non-trivial.
- *The check-in paradox.* The risk of frictionless check-in
  generation is that nobody reads them carefully. The "For human
  input" block is a guardrail; it's not a solution.

If any of these get solved in a way I haven't thought of, I'd want to
know.
