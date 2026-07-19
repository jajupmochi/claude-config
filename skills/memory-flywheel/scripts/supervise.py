#!/usr/bin/env python3
# memory-flywheel supervisor · version: 0.1.0
"""The supervising hook that makes the memory flywheel spin AUTOMATICALLY (overhaul task 5).

Design (from docs/strategy/.../00-research.md): the flywheel's fourth layer is a "supervising plugin" that
records each round's VERBATIM raw I/O into the per-project memory without the agent having to call
`mem.py record` by hand. This is that supervisor, wired as a Stop hook.

LLM-as-component: this file is PURE PLUMBING. It reads the Stop payload + the session transcript, extracts the
latest round deterministically, and calls mem.py's record(). No model call. The recorded CONTENT is the
model's own verbatim turn — the model is the content source, never part of the control flow.

SAFETY (this is a live Stop hook):
  - OFF BY DEFAULT. It does nothing unless explicitly enabled (env AGENT_HARNESS_MEM_SUPERVISE=1, or a
    `supervise=on` line in a config file next to the hook). Shipping it disabled means wiring it into
    settings.json is inert until the user opts in.
  - NON-FATAL. Every path is guarded; any error is logged to the memory root's `supervise-errors.log`
    (deploy-context fallback MUST record why it fired — see the repo's fallback-discipline rule) and the
    hook exits 0. It can never break or slow a real turn beyond a bounded transcript read.
  - INTERVAL/DEDUP GUARDED. Records at most once per (session, transcript-state) so re-fired Stop hooks or
    unchanged turns do not spam the memory.

Usage as a Stop hook (NOT auto-wired; document in settings.json when the user opts in):
    command: python3 <this>/supervise.py
    stdin:   Claude Code Stop payload JSON {session_id, transcript_path, cwd}

Also exposes pure helpers for tests: extract_round(messages), should_record(state_dir, sid, token), enabled(env).
"""
import datetime
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# --- pure helpers (no I/O side effects except where noted) --------------------------------------------

_STOP = {"the", "a", "an", "to", "of", "and", "or", "is", "it", "in", "on", "for", "this", "that", "i",
         "you", "we", "with", "as", "at", "be", "by", "from", "so", "do", "did", "can", "will", "the"}


def _text_from_message(msg):
    """Pull plain text out of a Claude-transcript message, tolerating several content shapes."""
    if msg is None:
        return ""
    content = msg.get("content", msg) if isinstance(msg, dict) else msg
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") in (None, "text") and isinstance(b.get("text"), str):
                    parts.append(b["text"])
            elif isinstance(b, str):
                parts.append(b)
        return "\n".join(parts)
    if isinstance(content, dict) and isinstance(content.get("text"), str):
        return content["text"]
    return ""


def _tools_used(messages):
    names = []
    for m in messages:
        msg = m.get("message", m) if isinstance(m, dict) else m
        content = msg.get("content") if isinstance(msg, dict) else None
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name"):
                    names.append(b["name"])
    # de-dupe preserving order
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _keywords(text, k=6):
    toks = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    freq = {}
    for t in toks:
        if t in _STOP:
            continue
        freq[t] = freq.get(t, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]


def extract_round(messages, max_body=8000):
    """From a list of transcript entries, build a verbatim round record for the LATEST exchange.

    Returns {kind, title, body, keywords} or None if there is nothing worth recording.
    Deterministic; no model call.
    """
    if not messages:
        return None
    # normalize: each entry may be {"type","message":{...}} or a bare message
    def role(e):
        return (e.get("type") or (e.get("message", {}) or {}).get("role") or e.get("role") or "") if isinstance(e, dict) else ""

    def body_of(e):
        return _text_from_message(e.get("message", e) if isinstance(e, dict) else e)

    last_user = ""
    for e in reversed(messages):
        if role(e) == "user":
            last_user = body_of(e).strip()
            if last_user:
                break
    last_asst = ""
    for e in reversed(messages):
        if role(e) == "assistant":
            last_asst = body_of(e).strip()
            if last_asst:
                break
    if not last_user and not last_asst:
        return None
    tools = _tools_used(messages)
    title = (last_user.splitlines()[0] if last_user else last_asst.splitlines()[0] if last_asst else "round")
    title = title.strip()[:70] or "round"
    body_parts = []
    if last_user:
        body_parts.append("## User\n" + last_user)
    if last_asst:
        body_parts.append("## Assistant\n" + last_asst)
    if tools:
        body_parts.append("## Tools\n" + ", ".join(tools))
    body = "\n\n".join(body_parts)[:max_body]
    return {"kind": "round", "title": title, "body": body,
            "keywords": ",".join(_keywords(last_user + " " + last_asst))}


