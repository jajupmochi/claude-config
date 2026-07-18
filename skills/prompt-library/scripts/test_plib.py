#!/usr/bin/env python3
"""Tests for plib.py + plib_mine.py (prompt-library, privacy-gated). Run: python3 test_plib.py

The miner tests build SYNTHETIC history files in a tempdir and point the extractors at it — they never
read the machine's real Claude / Codex / Copilot / opencode history."""
import importlib.util
import io
import json
import os
import sqlite3
import tempfile
from contextlib import redirect_stdout, redirect_stderr

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


plib = _load("plib")
mine = _load("plib_mine")


def _run(argv, stdin=""):
    import sys
    old = sys.stdin
    sys.stdin = io.StringIO(stdin)
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            rc = plib.main(argv)
    finally:
        sys.stdin = old
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------- store (v1 behaviour, unchanged)

def test_store():
    # privacy_scan unit checks (extra=[] so no local private-terms file leaks into the test)
    assert plib.privacy_scan("clean reusable prompt about dashboards", extra=[]) == []
    assert any(l == "absolute home path" for l, _ in plib.privacy_scan("see /home/bob/x", extra=[]))
    assert any(l == "email address" for l, _ in plib.privacy_scan("mail me a@b.com", extra=[]))
    # user-specific terms come from the caller / local file, not shipped literals:
    assert any(l == "private term" for l, _ in plib.privacy_scan("reuse the ZZCODENAME brief", extra=["ZZCODENAME"]))

    with tempfile.TemporaryDirectory() as root:
        base = ["--root", root]

        # 1. add a CLEAN prompt -> stored + indexed
        rc, out, err = _run(["add", *base, "--title", "Redesign a dashboard", "--scenarios", "ui,redesign",
                             "--source", "claude-code", "--tags", "design"],
                            stdin="You are redesigning a data dashboard. Produce N rounds, each a full mock.\n")
        assert rc == 0, f"clean add should succeed: {err}"
        p = out.strip()
        assert os.path.basename(p) == "redesign-a-dashboard.md"
        assert "You are redesigning a data dashboard" in open(p, encoding="utf-8").read()
        idx = open(os.path.join(root, "INDEX.md"), encoding="utf-8").read()
        assert "Redesign a dashboard" in idx and "ui,redesign" in idx

        # 2. add a prompt with an absolute path -> REFUSED, not stored
        rc, out, err = _run(["add", *base, "--title", "Bad one"],
                            stdin="run the script at /home/someone/secret/run.sh\n")
        assert rc == 1 and "REFUSED" in err and "absolute home path" in err
        assert not os.path.exists(os.path.join(root, "prompts", "bad-one.md")), "refused prompt not written"

        # 3. refuse on email; and on a user-specific private term loaded from a LOCAL file (env-pointed)
        rc, _, err = _run(["add", *base, "--title", "E"], stdin="ping me at foo@bar.com\n")
        assert rc == 1 and "email" in err
        tf = os.path.join(root, "terms.txt")
        open(tf, "w").write("# my private terms\nZZCODENAME\n")
        os.environ["PLIB_PRIVATE_TERMS"] = tf
        try:
            rc, _, err = _run(["add", *base, "--title", "C"], stdin="reuse the ZZCODENAME prompt\n")
            assert rc == 1 and "private term" in err, f"local private term must block: {err}"

            # 4. private content in the TITLE is also caught (term in title, clean body)
            rc, _, err = _run(["add", *base, "--title", "ZZCODENAME playbook"], stdin="totally clean body\n")
            assert rc == 1 and "private term" in err
        finally:
            del os.environ["PLIB_PRIVATE_TERMS"]

        # 5. scan command: exit 1 on private, 0 on clean
        rc, _, _ = _run(["scan"], stdin="/media/disk/x\n")
        assert rc == 1
        rc, _, _ = _run(["scan"], stdin="a perfectly clean line\n")
        assert rc == 0

        # 6. find ranks by keyword
        _run(["add", *base, "--title", "Write release notes", "--scenarios", "docs"],
             stdin="Draft concise release notes from the git log.\n")
        rc, out, _ = _run(["find", *base, "--query", "dashboard"])
        lines = [ln for ln in out.strip().splitlines() if ln]
        assert lines and lines[0].endswith("redesign-a-dashboard.md"), f"find top, got {out!r}"
    return 6


