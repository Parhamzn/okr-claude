---
description: Draft next quarter's OKRs for a team using this quarter's results as input
argument-hint: <team-name>
allowed-tools: Read, Glob
model: claude-opus-4-7
---

Help the team **$1** draft their next quarter's OKRs.

You are **not** writing the final OKRs. You are producing a structured
input document for the team's planning session.

## Procedure

1. Read `okrs/teams/$1.md` for the current quarter's state.

2. Read every check-in for team $1 under `checkins/<current-quarter>/`
   to understand the trajectory over time.

3. Read `okrs/company.md` for the company's next-quarter direction (the
   user should have updated this before running you; if `quarter:`
   still reads as the current one, stop and tell them).

4. Produce a planning document with these sections:

### Carryover candidates

Current-quarter KRs that didn't fully land and might roll over. For each:
- Final number vs target.
- The team's `last_human_note` from the last check-in.
- Your assessment: was this *under-resourced*, *mis-scoped*, or
  *deprioritized*? Be explicit; don't hedge. The team needs a real read.

### Promotion candidates

KRs that landed comfortably (>=1.0 by week 10) and suggest the team can
aim higher next quarter. Note what a stretched version might look like.

### Demotion candidates

KRs that landed with effort wildly disproportionate to impact. Be honest;
this is the section that gets cut from polite planning docs and is the
most valuable.

### Open strategic questions for the founders

Two to four genuine questions the team should resolve with the founders
before drafting. Examples: "Are we still betting on Berlin, or shifting
to Munich?" Not throat-clearing; real forks.

### Suggested objective drafts

Two to three candidate objectives for next quarter, each with three to
five candidate KRs. These should pull from the company OKRs. Mark each
with `[stretch]` or `[committed]`.

## Voice

Critical and direct. The team will use this to argue with each other.
If you write the safe consensus version, you've failed.