def enabled(env=None):
    env = env if env is not None else os.environ
    if env.get("AGENT_HARNESS_MEM_SUPERVISE", "").strip() in ("1", "true", "on", "yes"):
        return True
    conf = os.path.join(HERE, "supervise.conf")
    try:
        with open(conf, encoding="utf-8") as f:
            for line in f:
                if re.match(r"^\s*supervise\s*=\s*(on|1|true|yes)\s*$", line, re.I):
                    return True
    except OSError:
        pass
    return False


def _state_file(state_dir, sid):
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", sid or "nosess")
    return os.path.join(state_dir, f"supervise-{safe}.state")


def should_record(state_dir, sid, token):
    """True unless we already recorded this exact (session, transcript-state) token. Writes nothing."""
    sf = _state_file(state_dir, sid)
    try:
        with open(sf, encoding="utf-8") as f:
            return f.read().strip() != token
    except OSError:
        return True


def _mark_recorded(state_dir, sid, token):
    os.makedirs(state_dir, exist_ok=True)
    with open(_state_file(state_dir, sid), "w", encoding="utf-8") as f:
        f.write(token)


def _load_mem():
    spec = importlib.util.spec_from_file_location("mem", os.path.join(HERE, "mem.py"))
    mem = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mem)
    return mem


class _NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _read_transcript(path, max_lines=4000):
    msgs = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msgs.append(json.loads(line))
            except ValueError:
                continue
    return msgs


def _project_name(cwd):
    name = os.path.basename(os.path.normpath(cwd or os.getcwd())) or "project"
    return re.sub(r"[^A-Za-z0-9._-]", "-", name)


def default_mem_root(payload=None):
    """Where a project's memory lives: inside the project, not in a home directory.

    The memory of a project belongs with that project — it should survive being copied to another
    machine, be visible in a diff, and not accumulate in a hidden home folder no one looks at. This
    mirrors task-ledger, which keeps its round documents in the same `.agent/` folder. Falls back to
    the old ~/.agent-harness/memory only when the payload carries no usable cwd.
    """
    cwd = (payload or {}).get("cwd")
    if cwd and os.path.isdir(cwd):
        return os.path.join(cwd, ".agent", "memory")
    return os.path.join(os.path.expanduser("~"), ".agent-harness", "memory")


def run(payload, mem_root=None, mem=None):
    """Core entry: given a parsed Stop payload, record the latest round. Returns a status string.

    mem_root defaults to <project>/.agent/memory. mem is injectable for tests.
    """
    if not enabled():
        return "disabled"
    root = mem_root or default_mem_root(payload)
    state_dir = os.path.join(root, ".supervise-state")
    sid = str(payload.get("session_id") or "nosess")
    tpath = payload.get("transcript_path")
    if not tpath or not os.path.isfile(tpath):
        return "no-transcript"
    # token = session + transcript size + mtime — cheap "did this turn change?" signal
    st = os.stat(tpath)
    token = hashlib.sha1(f"{sid}:{st.st_size}:{int(st.st_mtime)}".encode()).hexdigest()[:16]
    if not should_record(state_dir, sid, token):
        return "already-recorded"
    msgs = _read_transcript(tpath)
    round_ = extract_round(msgs)
    if not round_:
        return "nothing-to-record"
    mem = mem or _load_mem()
    project = _project_name(payload.get("cwd"))
    args = _NS(root=root, project=project, kind=round_["kind"], title=round_["title"],
               keywords=round_["keywords"], ts=datetime.date.today().isoformat())
    old = sys.stdin
    sys.stdin = io.StringIO(round_["body"])
    try:
        buf = io.StringIO()
        _stdout = sys.stdout
        sys.stdout = buf
        try:
            mem.cmd_record(args)
        finally:
            sys.stdout = _stdout
    finally:
        sys.stdin = old
    _mark_recorded(state_dir, sid, token)
    return f"recorded:{project}"


def main():
    # Stop hooks must never break the turn: swallow everything, log, exit 0.
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0
    try:
        status = run(payload)
        if status not in ("disabled", "already-recorded", "no-transcript", "nothing-to-record") and not status.startswith("recorded"):
            raise RuntimeError(status)
    except Exception as e:  # deploy fallback: record WHY it fired, never crash the turn
        try:
            root = default_mem_root(payload if isinstance(payload, dict) else None)
            os.makedirs(root, exist_ok=True)
            with open(os.path.join(root, "supervise-errors.log"), "a", encoding="utf-8") as f:
                f.write(f"{datetime.datetime.now().isoformat()}\t{type(e).__name__}\t{e}\n")
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
