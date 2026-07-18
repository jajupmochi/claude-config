#!/usr/bin/env python3
# prompt-library · version: 0.2.0
"""Mine reusable-prompt CANDIDATES out of local agent histories. Read-only, dependency-free.

Called by `plib.py mine`. It emits CANDIDATES for a human or an agent to curate — it deliberately does
NOT publish, because writing the optimized variant and the when-to-use notes needs judgement, and the
raw mined text still carries absolute paths, usernames and project codenames.

Sources (each recipe verified against the on-disk format):

  claude-history      ~/.claude/history.jsonl
                      one JSON per line: `display` (prompt), `project` (cwd), `sessionId`, `timestamp` (ms).
  claude-transcripts  ~/.claude/projects/*/*.jsonl, excluding */subagents/*
                      keep type=="user" and message.role=="user"; drop toolUseResult / isMeta entries,
                      drop promptSource in ("sdk","system"). NOTE promptSource did not exist before
                      2026-06, so its ABSENCE must not be read as machine-generated — `entrypoint`
                      does cover the whole range and is what actually separates a typed prompt from a
                      programmatic one. Also drops isCompactSummary (Claude Code's own
                      continued-from-a-previous-conversation summary) and isSidechain turns.
  codex               ~/.codex/sessions/**/*.jsonl
                      first line type=="session_meta" carries payload.cwd; prompts are type=="event_msg"
                      with payload.type=="user_message", text at payload.message. Most entries are
                      history REPLAYS ("The following is the Codex agent history") and are dropped.
  copilot-cli         ~/.copilot/session-state/*/events.jsonl and ~/.copilot/jb/*/partition-1.jsonl
                      type=="user.message", text at data.content ("user.message_rendered" is a duplicate).
  copilot-vscode      ~/.config/Code/User/workspaceStorage/*/chatSessions/*.jsonl
                      incremental op-log: kind==0 is a base snapshot at v.requests, later {kind:2,
                      k:["requests"], v:[...]} lines append. Prompt text at requests[i].message.text.
  opencode            ~/.local/share/opencode/opencode.db (SQLite, opened READ-ONLY)
                      part -> message -> session where message role=="user" and part type=="text".

Ranking: a mined prompt is worth curating when it is REUSABLE, i.e. it specifies a repeatable piece of
work rather than a one-off ("fix line 42"). `score_all` combines five computable signals — length,
structure, imperative phrasing, generality (absence of one-off identifiers) and recurrence of similar
prompts — and emits the components so a curator can see why something ranked where it did.
"""
import glob
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

MAX_TEXT = 20000  # cap a single candidate; a longer paste is a document, not a prompt

# ---------------------------------------------------------------- helpers

def _home(*parts):
    return os.path.join(os.path.expanduser("~"), *parts)


def _iso(ms):
    """ms epoch -> aware UTC datetime (None when unparseable)."""
    try:
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _parse_iso(s):
    """ISO-8601 (with Z or offset) -> aware UTC datetime (None when unparseable)."""
    if not isinstance(s, str) or not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _jsonl(path):
    """Yield parsed objects from a .jsonl file, skipping blank/corrupt lines."""
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict):
                yield obj


def _cand(text, source, project, session, dt):
    """Build a raw candidate record, or None when the text is unusable."""
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not text:
        return None
    truncated = len(text) > MAX_TEXT
    return {
        "text": text[:MAX_TEXT],
        "truncated": truncated,
        "source": source,
        "project": project or "",
        "session": session or "",
        "ts": int(dt.timestamp()) if dt else 0,
        "date": dt.date().isoformat() if dt else "",
    }


# ---------------------------------------------------------------- extractors

def iter_claude_history(base=None):
    path = os.path.join(base, ".claude", "history.jsonl") if base else _home(".claude", "history.jsonl")
    for d in _jsonl(path):
        c = _cand(d.get("display"), "claude-history", d.get("project"), d.get("sessionId"), _iso(d.get("timestamp")))
        if c:
            yield c


# Markers of machine-generated / harness text that is echoed into the user turn.
_TRANSCRIPT_NOISE = ("<command-name", "<local-command-stdout", "<system-reminder", "Caveat:", "[Request interrupted")
# `entrypoint` values that mean "a program issued this prompt", not "a human typed it". Unlike
# promptSource this field is present across the whole history, so it catches SDK turns from before
# promptSource existed (in this machine's history, 331 such turns in 2026-05 alone).
_SDK_ENTRYPOINTS = {"sdk-cli"}


