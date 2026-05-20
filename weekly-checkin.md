---
description: Generate a weekly check-in draft for one team
argument-hint: <team-name>
allowed-tools: Read, Write, Glob, Bash(date:*)
model: claude-sonnet-4-5
---

Generate a weekly check-in draft for team **$1**.

## Procedure

1. Read `okrs/teams/$1.md`. If the file doesn't exist, list available
   teams and stop.

2. Read every other file in `okrs/teams/*.md` and `okrs/company.md`,
   parsing all `depends_on:` references. Build an in-memory map of which
   external KRs team $1 depends on, and which external KRs depend on
   team $1.

3. Determine the current quarter folder (e.g. `checkins/2026-Q2/`) from
   the team file's `quarter:` frontmatter. Determine the ISO week number
   for today (use `!date +%V`).

4. Write the draft to
   `checkins/<quarter>/week-<week>-$1.md`. If the file already exists,
   stop and ask the user whether to overwrite.

## Draft format

```markdown
# $1 &mdash; <quarter> week <NN>

_Generated <date>. Edit the "For human input" sections; the rest will
be regenerated next week._

## Trajectory at a glance

| KR | Current | Target | Pace | Trajectory |
|---|---|---|---|---|
| O1.KR1: <short label> | <current> | <target> | <linear pace target> | green/yellow/red |
| ... | | | | |

## What the numbers say

For each non-green KR, one tight paragraph:
- What the metric did since last week (use the previous check-in if
  one exists in the same folder, otherwise compare to the team file's
  `baseline`).
- What the team's `last_human_note` says about it.
- If the KR depends on another team's KR that is not green, name that
  dependency explicitly: "Upstream: eng:O2.KR1 is red; tutorial slip is
  the proximate risk to KR2."

Do not editorialize. Do not say "needs attention." The reader can tell.

## Upstream risks (depends_on)

A short list of external KRs that team $1 depends on, with current
trajectory. Only include yellow/red.

## Downstream impact

A short list of other teams' KRs that depend on team $1's KRs, with the
trajectory of the upstream (this team's) KR. Useful for the team to see
who they're blocking.

## For human input

_Leave blank for <owner from frontmatter> to fill in. This check-in is a draft until every question below has an answer._

### 1. What changed this week that the numbers don't show?

_(to be filled in)_

### 2. What's the plan for the at-risk KRs?

_(to be filled in)_

### 3. Any decisions you need from the founders or other teams?

_(to be filled in)_
```

## Why the human input section is structured this way

The check-in is a tool for forcing a conversation, not for producing a
status document. If you generate the data section and leave the human input
as a vague invitation, the team will skim it on Monday and the
"interesting" decisions never get made. Each question is its own block so
the UI can show, per question, whether it's been answered — and the
check-in is only marked **complete** when every block has real content.
The `_(to be filled in)_` placeholders are load-bearing: keep them
verbatim so downstream tooling can detect a draft.

## Voice

Founders read this on Monday morning. Lead with what's at risk. No
"I'd like to highlight," no "It's worth noting." A director should be
able to scan in 30 seconds and know which two KRs need a conversation.
