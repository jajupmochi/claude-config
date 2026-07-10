#!/usr/bin/env python3
"""Tests for supervise.py (memory-flywheel supervising hook). Run: python3 test_supervise.py"""
import importlib.util
import json
import os
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sup = _load("supervise")
mem = _load("mem")

n = 0


def ok(m):
    global n
    n += 1
    print("  ok:", m)


# 1. _text_from_message tolerates the shapes a Claude transcript uses
assert sup._text_from_message("hello") == "hello"
assert sup._text_from_message({"content": "hi"}) == "hi"
assert sup._text_from_message({"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}) == "a\nb"
assert sup._text_from_message({"content": [{"type": "tool_use", "name": "Bash"}]}) == ""  # non-text ignored
ok("_text_from_message handles str / content-str / block-list / non-text")

# 2. extract_round pulls the LATEST user+assistant + tools, deterministically
messages = [
    {"type": "user", "message": {"role": "user", "content": "old question"}},
    {"type": "assistant", "message": {"role": "assistant", "content": "old answer"}},
    {"type": "user", "message": {"role": "user", "content": "deploy the widget pipeline please"}},
    {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "done deploying"},
        {"type": "tool_use", "name": "Bash"},
        {"type": "tool_use", "name": "Edit"},
    ]}},
]
r = sup.extract_round(messages)
assert r is not None
assert r["title"] == "deploy the widget pipeline please", r["title"]
assert "## User\ndeploy the widget pipeline" in r["body"], r["body"]
assert "done deploying" in r["body"]
assert "Bash, Edit" in r["body"], r["body"]
assert "old question" not in r["body"], "must record only the LATEST round"
assert "deploy" in r["keywords"] and "widget" in r["keywords"], r["keywords"]
ok("extract_round: latest round only, verbatim body, tools, keywords")

# 3. empty / no-text -> None
assert sup.extract_round([]) is None
assert sup.extract_round([{"type": "user", "message": {"content": ""}}]) is None
ok("extract_round: empty -> None")

# 4. enabled() honors env and defaults off
assert sup.enabled({"AGENT_HARNESS_MEM_SUPERVISE": "1"}) is True
assert sup.enabled({"AGENT_HARNESS_MEM_SUPERVISE": "on"}) is True
assert sup.enabled({}) is False  # off by default (no conf file present in a clean env)
ok("enabled(): env on/off, default OFF")

# 5. should_record / _mark_recorded dedup by token
with tempfile.TemporaryDirectory() as sd:
    assert sup.should_record(sd, "s1", "tokA") is True
    sup._mark_recorded(sd, "s1", "tokA")
    assert sup.should_record(sd, "s1", "tokA") is False, "same token must be deduped"
    assert sup.should_record(sd, "s1", "tokB") is True, "new token records again"
    assert sup.should_record(sd, "s2", "tokA") is True, "different session records"
ok("should_record/_mark_recorded: per-(session,token) dedup")

# 6. run() end-to-end: enabled + real transcript + temp mem_root -> writes a round via mem.cmd_record
with tempfile.TemporaryDirectory() as root:
    tp = os.path.join(root, "transcript.jsonl")
    with open(tp, "w", encoding="utf-8") as f:
        for m in messages:
            f.write(json.dumps(m) + "\n")
    payload = {"session_id": "sess-xyz", "transcript_path": tp, "cwd": "/tmp/myproj"}
    os.environ["AGENT_HARNESS_MEM_SUPERVISE"] = "1"
    try:
        status = sup.run(payload, mem_root=root, mem=mem)
        assert status == "recorded:myproj", status
        # a round file exists under the project, with the verbatim body
        rounds = os.path.join(root, "myproj", "rounds")
        files = os.listdir(rounds)
        assert len(files) == 1, files
        content = open(os.path.join(rounds, files[0]), encoding="utf-8").read()
        assert "deploy the widget pipeline" in content and "done deploying" in content
        assert "kind: round" in content
        # INDEX.md was refreshed by mem.cmd_record -> cmd_index
        assert os.path.isfile(os.path.join(root, "myproj", "INDEX.md"))
        # second run with the SAME transcript state -> deduped
        status2 = sup.run(payload, mem_root=root, mem=mem)
        assert status2 == "already-recorded", status2
        assert len(os.listdir(rounds)) == 1, "must not double-record an unchanged turn"
    finally:
        del os.environ["AGENT_HARNESS_MEM_SUPERVISE"]
ok("run(): records verbatim round + index, then dedups the unchanged turn")

# 7. run() is safe/no-op when disabled or transcript missing
assert sup.run({"session_id": "s", "transcript_path": "/no/such"}, mem_root=tempfile.gettempdir()) == "disabled"
os.environ["AGENT_HARNESS_MEM_SUPERVISE"] = "1"
try:
    assert sup.run({"session_id": "s", "transcript_path": "/no/such/file.jsonl"}, mem=mem) == "no-transcript"
finally:
    del os.environ["AGENT_HARNESS_MEM_SUPERVISE"]
ok("run(): disabled -> no-op; missing transcript -> no-transcript (never raises)")

print(f"\nsupervise.py: all {n} checks PASS")