def _msg_text(message):
    """message.content is either a plain string or a list of content blocks."""
    if isinstance(message, str):
        return message
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def iter_claude_transcripts(base=None):
    root = os.path.join(base, ".claude", "projects") if base else _home(".claude", "projects")
    for path in sorted(glob.glob(os.path.join(root, "*", "**", "*.jsonl"), recursive=True)):
        if f"{os.sep}subagents{os.sep}" in path:
            continue
        session = os.path.splitext(os.path.basename(path))[0]
        for d in _jsonl(path):
            if d.get("type") != "user" or d.get("isMeta") or d.get("toolUseResult") is not None:
                continue
            message = d.get("message") or {}
            if not isinstance(message, dict) or message.get("role") != "user":
                continue
            # promptSource only exists from 2026-06 onward: a MISSING value is a real user prompt.
            if d.get("promptSource") in ("sdk", "system"):
                continue
            # isCompactSummary: Claude Code's own "continued from a previous conversation" summary.
            # isSidechain: a subagent turn that landed outside subagents/.
            if d.get("isCompactSummary") or d.get("isSidechain") or d.get("entrypoint") in _SDK_ENTRYPOINTS:
                continue
            text = _msg_text(message).strip()
            if not text or text.startswith(_TRANSCRIPT_NOISE):
                continue
            c = _cand(text, "claude-transcripts", d.get("cwd"), d.get("sessionId") or session, _parse_iso(d.get("timestamp")))
            if c:
                yield c


# 710 of 792 Codex user_message entries are the agent replaying its own history into a fresh turn.
_CODEX_NOISE = ("The following is the Codex agent history", "# Context from my IDE")


def iter_codex(base=None):
    root = os.path.join(base, ".codex", "sessions") if base else _home(".codex", "sessions")
    for path in sorted(glob.glob(os.path.join(root, "**", "*.jsonl"), recursive=True)):
        cwd, session = "", os.path.splitext(os.path.basename(path))[0]
        for d in _jsonl(path):
            payload = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            if d.get("type") == "session_meta":
                cwd = payload.get("cwd") or cwd
                continue
            if d.get("type") != "event_msg" or payload.get("type") != "user_message":
                continue
            text = (payload.get("message") or "").strip()
            if not text or text.startswith(_CODEX_NOISE):
                continue
            c = _cand(text, "codex", cwd, session, _parse_iso(d.get("timestamp")))
            if c:
                yield c


def _copilot_cwd(session_dir):
    """~/.copilot/session-state/<id>/workspace.yaml carries `cwd: <path>` (flat YAML, so a line read is enough)."""
    path = os.path.join(session_dir, "workspace.yaml")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("cwd:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return ""


def iter_copilot_cli(base=None):
    root = os.path.join(base, ".copilot") if base else _home(".copilot")
    files = [(p, _copilot_cwd(os.path.dirname(p))) for p in sorted(glob.glob(os.path.join(root, "session-state", "*", "events.jsonl")))]
    files += [(p, "") for p in sorted(glob.glob(os.path.join(root, "jb", "*", "partition-1.jsonl")))]
    for path, cwd in files:
        session = os.path.basename(os.path.dirname(path))
        for d in _jsonl(path):
            # "user.message_rendered" carries the same content wrapped in harness scaffolding — skip it.
            if d.get("type") != "user.message":
                continue
            data = d.get("data") if isinstance(d.get("data"), dict) else {}
            c = _cand(data.get("content"), "copilot-cli", cwd, session, _parse_iso(d.get("timestamp")))
            if c:
                yield c


def _vscode_folder(storage_dir):
    try:
        with open(os.path.join(storage_dir, "workspace.json"), encoding="utf-8") as f:
            return (json.load(f).get("folder") or "").replace("file://", "")
    except (OSError, ValueError, AttributeError):
        return ""


def iter_copilot_vscode(base=None):
    root = os.path.join(base, ".config", "Code", "User", "workspaceStorage") if base else _home(".config", "Code", "User", "workspaceStorage")
    for path in sorted(glob.glob(os.path.join(root, "*", "chatSessions", "*.jsonl"))):
        folder = _vscode_folder(os.path.dirname(os.path.dirname(path)))
        session = os.path.splitext(os.path.basename(path))[0]
        requests = []
        for d in _jsonl(path):  # replay the op-log: kind 0 seeds, kind 2 on ["requests"] appends
            if d.get("kind") == 0:
                v = d.get("v")
                requests = list(v.get("requests") or []) if isinstance(v, dict) else []
            elif d.get("kind") == 2 and d.get("k") == ["requests"] and isinstance(d.get("v"), list):
                requests.extend(d["v"])
        for r in requests:
            if not isinstance(r, dict):
                continue
            c = _cand((r.get("message") or {}).get("text"), "copilot-vscode", folder, session, _iso(r.get("timestamp")))
            if c:
                yield c


OPENCODE_SQL = """
SELECT json_extract(p.data,'$.text'), s.directory, m.session_id,
       COALESCE(json_extract(m.data,'$.time.created'), m.time_created)
  FROM part p
  JOIN message m ON p.message_id = m.id
  JOIN session s ON m.session_id = s.id
 WHERE json_extract(m.data,'$.role') = 'user'
   AND json_extract(p.data,'$.type') = 'text'
"""


def iter_opencode(base=None):
    db = os.path.join(base, ".local", "share", "opencode", "opencode.db") if base else _home(".local", "share", "opencode", "opencode.db")
    if not os.path.isfile(db):
        return
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)  # read-only: never touch the user's live DB
    try:
        rows = con.execute(OPENCODE_SQL).fetchall()
    except sqlite3.Error as e:
        print(f"plib mine: opencode DB unreadable ({e})", file=sys.stderr)
        return
    finally:
        con.close()
    for text, directory, session, created in rows:
        c = _cand(text, "opencode", directory, session, _iso(created))
        if c:
            yield c


