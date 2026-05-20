"""Parse and surgically edit OKR markdown files defined by SCHEMA.md.

The agent loop owns most fields. This module only writes back
human-owned ones (confidence, last_human_note, last_human_update).
Everything else is preserved verbatim, byte for byte where possible.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import yaml


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
OBJ_RE = re.compile(r"^## (O\d+):\s*(.+)$", re.MULTILINE)
KR_RE = re.compile(r"^### (KR\d+):\s*(.+)$", re.MULTILINE)
FIELD_LINE_RE = re.compile(r"^- (\w+):")


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, text[m.end():]


def parse_kr_block(block: str) -> dict:
    """Parse a KR's `- key: value` field list into a flat dict."""
    if not block.strip():
        return {}
    try:
        items = yaml.safe_load(block)
    except yaml.YAMLError:
        return {"_parse_error": True}
    if not items:
        return {}
    merged: dict = {}
    for item in items:
        if isinstance(item, dict):
            merged.update(item)
    return merged


def parse_team_file(path: Path) -> dict:
    text = Path(path).read_text()
    fm, body = parse_frontmatter(text)
    team_name = fm.get("team", "?")

    objectives = []
    obj_matches = list(OBJ_RE.finditer(body))
    for i, m in enumerate(obj_matches):
        end = obj_matches[i + 1].start() if i + 1 < len(obj_matches) else len(body)
        obj_body = body[m.end():end]

        krs = []
        kr_matches = list(KR_RE.finditer(obj_body))
        for j, km in enumerate(kr_matches):
            kend = kr_matches[j + 1].start() if j + 1 < len(kr_matches) else len(obj_body)
            data = parse_kr_block(obj_body[km.end():kend])
            data["id"] = km.group(1)
            data["title"] = km.group(2).strip()
            data["canonical_id"] = f"{team_name}:{m.group(1)}.{km.group(1)}"
            krs.append(data)

        objectives.append({
            "id": m.group(1),
            "title": m.group(2).strip(),
            "krs": krs,
        })

    return {
        "frontmatter": fm,
        "objectives": objectives,
        "path": str(path),
    }


def discover_team_files(data_dir: Path) -> dict[str, Path]:
    """Find every .md file whose frontmatter declares a `team:`.

    Empty (just-bootstrapped) team files count too — they have no objectives
    yet but the UI needs them discoverable so users can add the first one.
    """
    teams: dict[str, Path] = {}
    for path in sorted(data_dir.glob("*.md")):
        try:
            text = path.read_text()
        except OSError:
            continue
        if not text.startswith("---"):
            continue
        fm, _ = parse_frontmatter(text)
        team = fm.get("team")
        if team:
            teams[team] = path
    return teams


def find_kr_bounds(lines: list[str], obj_id: str, kr_id: str) -> Optional[tuple[int, int]]:
    """Line bounds [start, end) for a KR's field block (the lines after ### header)."""
    in_obj = False
    in_kr = False
    kr_start: Optional[int] = None

    for i, line in enumerate(lines):
        if line.startswith(f"## {obj_id}:"):
            in_obj = True
            continue
        if in_obj and line.startswith("## ") and not line.startswith(f"## {obj_id}:"):
            in_obj = False
            continue
        if in_obj and line.startswith(f"### {kr_id}:"):
            in_kr = True
            kr_start = i + 1
            continue
        if in_kr and (line.startswith("### ") or line.startswith("## ")):
            return (kr_start, i)

    if kr_start is not None:
        return (kr_start, len(lines))
    return None


def find_field_bounds(kr_lines: list[str], field: str) -> Optional[tuple[int, int]]:
    """Line bounds [start, end) for one field within a KR block.

    A field starts at `^- field:` and continues until the next `^- otherfield:`
    or the next section header. Continuation lines of a YAML block scalar
    (indented under `field: |`) are included. Trailing blank lines are
    treated as separators between fields and excluded from the bounds.
    """
    start: Optional[int] = None
    for i, line in enumerate(kr_lines):
        if re.match(rf"^- {re.escape(field)}:", line):
            start = i
            break
    if start is None:
        return None
    end = len(kr_lines)
    for j in range(start + 1, len(kr_lines)):
        line = kr_lines[j]
        if FIELD_LINE_RE.match(line) or line.startswith(("# ", "## ", "### ")):
            end = j
            break
    while end > start + 1 and kr_lines[end - 1].strip() == "":
        end -= 1
    return (start, end)


