#!/usr/bin/env python3
# doc-writing · version: 0.1.0
"""doccheck — lint a written Markdown document against the mechanically checkable doc rules.

The rules come from `skills/doc-writing/SKILL.md`, mined from two real project sessions. Every finding
cites the mined rule it enforces (`B<n>` = consolidated rule n) plus its frequency rank (`#<n>` = how
often the user had to repeat the point), so the author can look up why the check exists.

    doccheck.py <file.md> [--type spec|manual|report|readme|release-notes|plan|handoff|generic]
                          [--json] [--strict] [--config PATH]

Checks:
  1 secrets            ERROR  a credential, token, private path, or email in the text          (B1,  #10)
  2 bare-ref           WARN   a path, filename, commit, or PR number that is not a link        (B4,  #4)
  3 undefined-jargon   WARN   an ALL-CAPS acronym the document never glosses                   (B6,  #1)
  4 missing-diagram    WARN   no mermaid diagram, for types that require one                   (B5,  #6)
  5 missing-section    WARN   no verification / remaining-tasks heading, per type          (B2/B18, #3/#9)
  6 render             WARN   a table or list glued to the line above, or a broken table        (B12)
  7 staleness          WARN   TODO / TBD / FIXME / XXX / placeholder / 待补充                    (B11, #5)
  8 list-numbering     INFO   a flat list of more than 3 items using dashes instead of numbers

Exit codes: 0 clean · 1 warnings present (with --strict, info-level findings fail too) · 2 errors present.
A secret is always an ERROR and always exits 2; --strict cannot make it milder, and the matched text is
never echoed, because echoing it would put the secret back into the session transcript (rule B1).

Stdlib only. Per-type required sections, the acronym stoplist, marker lists, and type inference live in
`../doccheck.config.json` so they are editable without touching this file.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(os.path.dirname(HERE), "doccheck.config.json")

ERROR, WARN, INFO = "error", "warning", "info"
_LEVEL_RANK = {ERROR: 0, WARN: 1, INFO: 2}

# Secret / private-content patterns. Kept in CODE rather than in the JSON config on purpose: a document
# must not be able to weaken its own leak check by editing a config file. The first five mirror
# `skills/prompt-library/scripts/plib.py` PRIVACY_PATTERNS; the sixth is added here because the mined
# evidence includes a password that was written into a document and had to be purged from git history.
SECRET_PATTERNS = [
    (r"/home/[A-Za-z0-9._-]+", "absolute home path"),
    (r"/media/[A-Za-z0-9._-]+", "absolute media path"),
    (r"/mnt/[0-9a-fA-F-]{8,}", "absolute mnt uuid path"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email address"),
    (r"\b(?:sk-[A-Za-z0-9]{6,}|ghp_[A-Za-z0-9]{6,}|gho_[A-Za-z0-9]{6,}|github_pat_[A-Za-z0-9_]{6,})",
     "token-shaped string"),
    (r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token)\b\s*[=:]\s*[\"']?([^\s\"'<>,;`]{8,})",
     "credential assignment"),
]

# A credential assignment whose value looks like a stand-in is not a leak.
_PLACEHOLDER_HINTS = ("your", "changeme", "change-me", "redacted", "xxxx", "****", "...", "…",
                      "placeholder", "example", "dummy", "somevalue", "value-here", "see-")

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})\s*(\S*)")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)\s]*(?:\s+\"[^\"]*\")?\)")
LINK_TARGET_RE = re.compile(r"\]\([^)]*\)")
REF_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*\S+")
AUTOLINK_RE = re.compile(r"<[^>\s]+>")
RAW_URL_RE = re.compile(r"\b(?:https?|ftp)://\S+")

HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d{1,3}[.)])\s+\S")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|[\s:|-]*$")

# Bare-reference shapes. Each is something the user asked to always arrive as a full, navigable link.
PATH_RE = re.compile(r"(?<![\w/.-])(?:[\w.-]+/)+[\w.-]+\.[A-Za-z]\w{0,5}(?![\w/])")
FILE_RE = re.compile(
    r"(?<![\w/.-])[\w-]+(?:\.[\w-]+)*\."
    r"(?:md|py|ts|tsx|js|jsx|mjs|cjs|json|ya?ml|sh|sql|toml|go|rs|java|rb|php|css|scss|html|tex|ipynb|cfg|ini)"
    r"\b(?![\w/])")
# 7-40 hex chars containing at least one letter and at least one digit (rules out plain numbers and words
# like "deadbeef"), not preceded by `#` (rules out hex colours).
HASH_RE = re.compile(r"(?<![\w#])(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}(?![\w])")
ISSUE_RE = re.compile(r"(?<![\w#])#\d{1,6}\b|\b(?:PR|pull request|issue)\s+#?\d{1,6}\b", re.I)
# 3+ upper-case chars, keeping a hyphenated coined phrase (FAKE-RUN) as one term rather than two.
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9]{2,}(?:-[A-Z][A-Z0-9]*)*\b")


def _blank(m):
    """Replace a match with spaces so column offsets in the line survive masking."""
    return " " * len(m.group(0))


def _finding(level, check, rule, line, message):
    return {"level": level, "check": check, "rule": rule, "line": line, "message": message}


def load_config(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class Doc:
    """A parsed Markdown document: raw lines plus the masked views the checks need."""

    def __init__(self, text, path):
        self.path = path
        self.lines = text.splitlines()
        n = len(self.lines)

        # YAML frontmatter is metadata, not prose. Skip it everywhere except the secret scan. Only when a
        # closing `---` turns up early, so a lone horizontal rule cannot swallow the whole document.
        self.frontmatter = set()
        if self.lines and self.lines[0].strip() == "---":
            for i in range(1, min(n, 40)):
                if self.lines[i].strip() == "---":
                    self.frontmatter = set(range(i + 1))
                    break

        self.in_fence, self.fence_langs, self.unclosed_fence = self._scan_fences(self.lines)

        self.mask_code, self.mask_refs, self.mask_jargon = [], [], []
        for ln in self.lines:
            code = INLINE_CODE_RE.sub(_blank, ln)
            refs = AUTOLINK_RE.sub(_blank, MD_LINK_RE.sub(_blank, code))
            refs = RAW_URL_RE.sub(_blank, refs)
            if REF_DEF_RE.match(ln):
                refs = " " * len(ln)
            jarg = LINK_TARGET_RE.sub(_blank, code)          # keep link text, drop the target
            jarg = RAW_URL_RE.sub(_blank, AUTOLINK_RE.sub(_blank, jarg))
            jarg = FILE_RE.sub(_blank, PATH_RE.sub(_blank, jarg))  # a filename is not jargon
            self.mask_code.append(code)
            self.mask_refs.append(refs)
            self.mask_jargon.append(jarg)

    @staticmethod
    def _scan_fences(lines):
        in_fence = [False] * len(lines)
        langs, opener, marker = [], None, None
        for i, ln in enumerate(lines):
            m = FENCE_RE.match(ln)
            if opener is None:
                if m:
                    opener, marker = i, m.group(1)[0]
                    langs.append((i, m.group(2).lower()))
                    in_fence[i] = True
            else:
                in_fence[i] = True
                if m and m.group(1)[0] == marker and not m.group(2).strip():
                    opener = None
        return in_fence, langs, opener

    def body(self):
        """Yield (index, raw) for prose lines only — outside fences and frontmatter."""
        for i, ln in enumerate(self.lines):
            if not self.in_fence[i] and i not in self.frontmatter:
                yield i, ln

    def headings(self):
        for i, ln in self.body():
            m = HEADING_RE.match(ln)
            if m:
                yield i, len(m.group(1)), m.group(2).strip()


# --------------------------------------------------------------------------------------- checks

def _placeholderish(value):
    low = value.lower()
    return any(h in low for h in _PLACEHOLDER_HINTS) or set(low) <= set("x*.-_ ")


def check_secrets(doc, cfg):
    """B1 (#10) — a real secret must never reach a document. Scans raw text, fences included."""
    allow = [a.lower() for a in cfg.get("secret_allowlist", [])]
    out, seen = [], set()
    for i, ln in enumerate(doc.lines):
        for pat, label in SECRET_PATTERNS:
            for m in re.finditer(pat, ln):
                hit = m.group(0)
                if any(a in hit.lower() for a in allow):
                    continue
                if label == "credential assignment" and _placeholderish(m.group(1)):
                    continue
                if (i, label) in seen:
                    continue
                seen.add((i, label))
                out.append(_finding(
                    ERROR, "secrets", "B1", i + 1,
                    f"{label} ({len(hit)} chars) — not echoed here on purpose, printing it would put the "
                    f"secret back into the session. Open the line, remove the value, and reference where "
                    f"the credential lives instead."))
    return out


def check_bare_refs(doc, cfg):
    """B4 (#4) — every path, file, commit, PR, or issue arrives as a full navigable link."""
    kinds = [(PATH_RE, "file path"), (FILE_RE, "filename"), (HASH_RE, "commit hash"),
             (ISSUE_RE, "pull request or issue number")]
    hits = {}
    for i, _ in doc.body():
        masked = doc.mask_refs[i]
        for rx, kind in kinds:
            for m in rx.finditer(masked):
                text = m.group(0).strip()
                key = (kind, text)
                if key not in hits:
                    hits[key] = [i + 1, 0]
                hits[key][1] += 1
    out = []
    for (kind, text), (line, count) in hits.items():
        extra = f" ({count} occurrences)" if count > 1 else ""
        out.append(_finding(WARN, "bare-ref", "B4", line,
                            f"bare {kind} \"{text}\"{extra} — give the full clickable link, or wrap it in "
                            f"a code span if it is not meant to be navigable"))
    return sorted(out, key=lambda f: f["line"])


def _defines(term, line):
    """True if `line` glosses `term` — parenthetical, dash gloss, or definition-list entry."""
    t = re.escape(term)
    tests = [
        rf"\b{t}\b\s*[（(][^)）]{{2,}}[)）]",            # ETL (extract, transform, load)
        rf"[（(][^)）]*\b{t}\b[^)）]*[)）]",              # extract, transform, load (ETL)
        rf"\b{t}\b\s*[—–-]\s+\S",                       # ETL — extract, transform, load
        rf"\b{t}\b\s*[:：]\s*\S",                       # ETL: extract, transform, load
        rf"^\s*[-*+]\s+\**{t}\**\s*[—–:：-]",           # - **ETL** — ...
        rf"^\s*\|\s*\**{t}\**\s*\|",                    # | ETL | ... |
        rf"\b{t}\b\s*(?:是|指|即)",                      # ETL 是 ...
    ]
    return any(re.search(p, line) for p in tests)


def check_jargon(doc, cfg):
    """B6 (#1) — the highest-frequency friction: define every term, acronym, or coined phrase in place."""
    stop = {s.upper() for s in cfg.get("acronym_stoplist", [])}
    first, defined = {}, set()
    for i, _ in doc.body():
        masked = doc.mask_jargon[i]
        words = [w for w in re.findall(r"[A-Za-z]+", masked) if w]
        shouting = len(words) >= 3 and all(w.isupper() for w in words)
        if shouting:
            continue
        for m in ACRONYM_RE.finditer(masked):
            term = m.group(0)
            if term in stop:
                continue
            first.setdefault(term, i + 1)
            prev = doc.mask_jargon[i - 1] if i > 0 else ""
            if _defines(term, masked) or (prev and _defines(term, prev)):
                defined.add(term)
    out = []
    for term, line in sorted(first.items(), key=lambda kv: kv[1]):
        if term in defined:
            continue
        out.append(_finding(WARN, "undefined-jargon", "B6", line,
                            f"\"{term}\" is used but never glossed — define it in place on first use "
                            f"(a parenthetical, a dash gloss, or a glossary row)"))
    return out


def check_diagram(doc, cfg, dtype):
    """B5 (#6) — mermaid diagrams wherever a diagram is possible."""
    if not cfg["types"][dtype].get("require_mermaid"):
        return []
    if any(lang.startswith("mermaid") for _, lang in doc.fence_langs):
        return []
    return [_finding(WARN, "missing-diagram", "B5", 1,
                     f"a {dtype} carries no mermaid diagram — add the architecture, data flow, and storage "
                     f"diagrams, one per feature and one per layer that behaves differently")]


def check_sections(doc, cfg, dtype):
    """B2 (#3) and B18 (#9) — the sections a given document type must carry."""
    wanted = cfg["types"][dtype].get("required_sections", [])
    if not wanted:
        return []
    texts = [text for _, _, text in doc.headings()]
    out = []
    for sid in wanted:
        spec = cfg["sections"][sid]
        if any(re.search(p, t) for t in texts for p in spec["patterns"]):
            continue
        out.append(_finding(WARN, "missing-section", spec["rule"], 1,
                            f"a {dtype} has no {sid} section — add a heading covering {spec['label']} "
                            f"(frequency rank {spec['rank']})"))
    return out


def _kind(doc, i):
    ln = doc.lines[i]
    if doc.in_fence[i] or i in doc.frontmatter:
        return "skip"
    if not ln.strip():
        return "blank"
    if HEADING_RE.match(ln):
        return "heading"
    if TABLE_ROW_RE.match(ln):
        return "table"
    if LIST_RE.match(ln):
        return "list"
    if ln[:1] in (" ", "\t"):
        return "cont"
    return "text"


def check_render(doc, cfg):
    """B12 — a document that does not render is a defect the user reports."""
    out = []
    if doc.unclosed_fence is not None:
        out.append(_finding(WARN, "render", "B12", doc.unclosed_fence + 1,
                            "code fence opened here is never closed — everything below it stops rendering"))
    glued = "no blank line above it, so it renders as raw source in the terminal and on a phone"
    prev, list_open, table = "blank", False, []

    def flush_table():
        if len(table) >= 2 and not TABLE_SEP_RE.match(doc.lines[table[1]]):
            out.append(_finding(WARN, "render", "B12", table[0] + 1,
                                "table has no |---| separator row after its header, so it renders as "
                                "plain text"))
        table.clear()

    for i in range(len(doc.lines)):
        k = _kind(doc, i)
        if k != "table" and table:
            flush_table()
        if k == "list":
            if not list_open and prev in ("heading", "text", "table"):
                out.append(_finding(WARN, "render", "B12", i + 1, f"list has {glued}"))
            list_open = True
        elif k == "table":
            if not table and prev in ("heading", "text", "list", "cont"):
                out.append(_finding(WARN, "render", "B12", i + 1, f"table has {glued}"))
            table.append(i)
            list_open = False
        elif k in ("heading", "text", "skip"):
            list_open = False
        prev = k
    if table:
        flush_table()
    return sorted(out, key=lambda f: f["line"])


def check_staleness(doc, cfg):
    """B11 (#5) — a document that has gone stale is a rejection, not a nit."""
    out = []
    for i, _ in doc.body():
        masked = doc.mask_code[i]
        for pat in cfg.get("staleness_markers", []):
            m = re.search(pat, masked)
            if m:
                out.append(_finding(WARN, "staleness", "B11", i + 1,
                                    f"staleness marker \"{m.group(0)}\" — either finish the statement or "
                                    f"move it into the remaining-tasks section with its risk"))
                break
    return out


def check_list_numbering(doc, cfg):
    """House rule (rules/human-readable-output) — more than 3 flat items must be numbered."""
    conf = cfg.get("list_numbering", {})
    limit = conf.get("max_dash_items", 3)
    exempt = [h.lower() for h in conf.get("exempt_under_headings", [])]
    out, heading, groups = [], "", {}

    def flush():
        for (indent, start), count in sorted(groups.items(), key=lambda kv: kv[0][1]):
            if count > limit:
                out.append(_finding(INFO, "list-numbering", "house", start + 1,
                                    f"flat list of {count} dash items — more than {limit} items must be "
                                    f"numbered so they scan and can be referred back to"))
        groups.clear()

    for i in range(len(doc.lines)):
        k = _kind(doc, i)
        if k == "heading":
            flush()
            heading = HEADING_RE.match(doc.lines[i]).group(2).strip().lower()
            continue
        if k in ("text", "table", "skip"):
            flush()
            continue
        if k == "list" and not any(e in heading for e in exempt):
            m = LIST_RE.match(doc.lines[i])
            indent = len(m.group(1).expandtabs(4))
            if m.group(2) in ("-", "*", "+"):
                key = next((k2 for k2 in groups if k2[0] == indent), (indent, i))
                groups[key] = groups.get(key, 0) + 1
            else:
                groups.pop(next((k2 for k2 in groups if k2[0] == indent), (indent, i)), None)
    flush()
    return sorted(out, key=lambda f: f["line"])


# ----------------------------------------------------------------------------------------- driver

def infer_type(path, cfg):
    base = os.path.basename(path)
    for rule in cfg.get("type_inference", []):
        if re.search(rule["pattern"], base):
            return rule["type"], True
    return "generic", False


def lint(text, path, dtype, cfg):
    doc = Doc(text, path)
    findings = []
    findings += check_secrets(doc, cfg)
    findings += check_bare_refs(doc, cfg)
    findings += check_jargon(doc, cfg)
    findings += check_diagram(doc, cfg, dtype)
    findings += check_sections(doc, cfg, dtype)
    findings += check_render(doc, cfg)
    findings += check_staleness(doc, cfg)
    findings += check_list_numbering(doc, cfg)
    return sorted(findings, key=lambda f: (f["line"], _LEVEL_RANK[f["level"]], f["check"]))


def exit_code(findings, strict):
    if any(f["level"] == ERROR for f in findings):
        return 2
    if any(f["level"] == WARN for f in findings):
        return 1
    if strict and findings:
        return 1
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="doccheck.py",
        description="Lint a Markdown document against the mechanically checkable doc-writing rules.",
        epilog="Exit codes: 0 clean, 1 warnings (with --strict, info findings fail too), 2 errors. "
               "A secret is always an error.")
    ap.add_argument("file", help="the Markdown file to lint")
    ap.add_argument("--type", dest="dtype", default=None,
                    help="document type; inferred from the filename when omitted")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--strict", action="store_true", help="also fail on info-level findings")
    ap.add_argument("--config", default=DEFAULT_CONFIG, help=f"config file (default {DEFAULT_CONFIG})")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except (OSError, ValueError) as err:
        print(f"doccheck: cannot read config {args.config}: {err}", file=sys.stderr)
        return 2
    try:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    except OSError as err:
        print(f"doccheck: cannot read {args.file}: {err}", file=sys.stderr)
        return 2

    if args.dtype:
        if args.dtype not in cfg["types"]:
            print(f"doccheck: unknown --type {args.dtype!r}; choose from "
                  f"{', '.join(sorted(cfg['types']))}", file=sys.stderr)
            return 2
        dtype, inferred = args.dtype, False
    else:
        dtype, inferred = infer_type(args.file, cfg)

    findings = lint(text, args.file, dtype, cfg)
    counts = {lv: sum(1 for f in findings if f["level"] == lv) for lv in (ERROR, WARN, INFO)}
    code = exit_code(findings, args.strict)

    if args.json:
        print(json.dumps({"file": args.file, "type": dtype, "type_inferred": inferred,
                          "strict": args.strict, "counts": counts, "exit_code": code,
                          "findings": findings}, ensure_ascii=False, indent=2))
        return code

    note = "" if args.dtype else (" (inferred)" if inferred else " (inferred; pass --type for the "
                                                                "per-type checks)")
    print(f"{args.file}  ·  type: {dtype}{note}")
    if not findings:
        print("clean — no findings")
        return code
    print()
    for f in findings:
        print(f"{f['level'].upper():<7} {f['line']:>4}  {f['check']:<17} {f['rule']:<5} {f['message']}")
    print()
    print(f"{counts[ERROR]} error(s) · {counts[WARN]} warning(s) · {counts[INFO]} info  →  exit {code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