SOURCES = {
    "claude-history": iter_claude_history,
    "claude-transcripts": iter_claude_transcripts,
    "codex": iter_codex,
    "copilot-cli": iter_copilot_cli,
    "copilot-vscode": iter_copilot_vscode,
    "opencode": iter_opencode,
}
# Friendly aliases so `--source claude,copilot` does the obvious thing.
ALIASES = {
    "claude": ["claude-history", "claude-transcripts"],
    "copilot": ["copilot-cli", "copilot-vscode"],
    "all": list(SOURCES),
}


def resolve_sources(spec):
    """'claude,codex' / 'all' -> a de-duplicated list of concrete source names. Raises ValueError on unknown."""
    names, seen = [], set()
    for raw in (spec or "all").split(","):
        raw = raw.strip()
        if not raw:
            continue
        for name in ALIASES.get(raw, [raw]):
            if name not in SOURCES:
                raise ValueError(f"unknown source {raw!r} (known: {', '.join(sorted(SOURCES))}, {', '.join(sorted(ALIASES))})")
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names


# ---------------------------------------------------------------- noise filter

_SLASH_CMD = re.compile(r"^/[a-z][a-z0-9:_-]*(\s|$)")
# A turn that OPENS with an XML-ish tag is harness scaffolding, never something a human typed:
# <task-notification>, <task_description>, <skill-context>, <bash-input>, <command-message>, …
_XML_WRAPPER = re.compile(r"^<[a-zA-Z][\w.-]*(\s[^<>]*)?>")
_TRIVIAL = {
    "continue", "go", "ok", "okay", "yes", "no", "y", "n", "thanks", "stop", "autorun", "next", "done",
    "继续", "好", "好的", "是", "对", "行", "可以", "谢谢", "停", "退出",
}


def is_noise(text):
    """True for turns that are never worth curating: slash commands, bare acknowledgements, pure pastes."""
    stripped = text.strip()
    if not stripped or _SLASH_CMD.match(stripped) or _XML_WRAPPER.match(stripped):
        return True
    if stripped.lower().rstrip(".!?。！？ ") in _TRIVIAL:
        return True
    # A turn that is only a fenced block or only a traceback is a paste, not a prompt.
    if stripped.startswith("```") and stripped.count("```") <= 2 and "\n" not in stripped.split("```", 1)[-1][:80]:
        return True
    if stripped.startswith(("Traceback (most recent call last)", "npm ERR!", "error TS", "fatal:")):
        return True
    return False


# ---------------------------------------------------------------- scoring