# ---------------------------------------------------------------- v2 schema

def test_schema_v2():
    with tempfile.TemporaryDirectory() as root:
        base = ["--root", root]

        # 7. all four sections + the new frontmatter round-trip through add
        rc, out, err = _run(["add", *base, "--title", "Batch brief", "--scenarios", "spec,planning",
                             "--tags", "brief", "--source", "claude-code", "--session", "abc123",
                             "--date", "2026-07-18",
                             "--optimized", "Do X, then Y. Report per item.",
                             "--when", "Use when several unrelated changes pile up.\n\n- second paragraph",
                             "--when-not", "Skip it when the items are sequential."], stdin="original text here")
        assert rc == 0, err
        text = open(out.strip(), encoding="utf-8").read()
        fm, body = plib._fm(text)
        assert fm["session"] == "abc123" and fm["date"] == "2026-07-18" and fm["tags"] == "brief"
        sec = plib.split_sections(body)
        assert sec["Original"].strip().splitlines()[1] == "original text here"
        assert "Do X, then Y" in sec["Optimized"]
        assert sec["When to use"].startswith("Use when several")
        assert sec["When NOT to use"].startswith("Skip it when")
        # the `> purpose` line is the first SENTENCE of When-to-use, unwrapped, not a cut-off line
        assert "> Use when several unrelated changes pile up." in text

        # 8. optional sections are omitted rather than left empty
        rc, out, _ = _run(["add", *base, "--title", "Bare"], stdin="just an original")
        assert rc == 0
        bare = open(out.strip(), encoding="utf-8").read()
        assert "## Original" in bare and "## Optimized" not in bare and "## When NOT to use" not in bare

        # 9. the privacy gate covers the NEW fields too, not just stdin
        for flag, payload in (("--optimized", "ssh into /home/bob/prod"),
                              ("--when", "email me at a@b.com"),
                              ("--when-not", "token ghp_abcdef123456")):
            rc, _, err = _run(["add", *base, "--title", "Leaky", flag, payload], stdin="clean original")
            assert rc == 1 and "REFUSED" in err, f"{flag} must be scanned: {err}"
            assert not os.path.exists(os.path.join(root, "prompts", "leaky.md"))

        # 10. a prompt containing ``` fences and a literal section heading still parses
        tricky = "Write a README:\n\n```python\nprint('## Original')\n```\n\n## Original\nnot a heading\n"
        rc, out, _ = _run(["add", *base, "--title", "Tricky", "--optimized", "opt body"], stdin=tricky)
        assert rc == 0
        sec = plib.split_sections(plib._fm(open(out.strip(), encoding="utf-8").read())[1])
        assert "not a heading" in sec["Original"] and sec["Optimized"].strip().splitlines()[1] == "opt body"

        # 11. v1 files (bare body, no sections) still read: whole body is the Original
        v1 = "---\ntitle: Old\nscenarios: x\nsource: s\ntags: t\n---\nplain v1 body\n"
        open(os.path.join(root, "prompts", "old.md"), "w", encoding="utf-8").write(v1)
        assert plib.split_sections(plib._fm(v1)[1])["Original"] == "plain v1 body"
        rc, _, _ = _run(["index", *base])
        assert rc == 0 and "Old" in open(os.path.join(root, "INDEX.md"), encoding="utf-8").read()

        # 12. text flags accept @path
        src = os.path.join(root, "opt.txt")
        open(src, "w", encoding="utf-8").write("loaded from a file")
        rc, out, _ = _run(["add", *base, "--title", "From file", "--optimized", f"@{src}"], stdin="orig")
        assert rc == 0 and "loaded from a file" in open(out.strip(), encoding="utf-8").read()
    return 6


# ---------------------------------------------------------------- miner fixtures

