#!/usr/bin/env python3
"""Tests for doccheck.py (doc-writing). Run: python3 test_doccheck.py

Every check gets a POSITIVE case (the defect is detected) and a NEGATIVE case (a document that must not
trigger it). A linter that flags everything is as useless as one that flags nothing, so the negative
cases are the real regression guard.
"""
import importlib.util
import io
import json
import os
import tempfile
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("doccheck", os.path.join(HERE, "doccheck.py"))
doccheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(doccheck)

ALL_TYPES = ["spec", "manual", "report", "readme", "release-notes", "plan", "handoff", "generic"]


def _run(text, name="doc.md", extra=()):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = doccheck.main([path, *extra])
        return rc, out.getvalue(), err.getvalue()


def _lint(text, dtype=None, name="doc.md", strict=False):
    """Return (exit_code, parsed_json)."""
    extra = ["--json"]
    if dtype:
        extra += ["--type", dtype]
    if strict:
        extra.append("--strict")
    rc, out, _ = _run(text, name, extra)
    return rc, json.loads(out)


def _of(data, check):
    return [f for f in data["findings"] if f["check"] == check]


# A document that satisfies every check for every type: mermaid diagram, verification heading,
# remaining-tasks heading, all references linked, its one acronym glossed, tables and lists spaced.
CLEAN = """# Bank logo system

> How bank logos are fetched, cached, and served.

## Master TOC

- [Terminology](#terminology)
- [Architecture](#architecture)
- [Verification](#verification)

## Terminology

- **ETL** — extract, transform, load. The nightly job that refills the cache.

## Architecture

```mermaid
flowchart TD
    A[Fetcher] --> B[Cache]
```

The fetcher lives in [the fetch module](https://example.invalid/repo/blob/main/fetch.py).

| Source | Count |
|---|---|
| direct | 12 |

## Verification

Run the check script and compare the row count against the table above.

## Remaining tasks

1. Backfill the ten banks that still have no logo.
2. Add a rate limit guard before the next import.
"""

PLAIN = """# Title

> One line purpose.

## Section

Plain prose with nothing wrong in it.
"""


def _plain(*extra_lines):
    return PLAIN + "\n" + "\n".join(extra_lines) + "\n"


# ------------------------------------------------------------------ 1. clean documents pass

def t_clean_every_type():
    for dtype in ALL_TYPES:
        rc, data = _lint(CLEAN, dtype)
        assert rc == 0, f"clean {dtype} should exit 0, got {rc}: {data['findings']}"
        assert data["findings"] == [], f"clean {dtype} produced findings: {data['findings']}"
    rc, data = _lint(PLAIN, "generic")
    assert rc == 0 and not data["findings"], data["findings"]


def t_type_inference():
    _, data = _lint(CLEAN, None, name="HANDOFF-2026-07-13.md")
    assert data["type"] == "handoff" and data["type_inferred"] is True, data["type"]
    _, data = _lint(CLEAN, None, name="README.md")
    assert data["type"] == "readme", data["type"]
    _, data = _lint(PLAIN, None, name="doc.md")
    assert data["type"] == "generic" and data["type_inferred"] is False, data["type"]


# ------------------------------------------------------------------ 2. secrets (ERROR, rule B1)

def t_secrets_positive():
    token = "sk" + "-" + "b7f2c9d1" * 3
    rc, data = _lint(_plain(f"The service token is {token} and it must be rotated."), "generic")
    hits = _of(data, "secrets")
    assert hits, "token-shaped string must be caught"
    assert all(h["level"] == "error" for h in hits), hits
    assert all(h["rule"] == "B1" for h in hits), hits
    assert rc == 2, f"a secret must exit 2 without --strict, got {rc}"
    # the matched text is never echoed back
    blob = json.dumps(data, ensure_ascii=False)
    assert token not in blob, "doccheck must not echo the secret into its own output"

    rc, data = _lint(_plain("password: hunter2hunter2"), "generic")
    assert [h for h in _of(data, "secrets") if "credential" in h["message"]], data["findings"]
    assert rc == 2

    rc, _ = _lint(_plain("Contact the owner at real.person@some-company.co.uk for access."), "generic")
    assert rc == 2, "an address in a document is a leak"