_BULLET = re.compile(r"^\s*(?:[-*+•]|\d+[.)]|\(\d+\))\s+\S", re.M)
_HEADING = re.compile(r"^\s*(?:#{1,4}\s+\S|\*\*[^*\n]{2,40}\*\*\s*$)", re.M)
_REQUIREMENT = re.compile(
    r"\b(must|should|shall|require[sd]?|requirements?|constraints?|deliverables?|acceptance|criteria|"
    r"do not|don't|never|always|ensure)\b|需要|要求|必须|不要|禁止|确保|交付", re.I)
_OUTPUT_SPEC = re.compile(
    r"\b(output|format|report|produce|deliver|write (?:to|a|the)|generate|save (?:to|as)|return|"
    r"summar(?:y|ise|ize)|markdown|table|json|yaml)\b|输出|格式|报告|生成|保存|表格", re.I)
_DIRECTIVE = re.compile(
    r"\b(design|write|build|create|implement|refactor|review|audit|analy[sz]e|generate|add|update|"
    r"set ?up|produce|draft|plan|research|optimi[sz]e|document|migrate|deploy|configure|integrate|"
    r"benchmark|evaluate|compare|summari[sz]e|explain|check|verify|test|fix|clean ?up|port|extend)\b"
    r"|设计|编写|实现|重构|审查|分析|生成|部署|配置|优化|整理|评估|对比|检查|验证|规划|调研|请帮|帮我|给我", re.I)

# Markers that a prompt is bound to ONE moment: they make it un-reusable as written. A curator can
# usually strip them, so they are reported per candidate rather than used as a hard filter.
ONE_OFF = [
    ("abs-path", re.compile(r"(?:/home/|/media/|/mnt/|[A-Z]:\\\\)[\w.\-]+")),
    ("line-ref", re.compile(r"\b(?:line|lines|行)\s*\d+|:\d+:\d+|\.\w{1,4}:\d+")),
    ("filename", re.compile(r"\b[\w.\-]+\.(?:py|js|ts|tsx|jsx|md|json|yml|yaml|sh|toml|tex|css|html|sql|rs|go|java)\b")),
    ("hash-id", re.compile(r"\b(?:[0-9a-f]{7,40}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4})\b")),
    ("url", re.compile(r"https?://\S+")),
    ("deictic", re.compile(r"^\s*(?:this|that|it|these|those|here|above|the (?:error|bug|issue|same))\b", re.I)),
    ("error-paste", re.compile(r"Traceback \(most recent call last\)|\bat [\w.$]+\(\w+\.\w+:\d+\)|^\s+File \"", re.M)),
]

_LATIN = re.compile(r"[a-z][a-z0-9_+\-]{2,}")
_CJK = re.compile(r"[一-鿿]")


def tokens(text):
    """Latin words plus CJK character bigrams, so recurrence works for English and Chinese prompts alike."""
    low = text.lower()
    out = set(_LATIN.findall(low))
    cjk = _CJK.findall(low)
    out.update(cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1))
    return out


def _length_score(n):
    for limit, score in ((150, 0.0), (300, 0.8), (800, 1.8), (2500, 2.5), (6000, 1.8)):
        if n < limit:
            return score
    return 1.0  # a 6000+ char turn is usually a pasted document, not a reusable prompt


def signals(text):
    """Per-candidate score components plus the one-off markers found. Pure function of the text."""
    struct = 0.0
    if len(_BULLET.findall(text)) >= 3:
        struct += 1.0
    if text.count("\n\n") >= 2:
        struct += 0.6
    if _REQUIREMENT.search(text):
        struct += 0.6
    if _HEADING.search(text):
        struct += 0.4
    if _OUTPUT_SPEC.search(text):
        struct += 0.4

    directives = {m.group(0).lower() for m in _DIRECTIVE.finditer(text)}
    imperative = 0.0
    head = text.lstrip()[:60]
    if _DIRECTIVE.match(head) or _DIRECTIVE.search(head):
        imperative += 0.8
    if len(directives) >= 2:
        imperative += 0.7

    flags = [name for name, pat in ONE_OFF if pat.search(text)]
    generality = 1.0 if not flags else max(-4.0, -1.2 * len(flags))

    return {
        "length": round(_length_score(len(text)), 2),
        "structure": round(min(struct, 3.0), 2),
        "imperative": round(imperative, 2),
        "generality": round(generality, 2),
    }, flags