def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _jsonl(path, records):
    _write(path, "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records))


LONG = ("Design the whole reporting subsystem. " + "Cover the schema, the API and the tests. " * 4).strip()
LONG2 = ("Write the onboarding guide for new contributors. " + "Explain setup, layout and review. " * 4).strip()


def _ms(iso):
    """'2026-06-15T10:00:00' -> ms epoch, so fixtures and date assertions cannot drift apart."""
    from datetime import datetime, timezone
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp() * 1000)


def _fixture_home(base):
    """Six synthetic history stores, one per supported source, mirroring the real on-disk formats."""
    # claude history.jsonl (ms epoch)
    _jsonl(os.path.join(base, ".claude", "history.jsonl"), [
        {"display": LONG, "project": "/w/proj", "sessionId": "s1", "timestamp": _ms("2026-06-15T10:00:00")},
        {"display": "ok", "project": "/w/proj", "sessionId": "s1",
         "timestamp": _ms("2026-06-15T10:00:01")},                                                # too short
        {"display": "/compact now please, and then keep going with the plan", "project": "/w/proj",
         "sessionId": "s1", "timestamp": _ms("2026-06-15T10:00:02")},                             # slash command
    ])
    # claude transcripts: one keeper + one of every drop rule
    _jsonl(os.path.join(base, ".claude", "projects", "-w-proj", "sess.jsonl"), [
        {"type": "user", "cwd": "/w/proj", "sessionId": "s2", "timestamp": "2026-06-15T10:00:00.000Z",
         "entrypoint": "cli", "message": {"role": "user", "content": [{"type": "text", "text": LONG2}]}},
        {"type": "user", "timestamp": "2026-06-15T10:01:00.000Z", "isMeta": True,
         "message": {"role": "user", "content": "meta " + LONG}},
        {"type": "user", "timestamp": "2026-06-15T10:02:00.000Z", "toolUseResult": {"ok": 1},
         "message": {"role": "user", "content": "tool result " + LONG}},
        {"type": "user", "timestamp": "2026-06-15T10:03:00.000Z", "promptSource": "sdk",
         "message": {"role": "user", "content": "sdk " + LONG}},
        {"type": "user", "timestamp": "2026-06-15T10:04:00.000Z", "isCompactSummary": True,
         "message": {"role": "user", "content": "This session is being continued. " + LONG}},
        {"type": "user", "timestamp": "2026-06-15T10:05:00.000Z", "isSidechain": True,
         "message": {"role": "user", "content": "sidechain " + LONG}},
        {"type": "user", "timestamp": "2026-06-15T10:06:00.000Z", "entrypoint": "sdk-cli",
         "message": {"role": "user", "content": "programmatic " + LONG}},
        {"type": "user", "timestamp": "2026-06-15T10:07:00.000Z",
         "message": {"role": "user", "content": "<system-reminder> " + LONG}},
        {"type": "assistant", "timestamp": "2026-06-15T10:08:00.000Z",
         "message": {"role": "assistant", "content": "not a user turn " + LONG}},
    ])
    # a subagent transcript must be skipped entirely
    _jsonl(os.path.join(base, ".claude", "projects", "-w-proj", "subagents", "sub.jsonl"), [
        {"type": "user", "timestamp": "2026-06-15T11:00:00.000Z",
         "message": {"role": "user", "content": "subagent " + LONG}},
    ])
    # codex: session_meta carries cwd; history replays and IDE context are dropped
    _jsonl(os.path.join(base, ".codex", "sessions", "2026", "06", "r.jsonl"), [
        {"type": "session_meta", "timestamp": "2026-06-16T09:00:00.000Z", "payload": {"cwd": "/w/codex"}},
        {"type": "event_msg", "timestamp": "2026-06-16T09:01:00.000Z",
         "payload": {"type": "user_message", "message": "Refactor the loader. " + LONG}},
        {"type": "event_msg", "timestamp": "2026-06-16T09:02:00.000Z",
         "payload": {"type": "user_message", "message": "The following is the Codex agent history" + LONG}},
        {"type": "event_msg", "timestamp": "2026-06-16T09:03:00.000Z",
         "payload": {"type": "user_message", "message": "# Context from my IDE" + LONG}},
        {"type": "response_item", "timestamp": "2026-06-16T09:04:00.000Z", "payload": {"type": "message"}},
    ])
    # copilot CLI: events.jsonl (+ workspace.yaml cwd) and the JetBrains partition file
    _write(os.path.join(base, ".copilot", "session-state", "cs1", "workspace.yaml"),
           "id: cs1\ncwd: /w/copilot\nbranch: main\n")
    _jsonl(os.path.join(base, ".copilot", "session-state", "cs1", "events.jsonl"), [
        {"type": "user.message", "timestamp": "2026-06-17T08:00:00.000Z", "data": {"content": "Add caching. " + LONG}},
        {"type": "user.message_rendered", "timestamp": "2026-06-17T08:01:00.000Z",
         "data": {"content": "duplicate render " + LONG}},
        {"type": "assistant.message", "timestamp": "2026-06-17T08:02:00.000Z", "data": {"content": LONG}},
    ])
    _jsonl(os.path.join(base, ".copilot", "jb", "jb1", "partition-1.jsonl"), [
        {"type": "user.message", "timestamp": "2026-06-17T09:00:00.000Z", "data": {"content": "Port the plugin. " + LONG}},
    ])
    # VS Code chat: incremental op-log, kind 0 seeds and kind 2 on ["requests"] appends
    _write(os.path.join(base, ".config", "Code", "User", "workspaceStorage", "ws1", "workspace.json"),
           json.dumps({"folder": "file:///w/vscode"}))
    _jsonl(os.path.join(base, ".config", "Code", "User", "workspaceStorage", "ws1", "chatSessions", "c.jsonl"), [
        {"kind": 0, "v": {"requests": [{"timestamp": _ms("2026-06-18T08:00:00"),
                                        "message": {"text": "Seeded request. " + LONG}}]}},
        {"kind": 2, "k": ["requests"], "v": [{"timestamp": _ms("2026-06-18T08:10:00"),
                                             "message": {"text": "Appended request. " + LONG}}]},
        {"kind": 1, "k": ["requests", 0, "promptTokens"], "v": 42},
        {"kind": 2, "k": ["requests", 0, "response"], "v": [{"value": "ignored"}]},
    ])
    # opencode SQLite
    db = os.path.join(base, ".local", "share", "opencode", "opencode.db")
    os.makedirs(os.path.dirname(db), exist_ok=True)
    con = sqlite3.connect(db)
    con.executescript("""
        CREATE TABLE session (id TEXT PRIMARY KEY, directory TEXT);
        CREATE TABLE message (id TEXT PRIMARY KEY, session_id TEXT, time_created INTEGER, data TEXT);
        CREATE TABLE part (id TEXT PRIMARY KEY, message_id TEXT, session_id TEXT, data TEXT);
    """)
    con.execute("INSERT INTO session VALUES ('sx','/w/opencode')")
    con.execute("INSERT INTO message VALUES ('m1','sx',?,?)",
                (_ms("2026-06-19T07:00:00"), json.dumps({"role": "user", "time": {"created": _ms("2026-06-19T07:00:00")}})))
    con.execute("INSERT INTO message VALUES ('m2','sx',?,?)",
                (_ms("2026-06-19T07:05:00"), json.dumps({"role": "assistant", "time": {"created": _ms("2026-06-19T07:05:00")}})))
    con.execute("INSERT INTO part VALUES ('p1','m1','sx',?)",
                (json.dumps({"type": "text", "text": "Set up the docs site. " + LONG}),))
    con.execute("INSERT INTO part VALUES ('p2','m2','sx',?)",
                (json.dumps({"type": "text", "text": "assistant reply " + LONG}),))
    con.commit()
    con.close()


