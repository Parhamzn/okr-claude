"""Thin Flask UI over the markdown OKR files.

Read-mostly. The only writes are to human-owned fields (confidence,
last_human_note, last_human_update), exactly the scope CLAUDE.md
defines for human edits.

Run:
    pip install -r requirements.txt
    python app.py
    open http://localhost:5050
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from parser import (
    add_kr,
    add_mermaid_click_handlers,
    add_objective,
    create_team_file,
    discover_team_files,
    extract_mermaid,
    linear_pace_target,
    parse_checkin_human_section,
    parse_team_file,
    update_checkin_human_section,
    update_kr_human_fields,
    update_kr_metadata,
)

DATA_DIR = Path(os.environ.get("OKR_DATA_DIR") or Path(__file__).resolve().parent.parent).resolve()
SHA_RE = re.compile(r"^[0-9a-f]{4,64}$")

# Optional HTTP Basic Auth. Both env vars must be set to enable.
# Leave them unset for local development.
AUTH_USER = os.environ.get("OKR_UI_USER")
AUTH_PASSWORD = os.environ.get("OKR_UI_PASSWORD")

app = Flask(__name__)
app.secret_key = os.environ.get("OKR_UI_SECRET", "okr-ui-demo")


@app.before_request
def _require_basic_auth():
    if not AUTH_USER or not AUTH_PASSWORD:
        return None
    auth = request.authorization
    if auth and auth.username == AUTH_USER and auth.password == AUTH_PASSWORD:
        return None
    return (
        "Authentication required.",
        401,
        {"WWW-Authenticate": 'Basic realm="OKRs"'},
    )


def git_root() -> Path | None:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=DATA_DIR, capture_output=True, text=True, check=True,
        )
        return Path(r.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def okr_paths_for_git() -> list[str]:
    """Paths to scope git log to, relative to repo root."""
    root = git_root()
    if root is None:
        return []
    paths: list[str] = []
    for p in sorted(DATA_DIR.glob("*.md")):
        try:
            paths.append(str(p.relative_to(root)))
        except ValueError:
            continue
    checkins = DATA_DIR / "checkins"
    if checkins.exists():
        try:
            paths.append(str(checkins.relative_to(root)))
        except ValueError:
            pass
    return paths


def git_log(limit: int = 100, paths: list[str] | None = None) -> list[dict] | None:
    """Return commit list touching `paths` (or all OKR files), newest first."""
    root = git_root()
    if root is None:
        return None
    if paths is None:
        paths = okr_paths_for_git()
    if not paths:
        return []
    sep = "\x1f"
    args = [
        "git", "log",
        f"--pretty=format:%H{sep}%h{sep}%an{sep}%ae{sep}%aI{sep}%s",
        f"-n{limit}", "--name-only", "--",
    ] + paths
    try:
        r = subprocess.run(args, cwd=root, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []

    commits: list[dict] = []
    current: dict | None = None
    for raw in r.stdout.splitlines():
        if sep in raw:
            if current is not None:
                commits.append(current)
            sha, short, an, ae, aiso, msg = raw.split(sep, 5)
            current = {
                "sha": sha, "short": short, "author": an, "email": ae,
                "date": aiso, "message": msg, "files": [],
            }
        elif raw.strip() and current is not None:
            current["files"].append(raw.strip())
    if current is not None:
        commits.append(current)
    return commits


def git_show(sha: str) -> str | None:
    if not SHA_RE.match(sha):
        return None
    root = git_root()
    if root is None:
        return None
    paths = okr_paths_for_git()
    args = ["git", "show", "--no-color", "--stat", "-p", sha, "--"] + paths
    try:
        r = subprocess.run(args, cwd=root, capture_output=True, text=True, check=True)
        return r.stdout
    except subprocess.CalledProcessError:
        return None


def git_commit_meta(sha: str) -> dict | None:
    if not SHA_RE.match(sha):
        return None
    root = git_root()
    if root is None:
        return None
    sep = "\x1f"
    try:
        r = subprocess.run(
            ["git", "show", "-s", f"--pretty=format:%H{sep}%h{sep}%an{sep}%ae{sep}%aI{sep}%s{sep}%b", sha],
            cwd=root, capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        return None
    parts = r.stdout.split(sep, 6)
    if len(parts) < 6:
        return None
    return {
        "sha": parts[0], "short": parts[1], "author": parts[2],
        "email": parts[3], "date": parts[4], "subject": parts[5],
        "body": parts[6] if len(parts) > 6 else "",
    }


def humanize_date(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = now - dt
    s = int(delta.total_seconds())
    if s < 60: return "just now"
    if s < 3600: return f"{s // 60} min ago"
    if s < 86400: return f"{s // 3600} hr ago"
    if s < 86400 * 14: return f"{s // 86400} days ago"
    return dt.strftime("%Y-%m-%d")


def classify_diff_lines(diff: str) -> list[dict]:
    lines: list[dict] = []
    for raw in diff.splitlines():
        if raw.startswith("diff "):
            cls = "file"
        elif raw.startswith("+++") or raw.startswith("---"):
            cls = "header"
        elif raw.startswith("@@"):
            cls = "hunk"
        elif raw.startswith("+"):
            cls = "add"
        elif raw.startswith("-"):
            cls = "del"
        elif raw.startswith("index ") or raw.startswith("new file") or raw.startswith("deleted file") or raw.startswith("Binary "):
            cls = "meta"
        else:
            cls = "ctx"
        lines.append({"cls": cls, "text": raw})
    return lines


app.jinja_env.filters["humandate"] = humanize_date


def find_graph_file() -> Path | None:
    for name in ("dependency-graph.md", "dependency-graph2.md"):
        p = DATA_DIR / name
        if p.exists() and "```mermaid" in p.read_text():
            return p
    return None


def quarter_progress(quarter: str | None) -> tuple[int, int]:
    if not quarter:
        return (0, 13)
    m = re.match(r"(\d{4})-Q(\d)", quarter)
    if not m:
        return (0, 13)
    year, q = int(m.group(1)), int(m.group(2))
    q_start_month = {1: 1, 2: 4, 3: 7, 4: 10}[q]
    start = date(year, q_start_month, 1)
    today = date.today()
    days = (today - start).days
    return (max(0, min(13, days // 7)), 13)


def load_all_teams() -> dict:
    files = discover_team_files(DATA_DIR)
    return {team: parse_team_file(path) for team, path in files.items()}


def kr_display(kr: dict, weeks_elapsed: int) -> dict:
    info = {"percent": None, "pace_target": None, "on_pace": None}
    baseline, target, current = kr.get("baseline"), kr.get("target"), kr.get("current")
    direction = kr.get("direction", "up")
    try:
        b, t, c = float(baseline), float(target), float(current)
    except (TypeError, ValueError):
        return info
    if t == b:
        info["percent"] = 100 if c >= t else 0
    else:
        progress = (c - b) / (t - b)
        info["percent"] = max(0, min(100, round(progress * 100)))
    pace = linear_pace_target(b, t, weeks_elapsed)
    info["pace_target"] = round(pace, 2) if abs(pace) >= 1 else round(pace, 3)
    info["on_pace"] = (c <= pace) if direction == "down" else (c >= pace)
    return info


def summary_counts(teams: dict) -> dict:
    counts = {"green": 0, "yellow": 0, "red": 0, "unknown": 0, "total": 0}
    for team_data in teams.values():
        for obj in team_data["objectives"]:
            for kr in obj["krs"]:
                counts["total"] += 1
                counts[kr.get("trajectory") or "unknown"] = counts.get(kr.get("trajectory") or "unknown", 0) + 1
    return counts


def build_inbound_outbound(teams: dict) -> tuple[dict, dict]:
    """For each canonical KR id, who depends on it (inbound) and what does it depend on (outbound)."""
    inbound: dict[str, list[dict]] = {}
    outbound: dict[str, list[dict]] = {}
    for team_name, td in teams.items():
        for obj in td["objectives"]:
            for kr in obj["krs"]:
                cid = kr["canonical_id"]
                for dep in (kr.get("depends_on") or []):
                    outbound.setdefault(cid, []).append({"id": dep})
                    inbound.setdefault(dep, []).append({"id": cid})
    return inbound, outbound


def kr_lookup(teams: dict) -> dict:
    """canonical_id -> minimal info, for cross-team dep display."""
    out = {}
    for td in teams.values():
        for obj in td["objectives"]:
            for kr in obj["krs"]:
                out[kr["canonical_id"]] = {
                    "title": kr["title"],
                    "trajectory": kr.get("trajectory"),
                    "team": td["frontmatter"].get("team"),
                    "obj_id": obj["id"],
                    "kr_id": kr["id"],
                }
    return out


@app.route("/")
def dashboard():
    teams = load_all_teams()
    counts = summary_counts(teams)
    return render_template("dashboard.html", teams=teams, counts=counts)


@app.route("/team/<team>")
def team_page(team):
    teams = load_all_teams()
    if team not in teams:
        abort(404)
    td = teams[team]
    weeks_elapsed, total_weeks = quarter_progress(td["frontmatter"].get("quarter"))
    inbound, outbound = build_inbound_outbound(teams)
    lookup = kr_lookup(teams)
    for obj in td["objectives"]:
        for kr in obj["krs"]:
            kr["_display"] = kr_display(kr, weeks_elapsed)
            kr["_outbound"] = [
                {**d, "info": lookup.get(d["id"])} for d in outbound.get(kr["canonical_id"], [])
            ]
            kr["_inbound"] = [
                {**d, "info": lookup.get(d["id"])} for d in inbound.get(kr["canonical_id"], [])
            ]
    return render_template(
        "team.html",
        team=team,
        team_data=td,
        weeks_elapsed=weeks_elapsed,
        total_weeks=total_weeks,
    )


@app.route("/team/<team>/<obj_id>/<kr_id>/edit", methods=["POST"])
def edit_kr(team, obj_id, kr_id):
    teams = load_all_teams()
    if team not in teams:
        abort(404)
    path = Path(teams[team]["path"])

    note = request.form.get("note", "")
    risks = request.form.get("unwritten_risks", "")
    confidence_raw = request.form.get("confidence", "").strip()
    confidence_value: float | None = None
    if confidence_raw:
        try:
            confidence_value = max(0.0, min(1.0, float(confidence_raw)))
        except ValueError:
            pass

    update_kr_human_fields(
        path,
        obj_id,
        kr_id,
        note=note,
        confidence=confidence_value,
        update_date=date.today().isoformat(),
        unwritten_risks=risks,
    )
    flash(f"Saved {team}:{obj_id}.{kr_id}")
    return redirect(url_for("team_page", team=team) + f"#{obj_id}-{kr_id}")


@app.route("/graph")
def graph_page():
    path = find_graph_file()
    mermaid = None
    if path is not None:
        raw = extract_mermaid(path)
        if raw is not None:
            mermaid = add_mermaid_click_handlers(raw)
    return render_template("graph.html", mermaid=mermaid, graph_path=str(path) if path else None)


@app.route("/checkins")
def checkins_page():
    files: list[Path] = list(DATA_DIR.glob("week-*.md"))
    checkins_dir = DATA_DIR / "checkins"
    if checkins_dir.exists():
        files.extend(checkins_dir.rglob("*.md"))
    files = sorted(set(files))

    items = []
    for path in files:
        text = path.read_text()
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        section = parse_checkin_human_section(text)
        n_total = len(section.get("questions") or [])
        n_filled = sum(1 for q in (section.get("questions") or []) if q.get("answer"))
        items.append({
            "name": path.name,
            "title": m.group(1) if m else path.stem,
            "rel": str(path.relative_to(DATA_DIR)),
            "is_draft": bool(section.get("is_draft")) if section.get("present") else None,
            "n_total": n_total,
            "n_filled": n_filled,
        })
    return render_template("checkins.html", checkins=items)


def _resolve_checkin_path(rel: str) -> Path | None:
    if ".." in rel.split("/"):
        return None
    path = DATA_DIR / rel
    if not path.exists() or path.suffix != ".md":
        return None
    return path


@app.route("/checkin/<path:rel>")
def checkin_page(rel):
    path = _resolve_checkin_path(rel)
    if path is None:
        abort(404)
    text = path.read_text()
    section = parse_checkin_human_section(text)
    return render_template(
        "checkin.html",
        text=text,
        title=path.name,
        rel=rel,
        section=section,
    )


@app.route("/checkin/<path:rel>/edit", methods=["POST"])
def edit_checkin(rel):
    path = _resolve_checkin_path(rel)
    if path is None:
        abort(404)
    text = path.read_text()
    section = parse_checkin_human_section(text)
    if not section.get("present") or not section.get("questions"):
        flash("This check-in has no structured human-input section to edit.")
        return redirect(url_for("checkin_page", rel=rel))

    questions = []
    for q in section["questions"]:
        answer = request.form.get(f"q{q['num']}", "").strip()
        questions.append({"num": q["num"], "question": q["question"], "answer": answer})

    author = request.form.get("author", "").strip() or "team owner"
    update_checkin_human_section(path, questions, author=author, today=date.today().isoformat())

    n_filled = sum(1 for q in questions if q["answer"])
    if n_filled == len(questions):
        flash(f"Check-in complete — all {n_filled} answers saved.")
    elif n_filled > 0:
        flash(f"Saved {n_filled}/{len(questions)} answers. Check-in is still a draft.")
    else:
        flash("Saved (no answers yet — still a draft).")
    return redirect(url_for("checkin_page", rel=rel))


TEAM_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,30}$")


@app.route("/team/new", methods=["GET", "POST"])
def new_team():
    if request.method == "GET":
        existing = list(discover_team_files(DATA_DIR).keys())
        return render_template("new_team.html", existing=existing)

    team = (request.form.get("team") or "").strip().lower()
    owner = (request.form.get("owner") or "").strip()
    quarter = (request.form.get("quarter") or "").strip()
    parent = (request.form.get("parent") or "company").strip()

    if not TEAM_NAME_RE.match(team):
        flash("Team name must be lowercase letters, digits, and dashes only (e.g. growth, data-ops).")
        return redirect(url_for("new_team"))
    if not owner or "@" not in owner:
        flash("Owner must be an email address.")
        return redirect(url_for("new_team"))
    if not re.match(r"^\d{4}-Q[1-4]$", quarter):
        flash("Quarter must look like 2026-Q3.")
        return redirect(url_for("new_team"))
    if team in discover_team_files(DATA_DIR):
        flash(f"Team '{team}' already has an OKR file.")
        return redirect(url_for("new_team"))

    path = DATA_DIR / f"{team}.md"
    if path.exists():
        flash(f"{path.name} already exists.")
        return redirect(url_for("new_team"))

    create_team_file(
        path, team=team, owner=owner, quarter=quarter, parent=parent,
        today=date.today().isoformat(),
    )
    flash(f"Created {team}.md. Now add objectives and KRs.")
    return redirect(url_for("team_page", team=team))


@app.route("/team/<team>/objective/new", methods=["POST"])
def new_objective(team):
    teams = load_all_teams()
    if team not in teams:
        abort(404)
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("Objective title required.")
        return redirect(url_for("team_page", team=team))
    new_id = add_objective(Path(teams[team]["path"]), title)
    flash(f"Added objective {new_id}.")
    return redirect(url_for("team_page", team=team) + f"#{new_id}")


@app.route("/team/<team>/<obj_id>/kr/new", methods=["POST"])
def new_kr(team, obj_id):
    teams = load_all_teams()
    if team not in teams:
        abort(404)
    title = (request.form.get("title") or "").strip()
    if not title:
        flash("KR title required.")
        return redirect(url_for("team_page", team=team))
    baseline = (request.form.get("baseline") or "0").strip()
    target = (request.form.get("target") or "1").strip()
    direction = (request.form.get("direction") or "up").strip()
    source = (request.form.get("source") or "manual").strip()
    deps_raw = (request.form.get("depends_on") or "").strip()
    depends_on = [d.strip() for d in re.split(r"[,\n]", deps_raw) if d.strip()] or None

    try:
        new_id = add_kr(
            Path(teams[team]["path"]),
            obj_id,
            title=title, baseline=baseline, target=target,
            direction=direction, source=source,
            depends_on=depends_on,
            today=date.today().isoformat(),
        )
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("team_page", team=team))
    flash(f"Added {obj_id}.{new_id}.")
    return redirect(url_for("team_page", team=team) + f"#{obj_id}-{new_id}")


@app.route("/team/<team>/<obj_id>/<kr_id>/edit-meta", methods=["POST"])
def edit_kr_meta(team, obj_id, kr_id):
    teams = load_all_teams()
    if team not in teams:
        abort(404)
    title = (request.form.get("title") or "").strip() or None
    baseline = (request.form.get("baseline") or "").strip() or None
    target = (request.form.get("target") or "").strip() or None
    direction = (request.form.get("direction") or "").strip() or None
    source = (request.form.get("source") or "").strip() or None
    try:
        update_kr_metadata(
            Path(teams[team]["path"]),
            obj_id, kr_id,
            title=title, baseline=baseline, target=target,
            direction=direction, source=source,
        )
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("team_page", team=team))
    flash(f"Updated metadata for {team}:{obj_id}.{kr_id}.")
    return redirect(url_for("team_page", team=team) + f"#{obj_id}-{kr_id}")


@app.route("/history")
def history_page():
    filter_team = request.args.get("team") or None
    filter_file = request.args.get("file") or None

    paths = None
    if filter_file:
        root = git_root()
        if root and (DATA_DIR / filter_file).exists():
            paths = [str((DATA_DIR / filter_file).relative_to(root))]

    commits = git_log(limit=100, paths=paths)

    if commits is not None and filter_team:
        teams_files = discover_team_files(DATA_DIR)
        team_path = teams_files.get(filter_team)
        if team_path:
            root = git_root()
            if root:
                rel = str(team_path.relative_to(root))
                commits = [c for c in commits if rel in c["files"]]

    teams = list(discover_team_files(DATA_DIR).keys())
    return render_template(
        "history.html",
        commits=commits,
        repo_root=str(git_root()) if git_root() else None,
        teams=teams,
        filter_team=filter_team,
        filter_file=filter_file,
    )


@app.route("/history/<sha>")
def commit_page(sha):
    if not SHA_RE.match(sha):
        abort(404)
    meta = git_commit_meta(sha)
    if meta is None:
        abort(404)
    diff = git_show(sha) or ""
    return render_template(
        "commit.html",
        meta=meta,
        diff_lines=classify_diff_lines(diff),
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050)