def recurrence_neighbours(cands, min_shared=3, df_ceiling=0.05):
    """How many other candidates each one closely resembles.

    Cheap near-duplicate detection: index every candidate under its most DISTINCTIVE tokens (lowest
    document frequency, ignoring tokens common to >df_ceiling of the corpus), then count the peers that
    share at least `min_shared` of them. O(corpus) instead of the O(n^2) of all-pairs comparison.
    """
    n = len(cands)
    if n < 2:
        return [0] * n
    df = {}
    toks = []
    for c in cands:
        t = tokens(c["text"])
        toks.append(t)
        for tok in t:
            df[tok] = df.get(tok, 0) + 1
    # Skip tokens so common they carry no signal. The absolute floor matters: on a SMALL corpus a
    # proportional ceiling would discard the very tokens the near-duplicates share, reporting 0
    # recurrence for everything. A token in 4 or fewer documents is never "too common".
    ceiling = max(4, int(df_ceiling * n))
    index, distinctive = {}, []
    for i, t in enumerate(toks):
        # Select from the MIDDLE of the df range. A df==1 token appears in exactly one document, so it
        # can never be shared and only wastes a slot under the cap — two near-identical prompts that
        # differ in many unique ids or dates would otherwise fill the whole set with unmatchable tokens.
        rare = sorted((tok for tok in t if 2 <= df[tok] <= ceiling), key=lambda tok: (df[tok], tok))[:8]
        distinctive.append(rare)
        for tok in rare:
            index.setdefault(tok, []).append(i)
    out = [0] * n
    for i, rare in enumerate(distinctive):
        shared = {}
        for tok in rare:
            for j in index[tok]:
                if j != i:
                    shared[j] = shared.get(j, 0) + 1
        out[i] = sum(1 for v in shared.values() if v >= min_shared)
    return out


def score_all(cands):
    """Attach score / signals / flags to every candidate, in place. Returns the same list."""
    neighbours = recurrence_neighbours(cands)
    for c, nb in zip(cands, neighbours):
        sig, flags = signals(c["text"])
        repeats = nb + max(0, c.get("occurrences", 1) - 1)
        sig["recurrence"] = round(min(2.0, 0.7 * math.log2(1 + repeats)), 2)
        c["signals"] = sig
        c["flags"] = flags
        c["similar"] = nb
        c["score"] = round(sum(sig.values()), 2)
    return cands


# ---------------------------------------------------------------- pipeline

def _norm(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def collect(sources, since=None, min_len=120, base=None):
    """Run the extractors, drop noise/short turns, de-duplicate, and return (candidates, per_source_counts).

    Two de-duplications, for two different reasons:
      * (timestamp rounded to the second, hash of the text) — the SAME event seen through two sources
        (a Claude prompt appears in both history.jsonl and the session transcript).
      * exact repeated text anywhere in the corpus — collapsed into one candidate carrying
        `occurrences`, which is exactly the recurrence signal the ranking wants.
    """
    cutoff = None
    if since:
        cutoff = int(datetime.fromisoformat(since).replace(tzinfo=timezone.utc).timestamp())
    counts = {}
    seen_event, by_text, order = set(), {}, []
    for name in sources:
        kept = 0
        for c in SOURCES[name](base):
            text = c["text"]
            if len(text) < min_len or is_noise(text):
                continue
            if cutoff and c["ts"] < cutoff:
                continue
            digest = hashlib.sha1(_norm(text).encode("utf-8")).hexdigest()[:16]
            event = (c["ts"], digest)
            if event in seen_event:
                continue
            seen_event.add(event)
            kept += 1
            prior = by_text.get(digest)
            if prior is None:
                c["occurrences"] = 1
                c["sources"] = [name]
                by_text[digest] = c
                order.append(c)
            else:
                prior["occurrences"] += 1
                if name not in prior["sources"]:
                    prior["sources"].append(name)
                if c["ts"] and (not prior["ts"] or c["ts"] < prior["ts"]):  # keep the earliest sighting
                    prior["ts"], prior["date"] = c["ts"], c["date"]
        counts[name] = kept
    return order, counts


def mine(sources, since=None, min_len=120, limit=None, base=None):
    """Full pipeline: collect -> score -> rank. Returns (ranked_candidates, per_source_counts)."""
    cands, counts = collect(sources, since=since, min_len=min_len, base=base)
    score_all(cands)
    cands.sort(key=lambda c: (-c["score"], -c["occurrences"], c["ts"]))
    for i, c in enumerate(cands, 1):
        c["rank"] = i
    return (cands[:limit] if limit else cands), counts