def test_extractors():
    with tempfile.TemporaryDirectory() as home:
        _fixture_home(home)

        # 13. every source extracts exactly its real user prompts, with project + timestamp attached
        h = list(mine.iter_claude_history(home))
        assert [c["text"] for c in h][0] == LONG and h[0]["project"] == "/w/proj" and h[0]["date"] == "2026-06-15"

        t = list(mine.iter_claude_transcripts(home))
        assert len(t) == 1, [c["text"][:30] for c in t]          # only the genuine typed turn survives
        assert t[0]["text"] == LONG2 and t[0]["project"] == "/w/proj"
        assert not any("subagent" in c["text"] for c in t), "subagents/ must be skipped"
        for dropped in ("meta ", "tool result ", "sdk ", "This session is being continued",
                        "sidechain ", "programmatic ", "not a user turn ", "<system-reminder"):
            assert not any(c["text"].startswith(dropped) for c in t), f"{dropped!r} must be dropped"

        c = list(mine.iter_codex(home))
        assert len(c) == 1 and c[0]["project"] == "/w/codex" and c[0]["text"].startswith("Refactor")

        p = list(mine.iter_copilot_cli(home))
        assert len(p) == 2, [x["text"][:20] for x in p]           # message_rendered + assistant dropped
        assert {x["project"] for x in p} == {"/w/copilot", ""}    # workspace.yaml cwd; jb has none

        v = list(mine.iter_copilot_vscode(home))
        assert [x["text"][:8] for x in v] == ["Seeded r", "Appended"], "op-log replay"
        assert v[0]["project"] == "/w/vscode"

        o = list(mine.iter_opencode(home))
        assert len(o) == 1 and o[0]["project"] == "/w/opencode" and o[0]["text"].startswith("Set up")

        # 14. a missing source is silently empty, not an exception
        with tempfile.TemporaryDirectory() as empty:
            assert all(list(fn(empty)) == [] for fn in mine.SOURCES.values())

        # 15. source name resolution, including aliases and the unknown-name error
        assert mine.resolve_sources("claude") == ["claude-history", "claude-transcripts"]
        assert mine.resolve_sources("codex,codex") == ["codex"]
        assert set(mine.resolve_sources("all")) == set(mine.SOURCES)
        try:
            mine.resolve_sources("nope")
            raise AssertionError("unknown source must raise")
        except ValueError:
            pass
    return 3