def t_secrets_negative():
    doc = _plain(
        "The Clerk key lives in the local environment file and is never written down here.",
        "",
        "    api_key = <set in the environment, see the deployment manual>",
        "",
        "Questions go to you@example.com, which is a placeholder address.",
    )
    hits = _of(_lint(doc, "generic")[1], "secrets")
    assert not hits, f"placeholder credentials and allowlisted addresses must not fire: {hits}"


# ------------------------------------------------------------------ 3. bare references (rule B4)

def t_bare_refs_positive():
    _, data = _lint(_plain("See src/app/page.tsx, commit a1b2c3d4e5, and PR #42 for the change."),
                    "generic")
    kinds = " ".join(f["message"] for f in _of(data, "bare-ref"))
    assert "file path" in kinds, kinds
    assert "commit hash" in kinds, kinds
    assert "pull request or issue number" in kinds, kinds
    assert all(f["level"] == "warning" and f["rule"] == "B4" for f in _of(data, "bare-ref"))


def t_bare_refs_negative():
    doc = _plain(
        "See [the page component](https://example.invalid/x), commit `a1b2c3d4e5`, and",
        "[PR 42](https://example.invalid/pull/42) for the change.",
        "",
        "Version 1.2.3 shipped on 2026-07-18 with 15 fixes.",
    )
    hits = _of(_lint(doc, "generic")[1], "bare-ref")
    assert not hits, f"linked, code-spanned, and non-reference text must not fire: {hits}"


# ------------------------------------------------------------------ 4. undefined jargon (rule B6, rank 1)

def t_jargon_positive():
    _, data = _lint(_plain("The ETL job runs nightly and refills the cache."), "generic")
    hits = _of(data, "undefined-jargon")
    assert len(hits) == 1 and "ETL" in hits[0]["message"], hits
    assert hits[0]["rule"] == "B6" and hits[0]["level"] == "warning", hits


def t_jargon_negative():
    forms = [
        "The ETL (extract, transform, load) job runs nightly.",
        "The extract-transform-load pass (ETL) runs nightly.",
        "ETL — extract, transform, load — runs nightly.",
        "- **ETL**: the nightly extract, transform, load pass.",
        "The JSON payload is validated before the HTTP call.",
    ]
    for line in forms:
        hits = _of(_lint(_plain(line), "generic")[1], "undefined-jargon")
        assert not hits, f"defined or stoplisted term fired: {line!r} -> {hits}"
    # a filename is not jargon
    hits = _of(_lint(_plain("See [the handoff](https://example.invalid/HANDOFF-2026-07-13.md)."),
                     "generic")[1], "undefined-jargon")
    assert not hits, hits


# ------------------------------------------------------------------ 5. mermaid diagram (rule B5)

def t_diagram_positive():
    no_diagram = CLEAN.replace("```mermaid\nflowchart TD\n    A[Fetcher] --> B[Cache]\n```\n\n", "")
    for dtype in ("spec", "manual", "plan"):
        hits = _of(_lint(no_diagram, dtype)[1], "missing-diagram")
        assert len(hits) == 1, f"{dtype} must require a mermaid diagram: {hits}"


def t_diagram_negative():
    no_diagram = CLEAN.replace("```mermaid\nflowchart TD\n    A[Fetcher] --> B[Cache]\n```\n\n", "")
    for dtype in ("report", "readme", "release-notes", "handoff", "generic"):
        assert not _of(_lint(no_diagram, dtype)[1], "missing-diagram"), dtype
    for dtype in ("spec", "manual", "plan"):
        assert not _of(_lint(CLEAN, dtype)[1], "missing-diagram"), dtype


# ------------------------------------------------------------------ 6/7. required sections (B2, B18)