def replace_field(kr_lines: list[str], field: str, new_lines: list[str]) -> list[str]:
    bounds = find_field_bounds(kr_lines, field)
    if bounds is None:
        return kr_lines + new_lines
    s, e = bounds
    return kr_lines[:s] + new_lines + kr_lines[e:]


def _block_scalar_field(field: str, value: str) -> list[str]:
    """Build a YAML list-item field with a literal block scalar value."""
    if value.strip() == "":
        return [f'- {field}: ""']
    out = [f"- {field}: |"]
    for line in value.rstrip().split("\n"):
        out.append(f"    {line}" if line else "")
    return out


def _ensure_field(kr_lines: list[str], field: str, new_lines: list[str]) -> list[str]:
    """Replace `field` if present; otherwise append it at the end of the KR block."""
    if find_field_bounds(kr_lines, field) is not None:
        return replace_field(kr_lines, field, new_lines)
    while kr_lines and kr_lines[-1].strip() == "":
        kr_lines = kr_lines[:-1]
    return kr_lines + new_lines + [""]


def update_kr_human_fields(
    path: Path,
    obj_id: str,
    kr_id: str,
    *,
    note: Optional[str] = None,
    confidence: Optional[float] = None,
    update_date: Optional[str] = None,
    unwritten_risks: Optional[str] = None,
) -> None:
    """Surgically rewrite the human-owned fields for one KR. Leaves everything else alone."""
    text = Path(path).read_text()
    trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if trailing_newline and lines and lines[-1] == "":
        lines = lines[:-1]

    bounds = find_kr_bounds(lines, obj_id, kr_id)
    if bounds is None:
        raise ValueError(f"KR {obj_id}.{kr_id} not found in {path}")
    kr_start, kr_end = bounds
    kr_lines = lines[kr_start:kr_end]

    if note is not None:
        kr_lines = replace_field(kr_lines, "last_human_note", _block_scalar_field("last_human_note", note))

    if confidence is not None:
        rounded = round(float(confidence), 2)
        kr_lines = replace_field(kr_lines, "confidence", [f"- confidence: {rounded}"])

    if update_date is not None:
        kr_lines = replace_field(
            kr_lines, "last_human_update", [f"- last_human_update: {update_date}"]
        )

    if unwritten_risks is not None:
        kr_lines = _ensure_field(
            kr_lines, "unwritten_risks",
            _block_scalar_field("unwritten_risks", unwritten_risks),
        )

    new_lines = lines[:kr_start] + kr_lines + lines[kr_end:]
    new_text = "\n".join(new_lines)
    if trailing_newline:
        new_text += "\n"
    Path(path).write_text(new_text)


def linear_pace_target(baseline: float, target: float, weeks_elapsed: int, total_weeks: int = 13) -> float:
    if total_weeks <= 0:
        return target
    return baseline + (target - baseline) * (weeks_elapsed / total_weeks)