def test_filter_and_score():
    # 16. noise filter: slash commands, XML scaffolding, bare acknowledgements, pasted errors
    for noisy in ("/compact", "<task-notification> <task-id>x</task-id>", "<task_description> do it",
                  "ok", "继续", "Traceback (most recent call last):\n  File \"x\""):
        assert mine.is_noise(noisy), noisy
    for real in (LONG, "Write the migration plan as a table.", "1. do this\n2. do that"):
        assert not mine.is_noise(real), real

    # 17. scoring: a structured, reusable brief must outrank a one-off, and one-off markers are reported
    reusable = ("Design the release checklist.\n\n"
                "- The build must be reproducible\n- Each step must be verifiable\n- Output a table\n\n"
                "Report what you could not verify rather than assuming it passed.")
    oneoff = "fix line 42 in /home/bob/app/main.py, the traceback above shows it"
    rs, rflags = mine.signals(reusable)
    os_, oflags = mine.signals(oneoff)
    assert sum(rs.values()) > sum(os_.values()), (rs, os_)
    assert rflags == [] and {"abs-path", "line-ref", "filename"} <= set(oflags), oflags
    assert rs["structure"] > 0 and rs["imperative"] > 0

    # 18. recurrence: near-identical texts find each other, a lone text finds nobody
    twins = [{"text": f"Write the {w} onboarding guide covering setup, layout, review and release."}
             for w in ("alpha", "beta", "gamma")]
    cands = twins + [{"text": "Completely unrelated: benchmark the sqlite writer against duckdb."}]
    nb = mine.recurrence_neighbours(cands, min_shared=2)
    assert all(n >= 2 for n in nb[:3]) and nb[3] == 0, nb
    return 3