def t_sections_positive():
    stripped = CLEAN.replace("## Verification", "## Notes").replace("## Remaining tasks", "## Extras")
    for dtype, want in (("spec", {"verification", "remaining-tasks"}),
                        ("report", {"verification", "remaining-tasks"}),
                        ("manual", {"verification"}),
                        ("plan", {"remaining-tasks"})):
        hits = _of(_lint(stripped, dtype)[1], "missing-section")
        got = {"verification" if "verification" in h["message"] else "remaining-tasks" for h in hits}
        assert got == want, f"{dtype}: expected {want}, got {got} ({[h['message'] for h in hits]})"


def t_sections_negative():
    stripped = CLEAN.replace("## Verification", "## Notes").replace("## Remaining tasks", "## Extras")
    for dtype in ("readme", "release-notes", "handoff", "generic"):
        assert not _of(_lint(stripped, dtype)[1], "missing-section"), dtype
    for dtype in ("spec", "report", "manual", "plan"):
        assert not _of(_lint(CLEAN, dtype)[1], "missing-section"), dtype
    # Chinese headings satisfy the same requirement
    zh = CLEAN.replace("## Verification", "## 如何验证").replace("## Remaining tasks", "## 剩余任务")
    assert not _of(_lint(zh, "spec")[1], "missing-section"), "Chinese headings must count"


# ------------------------------------------------------------------ 8. rendering defects (rule B12)

def t_render_positive():
    glued_table = _plain("Intro text", "| a | b |", "|---|---|", "| 1 | 2 |")
    hits = _of(_lint(glued_table, "generic")[1], "render")
    assert len(hits) == 1 and "blank line above" in hits[0]["message"], hits

    glued_list = _plain("**Steps**", "- one", "- two")
    hits = _of(_lint(glued_list, "generic")[1], "render")
    assert len(hits) == 1 and "list has" in hits[0]["message"], hits

    no_sep = _plain("", "| a | b |", "| 1 | 2 |")
    hits = _of(_lint(no_sep, "generic")[1], "render")
    assert len(hits) == 1 and "separator" in hits[0]["message"], hits

    unclosed = _plain("", "```python", "print(1)")
    hits = _of(_lint(unclosed, "generic")[1], "render")
    assert len(hits) == 1 and "never closed" in hits[0]["message"], hits


def t_render_negative():
    ok = _plain(
        "Intro text.",
        "",
        "| a | b |",
        "|---|---|",
        "| 1 | 2 |",
        "",
        "**Steps**",
        "",
        "- one",
        "  continued on the next line",
        "- two",
        "",
        "```python",
        "print(1)",
        "```",
    )
    hits = _of(_lint(ok, "generic")[1], "render")
    assert not hits, f"correctly spaced blocks must not fire: {hits}"


# ------------------------------------------------------------------ 9. staleness markers (rule B11)

def t_staleness_positive():
    for marker in ("TODO: wire this up.", "Status: TBD.", "FIXME before shipping.",
                   "XXX revisit this.", "This is a placeholder section.", "本节待补充。"):
        hits = _of(_lint(_plain(marker), "generic")[1], "staleness")
        assert len(hits) == 1, f"{marker!r} -> {hits}"
        assert hits[0]["rule"] == "B11", hits


def t_staleness_negative():
    doc = _plain("The wiring is finished and verified against the staging deployment.",
                 "Every statement here was checked on 2026-07-18.")
    assert not _of(_lint(doc, "generic")[1], "staleness"), "finished prose must not fire"


# ------------------------------------------------------------------ 10. list numbering (house rule)

def t_list_numbering_positive():
    doc = _plain("## Items", "", "- alpha", "- bravo", "- charlie", "- delta", "- echo")
    rc, data = _lint(doc, "generic")
    hits = _of(data, "list-numbering")
    assert len(hits) == 1 and hits[0]["level"] == "info", hits
    assert "5 dash items" in hits[0]["message"], hits
    assert rc == 0, f"info alone must not fail the run, got {rc}"
    rc, _ = _lint(doc, "generic", strict=True)
    assert rc == 1, f"--strict must fail on info, got {rc}"