def extract_mermaid(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    text = path.read_text()
    m = re.search(r"```mermaid\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else None


def next_objective_id(objectives: list[dict]) -> str:
    nums = []
    for o in objectives:
        m = re.match(r"O(\d+)", o.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    return f"O{(max(nums) + 1) if nums else 1}"


def next_kr_id(objective: dict) -> str:
    nums = []
    for kr in objective.get("krs", []):
        m = re.match(r"KR(\d+)", kr.get("id", ""))
        if m:
            nums.append(int(m.group(1)))
    return f"KR{(max(nums) + 1) if nums else 1}"


def create_team_file(
    path: Path,
    *,
    team: str,
    owner: str,
    quarter: str,
    parent: str = "company",
    today: str,
) -> None:
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    body = (
        f"---\n"
        f"team: {team}\n"
        f"owner: {owner}\n"
        f"quarter: {quarter}\n"
        f"status_date: {today}\n"
        f"parent: {parent}\n"
        f"---\n\n"
        f"# {team} team OKRs &mdash; {quarter}\n"
    )
    path.write_text(body)


def _splice_block(
    lines: list[str], insert_at: int, block_lines: list[str]
) -> list[str]:
    """Insert block_lines between lines[:insert_at] and lines[insert_at:], normalizing
    blank-line gaps to exactly one on each side."""
    prefix = lines[:insert_at]
    suffix = lines[insert_at:]
    while prefix and prefix[-1].strip() == "":
        prefix = prefix[:-1]
    while suffix and suffix[0].strip() == "":
        suffix = suffix[1:]
    out = list(prefix)
    if prefix:
        out.append("")
    out.extend(block_lines)
    if suffix:
        out.append("")
        out.extend(suffix)
    return out


def add_objective(path: Path, title: str) -> str:
    """Append a new objective to the team file. Returns the new objective id."""
    parsed = parse_team_file(path)
    new_id = next_objective_id(parsed["objectives"])
    text = path.read_text()
    trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if trailing_newline and lines and lines[-1] == "":
        lines = lines[:-1]

    new_lines = _splice_block(lines, len(lines), [f"## {new_id}: {title.strip()}"])
    new_text = "\n".join(new_lines)
    if trailing_newline or True:
        new_text += "\n"
    path.write_text(new_text)
    return new_id


def add_kr(
    path: Path,
    obj_id: str,
    *,
    title: str,
    baseline: float | int | str,
    target: float | int | str,
    direction: str = "up",
    source: str = "manual",
    today: str,
    depends_on: list[str] | None = None,
) -> str:
    """Append a new KR under the given objective. Returns the new KR id."""
    parsed = parse_team_file(path)
    objective = next((o for o in parsed["objectives"] if o["id"] == obj_id), None)
    if objective is None:
        raise ValueError(f"Objective {obj_id} not found in {path}")
    new_id = next_kr_id(objective)

    text = path.read_text()
    lines = text.split("\n")
    if text.endswith("\n") and lines and lines[-1] == "":
        lines = lines[:-1]

    # Find where this objective ends — insert before the next ## (or at EOF)
    obj_header = f"## {obj_id}:"
    insert_at: int | None = None
    in_obj = False
    for i, line in enumerate(lines):
        if line.startswith(obj_header):
            in_obj = True
            continue
        if in_obj and line.startswith("## "):
            insert_at = i
            break
    if insert_at is None:
        insert_at = len(lines)

    block_lines = [
        f"### {new_id}: {title.strip()}",
        f"- baseline: {baseline}",
        f"- target: {target}",
        f"- current: {baseline}",
        f"- direction: {direction}",
        f"- source: {source}",
        f"- trajectory: red",
        f"- confidence: 0.5",
    ]
    if depends_on:
        block_lines.append("- depends_on:")
        for d in depends_on:
            block_lines.append(f"    - {d.strip()}")
    else:
        block_lines.append("- depends_on: []")
    block_lines.append(f"- last_human_update: {today}")
    block_lines.append('- last_human_note: ""')

    new_lines = _splice_block(lines, insert_at, block_lines)
    new_text = "\n".join(new_lines) + "\n"
    path.write_text(new_text)
    return new_id


def update_kr_title(path: Path, obj_id: str, kr_id: str, title: str) -> None:
    text = path.read_text()
    pattern = re.compile(rf"^### {re.escape(kr_id)}:.*$", re.MULTILINE)
    new_text, n = pattern.subn(f"### {kr_id}: {title.strip()}", text, count=1)
    if n == 0:
        raise ValueError(f"KR {kr_id} not found in {path}")
    path.write_text(new_text)


def update_kr_metadata(
    path: Path,
    obj_id: str,
    kr_id: str,
    *,
    title: Optional[str] = None,
    baseline: Optional[str] = None,
    target: Optional[str] = None,
    direction: Optional[str] = None,
    source: Optional[str] = None,
) -> None:
    if title is not None:
        update_kr_title(path, obj_id, kr_id, title)

    text = path.read_text()
    trailing_newline = text.endswith("\n")
    lines = text.split("\n")
    if trailing_newline and lines and lines[-1] == "":
        lines = lines[:-1]

    bounds = find_kr_bounds(lines, obj_id, kr_id)
    if bounds is None:
        raise ValueError(f"KR {obj_id}.{kr_id} not found")
    kr_start, kr_end = bounds
    kr_lines = lines[kr_start:kr_end]

    if baseline is not None:
        kr_lines = replace_field(kr_lines, "baseline", [f"- baseline: {baseline}"])
    if target is not None:
        kr_lines = replace_field(kr_lines, "target", [f"- target: {target}"])
    if direction is not None:
        kr_lines = replace_field(kr_lines, "direction", [f"- direction: {direction}"])
    if source is not None:
        kr_lines = replace_field(kr_lines, "source", [f"- source: {source}"])

    new_lines = lines[:kr_start] + kr_lines + lines[kr_end:]
    new_text = "\n".join(new_lines)
    if trailing_newline:
        new_text += "\n"
    path.write_text(new_text)


def find_checkin_human_section(text: str) -> Optional[tuple[int, int]]:
    """Char bounds [start, end) of the `## For human input` section through end of file/next ##."""
    m = re.search(r"(?m)^## For human input\s*$", text)
    if not m:
        return None
    start = m.start()
    after = text[m.end():]
    nxt = re.search(r"(?m)^## ", after)
    end = m.end() + nxt.start() if nxt else len(text)
    return (start, end)


PLACEHOLDER_RE = re.compile(r"^_\(?to be filled in\)?_$", re.IGNORECASE)


def parse_checkin_human_section(text: str) -> dict:
    """Return shape:
        {present, is_draft, format, questions: [{num, question, answer}], start, end}
    """
    bounds = find_checkin_human_section(text)
    if bounds is None:
        return {"present": False}
    start, end = bounds
    body = text[start:end].split("\n", 1)[1] if "\n" in text[start:end] else ""

    # Canonical: ### N. Question \n answer
    canonical: list[dict] = []
    for qm in re.finditer(
        r"(?ms)^###\s+(\d+)\.\s+(.+?)\n(.*?)(?=\n###\s+\d+\.|\n##\s|\Z)",
        body,
    ):
        num = qm.group(1)
        q = qm.group(2).strip()
        ans_raw = qm.group(3).strip()
        # Strip leading italic intro lines from the answer body
        ans_lines = [ln for ln in ans_raw.split("\n") if not PLACEHOLDER_RE.match(ln.strip())]
        ans = "\n".join(ans_lines).strip()
        canonical.append({"num": num, "question": q, "answer": ans})

    if canonical:
        return {
            "present": True,
            "is_draft": any(not q["answer"] for q in canonical),
            "format": "canonical",
            "questions": canonical,
            "start": start,
            "end": end,
        }

    # Fallback: numbered list (the legacy draft template)
    numbered = re.findall(r"(?m)^(\d+)\.\s+(.+)$", body)
    if numbered:
        return {
            "present": True,
            "is_draft": True,
            "format": "list",
            "questions": [{"num": n, "question": q.strip(), "answer": ""} for n, q in numbered],
            "start": start,
            "end": end,
        }

    body_stripped = re.sub(r"(?m)^_.*?_\s*$", "", body).strip()
    return {
        "present": True,
        "is_draft": len(body_stripped) < 30,
        "format": "freeform",
        "questions": [],
        "start": start,
        "end": end,
    }


def update_checkin_human_section(
    path: Path,
    questions: list[dict],
    author: str,
    today: str,
) -> None:
    """Replace the `## For human input` section with canonical format.

    `questions` is a list of dicts with keys: num (str), question (str), answer (str).
    """
    text = Path(path).read_text()
    bounds = find_checkin_human_section(text)
    if bounds is None:
        return
    start, end = bounds

    answers_clean = [(q["num"], q["question"], (q.get("answer") or "").strip()) for q in questions]
    all_filled = all(a for _, _, a in answers_clean)
    any_filled = any(a for _, _, a in answers_clean)

    if all_filled:
        intro = f"_Filled by {author} on {today}. This check-in is complete._"
    elif any_filled:
        intro = f"_Partially filled by {author} on {today}. Open questions remain — this is still a draft._"
    else:
        intro = f"_Leave blank for {author} to fill in. This check-in is a draft until every question below has an answer._"

    parts: list[str] = ["## For human input", "", intro, ""]
    for num, question, ans in answers_clean:
        parts.append(f"### {num}. {question}")
        parts.append("")
        parts.append(ans if ans else "_(to be filled in)_")
        parts.append("")

    new_section = "\n".join(parts).rstrip() + "\n"

    # Trim trailing whitespace from pre-section text, then insert
    head = text[:start].rstrip("\n") + "\n\n"
    tail = text[end:].lstrip("\n")
    new_text = head + new_section + (("\n" + tail) if tail else "")
    if not new_text.endswith("\n"):
        new_text += "\n"
    Path(path).write_text(new_text)


def add_mermaid_click_handlers(mermaid: str) -> str:
    """Make `team_O1_KR1` nodes clickable to /team/<team>#O1-KR1 in the UI."""
    nodes = set(re.findall(r"^\s*([a-zA-Z][\w]*_O\d+_KR\d+)\[", mermaid, re.MULTILINE))
    if not nodes:
        return mermaid
    lines = [mermaid.rstrip()]
    for node in sorted(nodes):
        m = re.match(r"(.+?)_(O\d+)_(KR\d+)$", node)
        if not m:
            continue
        team_raw = m.group(1).replace("_", "-")
        url = f"/team/{team_raw}#{m.group(2)}-{m.group(3)}"
        lines.append(f'    click {node} "{url}"')
    return "\n".join(lines) + "\n"
