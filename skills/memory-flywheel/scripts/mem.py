#!/usr/bin/env python3
# memory-flywheel · version: 0.1.0
"""Deterministic core of the agent memory flywheel (WS-B, tasks 3/4/5).

The LLM is a COMPONENT, not the core: recording, indexing, and keyword recall are pure, deterministic
code (grep-friendly plain files) — the model only writes the round *content* and reads what recall returns.

Storage layout (per project, under --root, default `.agent-memory/`):

    <root>/<project>/
        rounds/NNNN-<kind>.md    one file per recorded round: YAML-ish frontmatter + VERBATIM body
        INDEX.md                 coarse progressive-disclosure layer: a table of all rounds (id/kind/title/keywords)

Progressive disclosure: read INDEX.md first (cheap, coarse); open only the round files recall points at.
Recall is keyword-grep over frontmatter + body, ranked by match count — works with native grep too.

CLI:
    mem.py record --project P --kind K --title T [--keywords a,b] [--ts YYYY-MM-DD] [--root R]   (body on stdin)
    mem.py index  --project P [--root R]
    mem.py recall --project P --query "term term" [--root R] [--top N]

Dependency-free. `--ts` is injectable for deterministic tests; it defaults to today.
"""
import argparse
import datetime
import json
import os
import re
import sys

FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


def _root(args):
    return args.root or os.environ.get("AGENT_MEMORY_ROOT") or ".agent-memory"


def _proj_dir(args):
    return os.path.join(_root(args), args.project)


def _rounds_dir(args):
    return os.path.join(_proj_dir(args), "rounds")