def test_pipeline():
    with tempfile.TemporaryDirectory() as home:
        _fixture_home(home)
        names = list(mine.SOURCES)

        # 19. full pipeline: scored, ranked, every source represented, filters applied
        cands, counts = mine.mine(names, base=home)
        assert counts == {"claude-history": 1, "claude-transcripts": 1, "codex": 1,
                          "copilot-cli": 2, "copilot-vscode": 2, "opencode": 1}, counts
        assert [c["rank"] for c in cands] == list(range(1, len(cands) + 1))
        assert all(c["score"] == round(sum(c["signals"].values()), 2) for c in cands)
        assert cands == sorted(cands, key=lambda c: -c["score"]), "ranked by score"

        # 20. --since and --min-len actually filter
        assert mine.mine(names, since="2026-06-16", base=home)[1]["claude-history"] == 0
        assert mine.mine(names, min_len=10 ** 6, base=home)[0] == []
        assert len(mine.mine(names, limit=2, base=home)[0]) == 2

        # 21. de-duplication: same event through two sources collapses on (second, text hash);
        #     the same text at a DIFFERENT time survives as one candidate with occurrences=2
        first = _ms("2026-06-15T10:00:00")
        _jsonl(os.path.join(home, ".claude", "history.jsonl"), [
            {"display": LONG, "project": "/w", "sessionId": "s", "timestamp": first},
            {"display": LONG, "project": "/w", "sessionId": "s", "timestamp": first + 400},   # same second
            {"display": LONG, "project": "/w", "sessionId": "s", "timestamp": first + 90000},  # later
        ])
        cands, counts = mine.mine(["claude-history"], base=home)
        assert counts["claude-history"] == 2, counts          # 3 rows, 2 distinct (second, hash) events
        assert len(cands) == 1 and cands[0]["occurrences"] == 2, cands
        assert cands[0]["ts"] == first // 1000, "keeps the earliest sighting"
    return 3


def test_mine_command():
    with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as work:
        _fixture_home(home)
        root = os.path.join(work, "lib")
        out = os.path.join(work, "candidates")
        real_home, os.environ["HOME"] = os.environ.get("HOME", ""), home
        try:
            # 22. mine writes candidates.jsonl + REVIEW.md and prints per-source counts to stderr
            rc, stdout, err = _run(["mine", "--root", root, "--source", "claude,codex", "--out", out])
            assert rc == 0, err
            rows = [json.loads(l) for l in open(os.path.join(out, "candidates.jsonl"), encoding="utf-8")]
            assert rows and all({"rank", "score", "signals", "flags", "privacy", "text"} <= set(r) for r in rows)
            assert "claude-history\t1" in err and "codex\t1" in err
            assert "## Ranked candidates" in open(os.path.join(out, "REVIEW.md"), encoding="utf-8").read()
            assert stdout.strip().endswith("candidates.jsonl")

            # 23. the privacy gate runs over every mined candidate so curation can see what to strip
            _jsonl(os.path.join(home, ".claude", "history.jsonl"),
                   [{"display": "Deploy from /home/bob/app and mail ops@corp.com. " + LONG,
                     "project": "/w", "sessionId": "s", "timestamp": _ms("2026-06-15T10:00:00")}])
            _run(["mine", "--root", root, "--source", "claude-history", "--out", out])
            rows = [json.loads(l) for l in open(os.path.join(out, "candidates.jsonl"), encoding="utf-8")]
            assert rows[0]["privacy"] == ["absolute home path", "email address"], rows[0]["privacy"]

            # 24. raw mined text may NOT be written into the publishable library
            rc, _, err = _run(["mine", "--root", root, "--source", "codex",
                               "--out", os.path.join(root, "prompts")])
            assert rc == 2 and "refusing" in err, err
            rc, _, err = _run(["mine", "--root", root, "--source", "bogus", "--out", out])
            assert rc == 2 and "unknown source" in err
        finally:
            os.environ["HOME"] = real_home
    return 3


def main():
    total = 0
    for fn in (test_store, test_schema_v2, test_extractors, test_filter_and_score, test_pipeline, test_mine_command):
        total += fn()
    print(f"plib.py + plib_mine.py: all {total} tests PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
