#!/usr/bin/env python3
# autopilot-stamp · version: 0.1.0 · created: 2026-06-24 · updated: 2026-06-24
"""autopilot stamp.py — date+version stamping for RUNTIME-GENERATED artifacts.

The long-term plan and the docs each run produces (daily-run, time/estimate, playbook,
comparison, summary) are continuously regenerated over the timer's long lifecycle, so each
must carry a machine/front-end-readable stamp AND (for point-in-time artifacts) a date in its
filename. This is the deterministic helper the per-run agent calls so back-filling missing
stamps and bumping versions never depends on the agent's memory. See docs/autopilot/README.md.

Stamp = YAML frontmatter keys (other frontmatter keys are preserved, order kept):
    ---
    autopilot_doc: plan        # plan|daily-run|time|playbook|comparison|summary
    version: 0.3.0             # new=0.1.0; locked plan=1.0.0; PATCH small / MINOR structural / MAJOR rewrite
    created: 2026-06-24        # set once (back-filled from filename date, then mtime, then --date)
    updated: 2026-06-24        # = run date on every modification
    ---

Commands:
    check <path>...                         list .md artifacts missing a stamp OR a date-in-filename; exit 1 if any
    apply <file> --type T [--date D] [--bump patch|minor|major]   ensure/refresh the stamp on one file
    newname <type> [--date D] [--time HHMM] print the conventional dated filename stem (no extension)

--date defaults to today (override for tests / back-dating). Dependency-free (no PyYAML).
"""
from __future__ import annotations

import datetime
import os
import re
import sys

MANAGED = ("autopilot_doc", "version", "created", "updated")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _today() -> str:
    return datetime.date.today().isoformat()


def _split_fm(text: str):
    """Return (fm_lines|None, body). fm_lines excludes the --- fences."""
    lines = text.split("\n")
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 60)):
            if lines[i].strip() == "---":
                return lines[1:i], "\n".join(lines[i + 1:])
    return None, text


def _get(fm_lines, key):
    for ln in fm_lines or []:
        m = re.match(rf"\s*{re.escape(key)}\s*:\s*(.*?)\s*$", ln)
        if m:
            return m.group(1)
    return None


def _bump(version: str, level: str) -> str:
    try:
        major, minor, patch = (int(x) for x in version.split("."))
    except Exception:
        return "0.1.0"
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _filename_date(path: str):
    m = DATE_RE.search(os.path.basename(path))
    return m.group(1) if m else None


def _newname(doc_type: str, date: str, hhmm: str | None = None) -> str:
    """Conventional filename stem. daily-run is inherently date-named; others prefix the type."""
    suffix = f"_{hhmm}" if hhmm else ""
    return f"{date}{suffix}" if doc_type == "daily-run" else f"{doc_type}-{date}{suffix}"


def has_stamp(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        fm, _ = _split_fm(f.read())
    return fm is not None and _get(fm, "version") is not None and _get(fm, "created") is not None


# rolling docs keep a stable name on purpose; they need a stamp but NOT a date in the filename
_ROLLING = ("plan.md", "playbook.md", "playbook.jsonl", "changelog.md", "README.md", "index.md")


def needs_filename_date(path: str) -> bool:
    base = os.path.basename(path)
    if base in _ROLLING:
        return False
    return _filename_date(path) is None


def apply(path: str, doc_type: str | None, date: str, bump: str | None) -> None:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fm_lines, body = _split_fm(text)
    existing = fm_lines if fm_lines is not None else []

    created = _get(existing, "created") or _filename_date(path)
    if not created:
        try:
            created = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
        except OSError:
            created = date
    cur_ver = _get(existing, "version")
    version = _bump(cur_ver, bump) if (cur_ver and bump) else (cur_ver or "0.1.0")
    doc = doc_type or _get(existing, "autopilot_doc") or "doc"
    values = {"autopilot_doc": doc, "version": version, "created": created, "updated": date}

    out, seen = [], set()
    for ln in existing:
        m = re.match(r"\s*([A-Za-z0-9_]+)\s*:", ln)
        key = m.group(1) if m else None
        if key in MANAGED:
            out.append(f"{key}: {values[key]}")
            seen.add(key)
        else:
            out.append(ln)
    for key in MANAGED:
        if key not in seen:
            out.append(f"{key}: {values[key]}")

    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n" + "\n".join(out) + "\n---\n" + body)


def _md_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _, files in os.walk(p):
                for fn in files:
                    if fn.endswith(".md"):
                        yield os.path.join(root, fn)
        elif p.endswith(".md") and os.path.isfile(p):
            yield p


def main(argv) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]

    if cmd == "check":
        flagged = []
        for fp in _md_files(argv[2:]):
            why = []
            if not has_stamp(fp):
                why.append("no-stamp")
            if needs_filename_date(fp):
                why.append("no-date-in-name")
            if why:
                flagged.append((fp, ",".join(why)))
        for fp, why in flagged:
            print(f"{why}\t{fp}")
        return 1 if flagged else 0

    if cmd == "apply":
        if len(argv) < 3:
            print("usage: stamp.py apply <file> --type T [--date D] [--bump LEVEL]", file=sys.stderr)
            return 2
        path = argv[2]
        rest = argv[3:]
        doc_type = _opt(rest, "--type")
        date = _opt(rest, "--date") or _today()
        bump = _opt(rest, "--bump")
        if bump and bump not in ("patch", "minor", "major"):
            print("--bump must be patch|minor|major", file=sys.stderr)
            return 2
        apply(path, doc_type, date, bump)
        print(f"stamped {path}")
        return 0

    if cmd == "newname":
        if len(argv) < 3:
            print("usage: stamp.py newname <type> [--date D] [--time HHMM]", file=sys.stderr)
            return 2
        doc_type = argv[2]
        date = _opt(argv[3:], "--date") or _today()
        hhmm = _opt(argv[3:], "--time")
        print(_newname(doc_type, date, hhmm))
        return 0

    print(__doc__)
    return 2


def _opt(rest, flag):
    if flag in rest:
        i = rest.index(flag)
        if i + 1 < len(rest):
            return rest[i + 1]
    return None


if __name__ == "__main__":
    sys.exit(main(sys.argv))
