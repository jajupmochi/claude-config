#!/usr/bin/env python3
# prompt-library · version: 0.2.0
"""Curate reusable prompts, de-privacy-gated (overhaul task 9).

Stores reusable prompts (with scenario tags + provenance) as plain Markdown so a human can browse them and
an agent can grep them. A PRIVACY GATE blocks `add` if the prompt still contains obvious private content
(absolute home/media/mnt paths, emails, token-shaped strings, the configured username, or project codenames)
— you must de-privacy first (see the privacy-redact skill). The gate is a heuristic, not a guarantee.

    plib.py add   --root R --title "…" --scenarios a,b --source claude-code [--tags t1,t2]
                  [--optimized TEXT|@file] [--when TEXT|@file] [--when-not TEXT|@file]
                  [--session ID] [--date YYYY-MM-DD]          (the ORIGINAL prompt on stdin)
    plib.py index --root R
    plib.py find  --root R --query "terms"
    plib.py scan  < text          # just run the privacy gate on stdin; exit 1 if matches
    plib.py mine  --source all --out DIR [--since YYYY-MM-DD] [--min-len N] [--limit N]

Stored format (v2): frontmatter `title/scenarios/tags/source/session/date`, then four sections —
`## Original` (the de-privacy'd prompt as it was actually sent), `## Optimized` (a rewrite worth reusing),
`## When to use`, `## When NOT to use`. Files written by v1 (a bare body, no sections) still read fine:
their whole body is treated as the Original.

Default --root: recommendations/prompt-library. Dependency-free.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

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

SECTIONS = ("Original", "Optimized", "When to use", "When NOT to use")


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


# ---------------------------------------------------------------- v2 sections

def _fence(text):
    """A fence long enough to wrap `text` verbatim, even when the prompt itself contains ``` blocks."""
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def split_sections(body):
    """Split a stored body into its `## <known section>` parts, ignoring headings inside fenced blocks.

    A v1 body (written before sections existed) has none of the known headings — its whole body is the
    Original, which is exactly what it was."""
    out, cur, buf, fence = {}, None, [], None
    for line in body.splitlines():
        stripped = line.strip()
        if fence is None:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                fence = m.group(1)
            else:
                h = re.match(r"^##\s+(.+?)\s*$", line)
                if h and h.group(1) in SECTIONS:
                    if cur:
                        out[cur] = "\n".join(buf).strip()
                    cur, buf = h.group(1), []
                    continue
        elif re.match(r"^%s{%d,}\s*$" % (re.escape(fence[0]), len(fence)), stripped):
            fence = None
        buf.append(line)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return out or {"Original": body.strip()}


def _one_line(text, fallback):
    """First SENTENCE of `text`, unwrapped — the `> purpose` line under the title."""
    para = " ".join(ln.lstrip("-* ").strip() for ln in text.strip().split("\n\n")[0].splitlines()).strip()
    if not para:
        return fallback
    m = re.match(r"^(.{20,200}?[.!?])(\s|$)", para)
    return m.group(1) if m else para


def render(title, original, optimized="", when="", when_not="", scenarios="", tags="", source="", session="", date=""):
    """Render a v2 prompt file. Verbatim prompt text is fenced so it stays copy-pasteable and never
    collides with the section headings."""
    purpose = _one_line(when, f"Reusable prompt for {scenarios or 'general'}.")
    doc = [
        "---",
        f"title: {title}",
        f"scenarios: {scenarios}",
        f"tags: {tags}",
        f"source: {source}",
        f"session: {session}".rstrip(),
        f"date: {date}".rstrip(),
        "---",
        "",
        f"# {title}",
        "",
        f"> {purpose}",
        "",
        "## Original",
        "",
        f"{_fence(original)}text",
        original.strip("\n"),
        _fence(original),
        "",
    ]
    if optimized.strip():
        doc += ["## Optimized", "", f"{_fence(optimized)}text", optimized.strip("\n"), _fence(optimized), ""]
    for head, text in (("When to use", when), ("When NOT to use", when_not)):
        if text.strip():
            doc += [f"## {head}", "", text.strip("\n"), ""]
    return "\n".join(doc).rstrip("\n") + "\n"


def _textarg(value):
    """A text flag is either a literal or `@path` to read the text from a file."""
    if value and value.startswith("@"):
        return _read(os.path.expanduser(value[1:]))
    return value or ""


# ---------------------------------------------------------------- commands

def cmd_scan(args):
    hits = privacy_scan(sys.stdin.read())
    for label, snip in hits:
        print(f"{label}: {snip}", file=sys.stderr)
    return 1 if hits else 0


def cmd_add(args):
    original = sys.stdin.read()
    doc = render(
        args.title, original,
        optimized=_textarg(args.optimized), when=_textarg(args.when), when_not=_textarg(args.when_not),
        scenarios=args.scenarios, tags=args.tags, source=args.source, session=args.session,
        date=args.date or datetime.date.today().isoformat(),
    )
    # Scan the RENDERED document: title, every section and every frontmatter value in one pass, so
    # nothing reaches disk without having gone through the gate.
    hits = privacy_scan(doc)
    if hits:
        print("REFUSED: prompt still contains private content — de-privacy first (see privacy-redact):", file=sys.stderr)
        for label, snip in hits:
            print(f"  - {label}: {snip}", file=sys.stderr)
        return 1
    os.makedirs(_prompts_dir(args.root), exist_ok=True)
    path = os.path.join(_prompts_dir(args.root), f"{_slug(args.title)}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    cmd_index(args)
    print(path)
    return 0


def _first_line(text, width=90):
    line = " ".join(text.strip().lstrip("- ").split())
    return (line[: width - 1] + "…") if len(line) > width else line


def cmd_index(args):
    os.makedirs(args.root, exist_ok=True)
    rows = []
    for p in _entries(args.root):
        fm, body = _fm(_read(p))
        sec = split_sections(body)
        rows.append((fm, sec, os.path.relpath(p, args.root)))
    out = [
        "# Prompt library",
        "",
        "> Reusable prompts, de-privacy'd and tagged by scenario — copy the Optimized block, or read"
        " When to use to decide whether this is the right prompt for the job.",
        "",
        "## Master TOC",
        "",
        "- [All prompts](#all-prompts)",
        "- [By scenario](#by-scenario)",
        "",
        "## All prompts",
        "",
        f"{len(rows)} reusable prompt(s). Each file holds the original prompt, an optimized rewrite, and"
        " when to use / when not to use it.",
        "",
    ]
    cell = lambda v: str(v).replace("|", "\\|").replace("\n", " ")  # noqa: E731
    if rows:
        out += ["| title | scenarios | when to use | source | file |", "|---|---|---|---|---|"]
        for fm, sec, rel in rows:
            out.append(
                f"| {cell(fm.get('title',''))} | {cell(fm.get('scenarios',''))} |"
                f" {cell(_first_line(_one_line(sec.get('When to use', ''), ''), 110))} |"
                f" {cell(fm.get('source',''))} | `{rel}` |"
            )
        by_scen = {}
        for fm, _sec, rel in rows:
            for s in [x.strip() for x in fm.get("scenarios", "").split(",") if x.strip()]:
                by_scen.setdefault(s, []).append((fm.get("title", ""), rel))
        out += ["", "## By scenario", ""]
        for s in sorted(by_scen):
            titles = ", ".join(f"[{t}]({r})" for t, r in sorted(by_scen[s]))
            out.append(f"- **{s}** — {titles}")
    with open(os.path.join(args.root, "INDEX.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip("\n") + "\n")
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


def _miner():
    spec = importlib.util.spec_from_file_location("plib_mine", os.path.join(HERE, "plib_mine.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_mine(args):
    """Mine CANDIDATES from local agent histories into --out. Never publishes: the raw text still holds
    absolute paths and codenames, and the optimized rewrite plus scenario tags need human judgement."""
    mine = _miner()
    try:
        sources = mine.resolve_sources(args.source)
    except ValueError as e:
        print(f"plib mine: {e}", file=sys.stderr)
        return 2
    out = os.path.abspath(os.path.expanduser(args.out))
    root = os.path.abspath(args.root)
    if out == root or out.startswith(root + os.sep):
        print(f"plib mine: refusing to write raw mined text inside the publishable library ({args.root}) —"
              " pick an --out outside it", file=sys.stderr)
        return 2

    cands, counts = mine.mine(sources, since=args.since, min_len=args.min_len, limit=args.limit)
    os.makedirs(out, exist_ok=True)
    jsonl = os.path.join(out, "candidates.jsonl")
    with open(jsonl, "w", encoding="utf-8") as f:
        for c in cands:
            c["privacy"] = sorted({label for label, _ in privacy_scan(c["text"])})
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    review = [
        "# Mined prompt candidates",
        "",
        "> RAW, NOT de-privacy'd — do not publish any of this verbatim. Curate the top rows, rewrite them,"
        " then `plib.py add` so the privacy gate runs.",
        "",
        "## Master TOC",
        "",
        "- [Per source](#per-source)",
        "- [Ranked candidates](#ranked-candidates)",
        "",
        "## Per source",
        "",
        "| source | kept |",
        "|---|---|",
    ]
    review += [f"| {name} | {counts.get(name, 0)} |" for name in sources]
    review += [
        f"| **total (de-duplicated)** | **{len(cands)}** |",
        "",
        "## Ranked candidates",
        "",
        "| # | score | occ | source | date | first line |",
        "|---|---|---|---|---|---|",
    ]
    for c in cands:
        head = _first_line(c["text"].splitlines()[0] if c["text"].splitlines() else "", 110).replace("|", "\\|")
        review.append(f"| {c['rank']} | {c['score']} | {c['occurrences']} | {','.join(c['sources'])} | {c['date']} | {head} |")
    with open(os.path.join(out, "REVIEW.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(review) + "\n")

    for name in sources:
        print(f"{name}\t{counts.get(name, 0)}", file=sys.stderr)
    print(f"total\t{len(cands)}", file=sys.stderr)
    print(jsonl)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="plib.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan")  # reads stdin only
    for name in ("add", "index", "find", "mine"):
        p = sub.add_parser(name)
        p.add_argument("--root", default="recommendations/prompt-library")
        if name == "add":
            p.add_argument("--title", required=True)
            p.add_argument("--scenarios", default="")
            p.add_argument("--source", default="")
            p.add_argument("--tags", default="")
            p.add_argument("--optimized", default="", help="optimized rewrite; literal text or @path")
            p.add_argument("--when", default="", help="when to use; literal text or @path")
            p.add_argument("--when-not", dest="when_not", default="", help="when NOT to use; literal text or @path")
            p.add_argument("--session", default="", help="optional provenance id (leave empty when publishing)")
            p.add_argument("--date", default="", help="YYYY-MM-DD; defaults to today")
        if name == "find":
            p.add_argument("--query", default="")
            p.add_argument("--top", type=int, default=10)
        if name == "mine":
            p.add_argument("--source", default="all", help="claude|claude-history|claude-transcripts|codex|copilot|copilot-cli|copilot-vscode|opencode|all (comma-separated)")
            p.add_argument("--out", required=True, help="candidate directory — must be OUTSIDE the library")
            p.add_argument("--since", default="", help="YYYY-MM-DD; keep prompts at or after this date")
            p.add_argument("--min-len", type=int, default=120, help="drop prompts shorter than N characters")
            p.add_argument("--limit", type=int, default=0, help="emit only the top N ranked candidates")
    args = ap.parse_args(argv)
    if args.cmd == "mine":
        args.since = args.since or None
        args.limit = args.limit or None
    return {"scan": cmd_scan, "add": cmd_add, "index": cmd_index, "find": cmd_find, "mine": cmd_mine}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