def _parse_kw(s):
    return [k.strip() for k in (s or "").split(",") if k.strip()]


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _split_fm(text):
    """Return (frontmatter_dict, body). Minimal parser: `key: value`, keywords as [a, b]."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm, body = {}, m.group(2)
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "keywords":
            v = _parse_kw(v.strip("[]"))
        fm[k] = v
    return fm, body


def _next_id(args):
    rd = _rounds_dir(args)
    if not os.path.isdir(rd):
        return 1
    ids = [int(m.group(1)) for f in os.listdir(rd) if (m := re.match(r"^(\d+)-", f))]
    return (max(ids) + 1) if ids else 1


def _round_files(args):
    rd = _rounds_dir(args)
    if not os.path.isdir(rd):
        return []
    return sorted(os.path.join(rd, f) for f in os.listdir(rd) if f.endswith(".md"))


def cmd_record(args):
    body = sys.stdin.read()
    ts = args.ts or datetime.date.today().isoformat()
    rid = _next_id(args)
    kind = re.sub(r"[^a-z0-9-]", "-", args.kind.lower())
    os.makedirs(_rounds_dir(args), exist_ok=True)
    kws = _parse_kw(args.keywords)
    fm = (
        "---\n"
        f"id: {rid:04d}\n"
        f"kind: {kind}\n"
        f"title: {args.title}\n"
        f"ts: {ts}\n"
        f"keywords: [{', '.join(kws)}]\n"
        "---\n"
    )
    path = os.path.join(_rounds_dir(args), f"{rid:04d}-{kind}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    cmd_index(args)  # keep the coarse layer current
    print(path)
    return 0


def _cell(v):
    """Make a value safe inside a Markdown table cell: escape pipes, flatten newlines."""
    return str(v).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def cmd_index(args):
    os.makedirs(_proj_dir(args), exist_ok=True)
    rows = []
    for p in _round_files(args):
        fm, _ = _split_fm(_read(p))
        rows.append(fm)
    out = [f"# Memory index — {args.project}", "", f"{len(rows)} round(s). Read this coarse layer first; open only the round files recall points at.", ""]
    if rows:
        out += ["| id | kind | title | keywords |", "|---|---|---|---|"]
        for r in rows:
            kw = ", ".join(r.get("keywords", [])) if isinstance(r.get("keywords"), list) else (r.get("keywords") or "")
            out.append(f"| {_cell(r.get('id',''))} | {_cell(r.get('kind',''))} | {_cell(r.get('title',''))} | {_cell(kw)} |")
    idx = os.path.join(_proj_dir(args), "INDEX.md")
    with open(idx, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return 0


def _graph_path(args):
    return os.path.join(_proj_dir(args), "graph.json")


def _load_graph(args):
    p = _graph_path(args)
    if os.path.isfile(p):
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (ValueError, OSError):
            return {}
    return {}


def _path_id(path):
    m = re.match(r"(\d+)-", os.path.basename(path))
    return m.group(1) if m else None


def cmd_link(args):
    """Record a directed edge round A -> round B in graph.json (ids normalized to 4 digits)."""
    a = f"{int(args.from_id):04d}"
    b = f"{int(args.to_id):04d}"
    g = _load_graph(args)
    g.setdefault(a, [])
    if b not in g[a]:
        g[a].append(b)
    os.makedirs(_proj_dir(args), exist_ok=True)
    with open(_graph_path(args), "w", encoding="utf-8") as f:
        json.dump(g, f, indent=2, sort_keys=True)
    print(f"{a} -> {b}")
    return 0


def _tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _fuzzy_hits(term, tokens):
    """Count tokens SIMILAR to (but not identical to) term — catches variant forms (memory↔memories,
    design↔designs) that exact substring match misses. Deterministic: substring-either-way or a shared
    4-char prefix, both terms >=4 chars. Exact matches are skipped (already counted by the exact scorer)."""
    if len(term) < 4:
        return 0
    n = 0
    for tok in tokens:
        if tok == term or len(tok) < 4:
            continue
        if term in tok or tok in term or term[:4] == tok[:4]:
            n += 1
    return n


def cmd_recall(args):
    terms = [t.lower() for t in (args.query or "").split() if t]
    fuzzy = getattr(args, "fuzzy", False)
    scored = []
    for p in _round_files(args):
        text = _read(p).lower()
        score = sum(text.count(t) for t in terms) if terms else 0
        if fuzzy and terms:
            toks = _tokens(text)
            score += sum(_fuzzy_hits(t, toks) for t in terms)
        if score > 0 or not terms:
            scored.append((score, p))
    # graph overlay: pull in rounds LINKED to a keyword hit (1 hop, undirected), with a small score, so
    # related context surfaces even when it shares no query keyword. Requires --graph and query terms.
    if getattr(args, "graph", False) and terms:
        g = _load_graph(args)
        adj = {}
        for a, bs in g.items():
            for b in bs:
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
        id2path = {}
        for p in _round_files(args):
            i = _path_id(p)
            if i:
                id2path[i] = p
        already = {p for _, p in scored}
        hit_ids = [_path_id(p) for s, p in scored if s > 0]
        for hid in hit_ids:
            for nb in adj.get(hid, ()):
                np = id2path.get(nb)
                if np and np not in already:
                    scored.append((1, np))  # linked-in (no direct keyword match)
                    already.add(np)
    scored.sort(key=lambda x: (-x[0], x[1]))
    for score, p in scored[: args.top]:
        print(f"{score}\t{p}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mem.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("record", "index", "recall", "link"):
        s = sub.add_parser(name)
        s.add_argument("--project", required=True)
        s.add_argument("--root", default=None)
        if name == "record":
            s.add_argument("--kind", required=True)
            s.add_argument("--title", required=True)
            s.add_argument("--keywords", default="")
            s.add_argument("--ts", default=None)
        if name == "recall":
            s.add_argument("--query", default="")
            s.add_argument("--top", type=int, default=10)
            s.add_argument("--fuzzy", action="store_true", help="also match similar keywords (variant forms) to boost recall")
            s.add_argument("--graph", action="store_true", help="also pull in rounds linked (1 hop) to a keyword hit")
        if name == "link":
            s.add_argument("--from", dest="from_id", required=True, help="source round id")
            s.add_argument("--to", dest="to_id", required=True, help="target round id")
    args = ap.parse_args(argv)
    return {"record": cmd_record, "index": cmd_index, "recall": cmd_recall, "link": cmd_link}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
