#!/usr/bin/env python3
# prompt-library · version: 0.1.0
"""Curate reusable prompts, de-privacy-gated (overhaul task 9).

Stores reusable prompts (with scenario tags + provenance) as plain Markdown so a human can browse them and
an agent can grep them. A PRIVACY GATE blocks `add` if the prompt still contains obvious private content
(absolute home/media/mnt paths, emails, token-shaped strings, the configured username, or project codenames)
— you must de-privacy first (see the privacy-redact skill). The gate is a heuristic, not a guarantee.

    plib.py add --root R --title "…" --scenarios a,b --source claude-code [--tags t1,t2]  (body on stdin)
    plib.py index --root R
    plib.py find  --root R --query "terms"
    plib.py scan  < text          # just run the privacy gate on stdin; exit 1 if matches

Default --root: recommendations/prompt-library. Dependency-free.
"""
import argparse
import os
import re
import sys

# Generic, non-personal privacy patterns (safe to ship). User-SPECIFIC private terms — your username, your
# project codenames — are deliberately NOT hardcoded here (that would publish them, and this repo's own CI
# privacy scan bans codename literals in content modules). Load those from a LOCAL, un-published file instead:
# env PLIB_PRIVATE_TERMS=<path>, else ~/.config/agent-harness/private-terms.txt (one term per line, # comments).
PRIVACY_PATTERNS = [
    (r"/home/[A-Za-z0-9._-]+", "absolute home path"),
    (r"/media/[A-Za-z0-9._-]+", "absolute media path"),
    (r"/mnt/[0-9a-fA-F-]{8,}", "absolute mnt uuid path"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
    (r"\b(sk-[A-Za-z0-9]{6,}|ghp_[A-Za-z0-9]{6,}|gho_[A-Za-z0-9]{6,}|github_pat_[A-Za-z0-9_]{6,})", "token-shaped string"),
]


def _extra_terms():
    src = os.environ.get("PLIB_PRIVATE_TERMS") or os.path.expanduser("~/.config/agent-harness/private-terms.txt")
    if not os.path.isfile(src):
        return []
    with open(src, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.lstrip().startswith("#")]


def privacy_scan(text, extra=None):
    """Return a list of (label, matched_snippet) for anything that looks private.
    `extra` (default: the local private-terms file) is a list of user-specific literal terms to also flag."""
    hits = []
    for pat, label in PRIVACY_PATTERNS:
        for m in re.finditer(pat, text):
            hits.append((label, m.group(0)))
    low = text.lower()
    for term in (extra if extra is not None else _extra_terms()):
        if term.lower() in low:
            hits.append(("private term", term))
    return hits


def _slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s.lower())).strip("-") or "prompt"


def _prompts_dir(root):
    return os.path.join(root, "prompts")


def _read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def _entries(root):
    d = _prompts_dir(root)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".md"))


def _fm(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, m.group(2)


def cmd_scan(args):
    hits = privacy_scan(sys.stdin.read())
    for label, snip in hits:
        print(f"{label}: {snip}", file=sys.stderr)
    return 1 if hits else 0


def cmd_add(args):
    body = sys.stdin.read()
    hits = privacy_scan(body + "\n" + args.title)
    if hits:
        print("REFUSED: prompt still contains private content — de-privacy first (see privacy-redact):", file=sys.stderr)
        for label, snip in hits:
            print(f"  - {label}: {snip}", file=sys.stderr)
        return 1
    os.makedirs(_prompts_dir(args.root), exist_ok=True)
    slug = _slug(args.title)
    path = os.path.join(_prompts_dir(args.root), f"{slug}.md")
    fm = (
        "---\n"
        f"title: {args.title}\n"
        f"scenarios: {args.scenarios}\n"
        f"source: {args.source}\n"
        f"tags: {args.tags}\n"
        "---\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + body.rstrip("\n") + "\n")
    cmd_index(args)
    print(path)
    return 0


def cmd_index(args):
    os.makedirs(args.root, exist_ok=True)
    rows = []
    for p in _entries(args.root):
        fm, _ = _fm(_read(p))
        rows.append((fm, os.path.relpath(p, args.root)))
    out = ["# Prompt library", "", f"{len(rows)} reusable prompt(s). Browse by scenario; grep the files for details.", ""]
    if rows:
        out += ["| title | scenarios | source | file |", "|---|---|---|---|"]
        for fm, rel in rows:
            cell = lambda v: str(v).replace("|", "\\|")  # noqa: E731
            out.append(f"| {cell(fm.get('title',''))} | {cell(fm.get('scenarios',''))} | {cell(fm.get('source',''))} | `{rel}` |")
    with open(os.path.join(args.root, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    return 0


def cmd_find(args):
    terms = [t.lower() for t in (args.query or "").split() if t]
    scored = []
    for p in _entries(args.root):
        text = _read(p).lower()
        score = sum(text.count(t) for t in terms) if terms else 0
        if score > 0 or not terms:
            scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    for score, p in scored[: args.top]:
        print(f"{score}\t{p}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="plib.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")  # noqa: F841  (reads stdin only)
    for name in ("add", "index", "find"):
        p = sub.add_parser(name)
        p.add_argument("--root", default="recommendations/prompt-library")
        if name == "add":
            p.add_argument("--title", required=True)
            p.add_argument("--scenarios", default="")
            p.add_argument("--source", default="")
            p.add_argument("--tags", default="")
        if name == "find":
            p.add_argument("--query", default="")
            p.add_argument("--top", type=int, default=10)
    args = ap.parse_args(argv)
    return {"scan": cmd_scan, "add": cmd_add, "index": cmd_index, "find": cmd_find}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