def t_list_numbering_negative():
    three = _plain("## Items", "", "- alpha", "- bravo", "- charlie")
    assert not _of(_lint(three, "generic")[1], "list-numbering"), "three items are allowed"

    numbered = _plain("## Items", "", "1. alpha", "2. bravo", "3. charlie", "4. delta", "5. echo")
    assert not _of(_lint(numbered, "generic")[1], "list-numbering"), "numbered lists are the fix"

    toc = _plain("## Master TOC", "", "- alpha", "- bravo", "- charlie", "- delta", "- echo")
    assert not _of(_lint(toc, "generic")[1], "list-numbering"), "the Master TOC list is exempt"

    split = _plain("## One", "", "- alpha", "- bravo", "", "Some prose.", "", "## Two", "",
                   "- charlie", "- delta", "- echo")
    assert not _of(_lint(split, "generic")[1], "list-numbering"), "separate lists count separately"


# ------------------------------------------------------------------ 11. output contract

def t_json_shape():
    token = "sk" + "-" + "b7f2c9d1" * 3
    rc, out, _ = _run(_plain(f"token {token}"), extra=["--json", "--type", "generic"])
    data = json.loads(out)                       # raises if the output is not valid JSON
    assert set(data) == {"file", "type", "type_inferred", "strict", "counts", "exit_code", "findings"}
    assert data["counts"]["error"] >= 1 and data["exit_code"] == 2 == rc
    for f in data["findings"]:
        assert set(f) == {"level", "check", "rule", "line", "message"}
        assert f["level"] in ("error", "warning", "info") and isinstance(f["line"], int)


def t_human_output_and_exit_codes():
    rc, out, _ = _run(CLEAN, extra=["--type", "spec"])
    assert rc == 0 and "clean — no findings" in out, out

    rc, out, _ = _run(_plain("The ETL job runs nightly."), extra=["--type", "generic"])
    assert rc == 1, f"warnings must exit 1, got {rc}"
    assert "WARN" in out and "undefined-jargon" in out and "B6" in out, out

    rc, out, _ = _run(_plain("The ETL job runs nightly."), extra=["--type", "generic", "--strict"])
    assert rc == 1, f"warnings stay 1 under --strict, got {rc}"

    rc, _, err = _run(PLAIN, extra=["--type", "nonsense"])
    assert rc == 2 and "unknown --type" in err, err

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = doccheck.main([os.path.join(HERE, "no-such-file.md")])
    assert rc == 2 and "cannot read" in err.getvalue(), err.getvalue()


TESTS = [
    ("clean document of every type passes", t_clean_every_type),
    ("type inference from the filename", t_type_inference),
    ("secrets detected as ERROR (B1)", t_secrets_positive),
    ("secrets: placeholders and allowlist do not fire", t_secrets_negative),
    ("bare references detected (B4)", t_bare_refs_positive),
    ("bare references: linked and code-spanned do not fire", t_bare_refs_negative),
    ("undefined jargon detected (B6, rank 1)", t_jargon_positive),
    ("undefined jargon: glossed and stoplisted do not fire", t_jargon_negative),
    ("missing mermaid diagram detected (B5)", t_diagram_positive),
    ("missing mermaid: only for the types that need one", t_diagram_negative),
    ("missing verification / remaining-tasks detected (B2, B18)", t_sections_positive),
    ("required sections: present or not required do not fire", t_sections_negative),
    ("rendering defects detected (B12)", t_render_positive),
    ("rendering: correctly spaced blocks do not fire", t_render_negative),
    ("staleness markers detected (B11)", t_staleness_positive),
    ("staleness: finished prose does not fire", t_staleness_negative),
    ("flat list of more than 3 dashes detected (info)", t_list_numbering_positive),
    ("list numbering: short, numbered, and TOC lists do not fire", t_list_numbering_negative),
    ("--json emits valid JSON with the documented shape", t_json_shape),
    ("human output and exit codes", t_human_output_and_exit_codes),
]


def run():
    failures = []
    for name, fn in TESTS:
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as err:  # a broken test must not abort the rest of the suite
            failures.append((name, err))
            print(f"  FAIL  {name}\n        {type(err).__name__}: {err}")
    print(f"\ndoccheck.py: {len(TESTS) - len(failures)}/{len(TESTS)} tests PASS")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(run())
