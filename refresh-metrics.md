---
description: Pull current values for every KR from connected sources and update team files
allowed-tools: Read, Edit, Glob, Bash(date:*), Bash(git diff:*)
model: claude-sonnet-4-5
---

You are running the weekly metric refresh. Update every team OKR file in
place with current values from connected data sources.

## Procedure

1. List every file matching `okrs/teams/*.md` and `okrs/company.md`.

2. For each file, parse the frontmatter and every `### KR<n>:` block.
   The format is defined in `okrs/SCHEMA.md` &mdash; read that file first
   if you have any doubt about the schema.

3. For each KR with `source:` not equal to `manual`:
   - Parse the source string `<provider>.<query>`.
   - Call the matching MCP server (see `.mcp.json` for what's wired up).
   - Update `current:` to the returned value.
   - Recompute `trajectory:` per the formula in `CLAUDE.md`.
   - Update the file's frontmatter `status_date:` to today's date
     (use `!date +%Y-%m-%d`).

4. **Do not touch** `confidence:`, `last_human_update:`, or
   `last_human_note:`. Those are human-owned.

5. If a source can't be resolved, leave `current:` unchanged and append
   `# unresolved !date +%Y-%m-%d` to that line as a comment. Then list
   the unresolved sources at the end of your summary so the user can fix
   them.

6. After all files are updated, run `!git diff --stat okrs/` and include
   it in your output so the user can see what moved.

## Output format

A single short summary block, then the git diff stat. Example:

```
Refreshed 12 KRs across 3 teams.

Notable moves:
- growth:O1.KR1 (inbound leads): 11 -> 14 (yellow stays yellow)
- data-ops:O1.KR2 (collection rate): 14200 -> 17500 (yellow -> yellow)
- eng:O1.KR2 (QA throughput): 1600 -> 1800 (red stays red)

Unresolved:
- growth:O1.KR3 (manual; brand survey not yet conducted)

[git diff --stat output here]
```

Keep it to that scale. No prose preamble.
