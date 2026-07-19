#!/usr/bin/env python3
"""ledger.py — the round task document: one markdown file that both a human and an agent read and write.

Why this exists
---------------
On a long round with a dozen-plus sub-tasks, an agent drifts. It forgets tasks it opened, it forgets
requirements the user added mid-run, and when it hands work to a sub-agent it hands over a summary that
has already lost the detail. None of that is fixable by telling the model to try harder, because the
failure IS the model's memory. So the state lives in a file, and a Stop hook refuses to let the round
end while anything in that file is unfinished.

Design
------
The markdown file is the SINGLE SOURCE OF TRUTH. There is no sidecar JSON, so there is nothing to drift
out of sync, and a human editing the file by hand is a first-class path. The parser is strict: a file it
cannot read is a loud error, never a silent misread that would let an unfinished round close.

Layout (per project):
    .agent/ledger/ACTIVE                 # one line: the active round's file name
    .agent/ledger/<round-id>.md          # the round document
    .agent/ledger/profiles.json          # per-agent / per-model rendering + enforcement profiles

Commands
--------
    open    --title T [--task "title|acceptance"]...   start a round, make it active
    add     --title T --acceptance A [--verbatim V] [--detail D]
    inbox   --text T                                   capture a mid-round requirement (hook writes here)
    triage  IN --into TID | --new "title|acceptance" | --drop "reason"
    start|done|block|drop  TID [--evidence E] [--reason R]
    status  [--json]                                   one-line or machine-readable summary
    check                                              exit 0 if the round may close, 2 if not
    brief   TID                                        full sub-agent prompt for one task
    view    [--compact]                                render for agent context
    close                                              close the round (runs check first)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER_DIR = Path(".agent/ledger")
ACTIVE_FILE = LEDGER_DIR / "ACTIVE"
PROFILES_FILE = LEDGER_DIR / "profiles.json"
LEDGER_MARKER = "<!-- task-ledger: v1 -->"

OPEN_STATUSES = ("todo", "doing")
CLOSED_STATUSES = ("done", "dropped")
ALL_STATUSES = OPEN_STATUSES + CLOSED_STATUSES + ("blocked",)

# Rendering/enforcement defaults. Overridable per agent+model via .agent/ledger/profiles.json so a new
# model or a new agent is a config edit, not a code change.
DEFAULT_PROFILES = {
    "default": {
        "view": "full",
        "enforce": True,
        "brief_includes": ["verbatim", "detail", "acceptance", "siblings"],
        "note": "Full ledger in context. Used when nothing more specific matches.",
    },
    "claude-code": {
        "view": "full",
        "enforce": True,
        "brief_includes": ["verbatim", "detail", "acceptance", "siblings"],
        "note": "Large context: the whole ledger fits, sub-agent briefs carry sibling context.",
    },
    "codex": {
        "view": "full",
        "enforce": True,
        "brief_includes": ["verbatim", "detail", "acceptance"],
        "note": "Stop hook uses the {continue,stopReason,systemMessage} schema, not {decision}.",
    },
    "opencode": {
        "view": "compact",
        "enforce": True,
        "brief_includes": ["verbatim", "detail", "acceptance"],
        "note": "Enforced through the opencode plugin API rather than a shell hook.",
    },
    "small-context": {
        "view": "compact",
        "enforce": True,
        "brief_includes": ["verbatim", "acceptance"],
        "note": "Only open tasks are rendered; briefs drop sibling context to save tokens.",
    },
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class LedgerError(Exception):
    """Raised when the ledger cannot be read or a command cannot be honored.

    Never swallowed: a ledger we cannot parse must fail loudly, because the whole point of the gate is
    that an unfinished round cannot slip past it.
    """


class NoActiveRound(LedgerError):
    """No round is open, so there is nothing to enforce.

    This is the ONLY benign reason the gate may pass without reading a ledger. It is a separate type
    precisely so `check` cannot catch it with a broad handler that would also swallow a corrupt ledger —
    that would turn an unreadable ledger into a silent green light, which is the failure this tool exists
    to prevent.
    """


# --------------------------------------------------------------------------- model


def oneline(s):
    """Collapse a value that is rendered on a single markdown line.

    The ledger is parsed back out of its own markdown, so a newline inside a single-line field would let
    the value forge structure — a `--title` carrying "\\n### `T99` fake\\n- **status**: `done`" would parse
    back as an extra, already-finished task. Callers interpolate agent and user text into these fields, so
    the render side, not the caller, is where this has to be enforced.
    """
    return " ".join(str(s or "").split())


class Task:
    def __init__(self, tid, title, status="todo", acceptance="", evidence="",
                 verbatim="", detail="", owner=""):
        self.tid = tid
        # Single-line fields: flattened so they cannot forge ledger structure. `verbatim` and `detail`
        # are deliberately NOT flattened — they are multi-line by design and are rendered indented (as a
        # blockquote and an indented block), which already prevents them matching a heading pattern.
        self.title = oneline(title)
        self.status = status
        self.acceptance = oneline(acceptance)
        self.evidence = oneline(evidence)
        self.verbatim = verbatim
        self.detail = detail
        self.owner = oneline(owner)

    @property
    def is_open(self):
        return self.status in OPEN_STATUSES

    def to_dict(self):
        return {
            "id": self.tid, "title": self.title, "status": self.status,
            "acceptance": self.acceptance, "evidence": self.evidence,
            "verbatim": self.verbatim, "detail": self.detail, "owner": self.owner,
        }


class InboxItem:
    def __init__(self, iid, text, captured, triaged=False, resolution=""):
        self.iid = iid
        self.text = text
        self.captured = captured
        self.triaged = triaged
        self.resolution = resolution

    def to_dict(self):
        return {"id": self.iid, "text": self.text, "captured": self.captured,
                "triaged": self.triaged, "resolution": self.resolution}


class Ledger:
    def __init__(self, path: Path, title="", meta=None, tasks=None, inbox=None, log=None):
        self.path = path
        self.title = title
        self.meta = meta or {}
        self.tasks = tasks or []
        self.inbox = inbox or []
        self.log = log or []

    # -- queries ------------------------------------------------------------

    def task(self, tid) -> Task:
        for t in self.tasks:
            if t.tid.upper() == tid.upper():
                return t
        raise LedgerError(f"no such task: {tid} (have: {', '.join(t.tid for t in self.tasks) or 'none'})")

    def inbox_item(self, iid) -> InboxItem:
        for i in self.inbox:
            if i.iid.upper() == iid.upper():
                return i
        raise LedgerError(f"no such inbox item: {iid} (have: {', '.join(i.iid for i in self.inbox) or 'none'})")

    def next_task_id(self):
        used = {int(m.group(1)) for t in self.tasks if (m := re.fullmatch(r"T(\d+)", t.tid))}
        return f"T{max(used) + 1 if used else 1}"

    def next_inbox_id(self):
        used = {int(m.group(1)) for i in self.inbox if (m := re.fullmatch(r"I(\d+)", i.iid))}
        return f"I{max(used) + 1 if used else 1}"

    def counts(self):
        c = {s: 0 for s in ALL_STATUSES}
        for t in self.tasks:
            c[t.status] = c.get(t.status, 0) + 1
        c["total"] = len(self.tasks)
        c["untriaged"] = sum(1 for i in self.inbox if not i.triaged)
        return c

    def blockers(self):
        """Everything standing between this round and closing."""
        out = []
        for t in self.tasks:
            if t.is_open:
                out.append(f"{t.tid} [{t.status}] {t.title}")
            elif t.status == "done" and not t.evidence.strip():
                out.append(f"{t.tid} [done but no evidence] {t.title}")
        for i in self.inbox:
            if not i.triaged:
                out.append(f"{i.iid} [untriaged inbox] {i.text[:80]}")
        return out

    def can_close(self):
        return not self.blockers()

    # -- rendering ----------------------------------------------------------

    def status_line(self):
        c = self.counts()
        done = c["done"] + c["dropped"]
        bits = [f"**{done}/{c['total']} settled**"]
        for s in ("doing", "todo", "blocked"):
            if c.get(s):
                bits.append(f"{c[s]} {s}")
        if c["untriaged"]:
            bits.append(f"{c['untriaged']} inbox untriaged")
        return " · ".join(bits)

    def render(self):
        L = [f"# Round: {self.title}", "", LEDGER_MARKER, "",
             "> Generated and maintained by `hooks/task-ledger/scripts/ledger.py`. This file is the source of",
             "> truth for the round. A Stop hook refuses to end the round while anything below is unfinished.",
             "", f"> {self.status_line()}", "", "## Meta", "", "| field | value |", "|---|---|"]
        for k, v in self.meta.items():
            L.append(f"| {k} | {v} |")
        L += ["", "## Inbox", "",
              "> Requirements that arrived mid-round land here automatically. Each must be triaged into a task",
              "> (or explicitly dropped, with a reason) before the round can close. This is what stops a",
              "> mid-run instruction from being forgotten.", ""]
        if not self.inbox:
            L.append("_(empty)_")
        for i in self.inbox:
            box = "x" if i.triaged else " "
            line = f"- [{box}] `{i.iid}` {i.captured} — {i.text}"
            if i.resolution:
                line += f" → **{i.resolution}**"
            L.append(line)
        L += ["", "## Tasks", ""]
        if not self.tasks:
            L.append("_(none)_")
        for t in self.tasks:
            L += [f"### `{t.tid}` {t.title}", "",
                  f"- **status**: `{t.status}`",
                  f"- **acceptance**: {t.acceptance or '—'}",
                  f"- **evidence**: {t.evidence or '—'}",
                  f"- **owner**: {t.owner or '—'}"]
            if t.verbatim:
                L += ["- **verbatim**:", ""]
                L += [f"  > {ln}" for ln in t.verbatim.splitlines()]
                L.append("")
            if t.detail:
                L += ["- **detail**:", ""]
                L += [f"  {ln}" for ln in t.detail.splitlines()]
                L.append("")
            L.append("")
        L += ["## Log", ""]
        for entry in self.log:
            L.append(f"- {entry}")
        L.append("")
        return "\n".join(L)

    def view(self, compact=False):
        """What the agent should hold in context. Compact drops settled tasks and long detail."""
        if not compact:
            return self.render()
        L = [f"# Round: {self.title}", "", f"> {self.status_line()}", "", "## Open tasks", ""]
        for t in self.tasks:
            if t.is_open or t.status == "blocked":
                L.append(f"- `{t.tid}` [{t.status}] {t.title} — accept: {t.acceptance or '—'}")
        untriaged = [i for i in self.inbox if not i.triaged]
        if untriaged:
            L += ["", "## Untriaged inbox", ""]
            for i in untriaged:
                L.append(f"- `{i.iid}` {i.text}")
        settled = [t for t in self.tasks if not t.is_open and t.status != "blocked"]
        if settled:
            L += ["", f"## Settled ({len(settled)})", "",
                  ", ".join(f"`{t.tid}`" for t in settled)]
        return "\n".join(L) + "\n"

    def brief(self, tid, includes):
        """A complete sub-agent prompt for one task.

        The drift this fixes: an agent dispatching a sub-agent normally retypes the task from memory and
        drops the user's original wording and the acceptance bar. Everything a sub-agent needs is stored
        on the task, so the brief is generated, not remembered.
        """
        t = self.task(tid)
        L = [f"# Task {t.tid} — {t.title}", "",
             f"Part of round: **{self.title}** (`{self.meta.get('round-id', '?')}`).", ""]
        if "verbatim" in includes and t.verbatim:
            L += ["## The user's own words", "",
                  "Treat this as the requirement of record. Where this and the summary below disagree,",
                  "this wins.", ""]
            L += [f"> {ln}" for ln in t.verbatim.splitlines()]
            L.append("")
        if "detail" in includes and t.detail:
            L += ["## Detail", "", t.detail, ""]
        if "acceptance" in includes:
            L += ["## Acceptance", "",
                  t.acceptance or "_Not specified — ask before assuming you are done._", "",
                  "Report the evidence that this was met (command output, file path, commit). "
                  "A claim without evidence does not close this task.", ""]
        if "siblings" in includes:
            others = [x for x in self.tasks if x.tid != t.tid]
            if others:
                L += ["## Sibling tasks in this round (context, not your job)", ""]
                for x in others:
                    L.append(f"- `{x.tid}` [{x.status}] {x.title}")
                L += ["", "Do not do these. If your work would change one of them, say so in your report.", ""]
        return "\n".join(L)


# --------------------------------------------------------------------------- parsing

_TASK_HEAD = re.compile(r"^### `(T\d+)` (.*)$")
_FIELD = re.compile(r"^- \*\*(\w+)\*\*: (.*)$")
_FIELD_BLOCK = re.compile(r"^- \*\*(\w+)\*\*:\s*$")
_INBOX = re.compile(r"^- \[([ x])\] `(I\d+)` (\S+) — (.*)$")
_META = re.compile(r"^\| (\S+) \| (.*) \|$")


def parse(path: Path) -> Ledger:
    if not path.exists():
        raise LedgerError(f"ledger not found: {path}")
    text = path.read_text(encoding="utf-8")
    if LEDGER_MARKER not in text:
        raise LedgerError(
            f"{path} is missing the {LEDGER_MARKER} marker — refusing to guess at its format. "
            "If you hand-edited it, restore the marker; the gate must never misread a ledger.")
    lines = text.splitlines()

    title = ""
    if lines and lines[0].startswith("# Round: "):
        title = lines[0][len("# Round: "):].strip()

    led = Ledger(path, title=title)
    section = None
    cur: Task | None = None
    block_field = None
    block_lines: list[str] = []

    def flush_block():
        nonlocal block_field, block_lines
        if cur is not None and block_field:
            val = "\n".join(block_lines).strip()
            if block_field == "verbatim":
                cur.verbatim = re.sub(r"^\s*> ?", "", val, flags=re.M).strip()
            elif block_field == "detail":
                cur.detail = "\n".join(ln.strip() for ln in val.splitlines()).strip()
        block_field, block_lines = None, []

    for raw in lines:
        if raw.startswith("## "):
            flush_block()
            cur = None
            section = raw[3:].strip().lower()
            continue

        if section == "meta":
            m = _META.match(raw)
            if m and m.group(1) != "field" and not m.group(1).startswith("-"):
                led.meta[m.group(1)] = m.group(2).strip()
            continue

        if section == "inbox":
            m = _INBOX.match(raw)
            if m:
                text_part = m.group(4)
                resolution = ""
                if " → **" in text_part:
                    text_part, resolution = text_part.split(" → **", 1)
                    resolution = resolution.rstrip("*")
                led.inbox.append(InboxItem(m.group(2), text_part.strip(), m.group(3),
                                           triaged=(m.group(1) == "x"), resolution=resolution))
            continue

        if section == "tasks":
            head = _TASK_HEAD.match(raw)
            if head:
                flush_block()
                cur = Task(head.group(1), head.group(2).strip())
                led.tasks.append(cur)
                continue
            if cur is None:
                continue
            mb = _FIELD_BLOCK.match(raw)
            if mb:
                flush_block()
                block_field = mb.group(1)
                continue
            mf = _FIELD.match(raw)
            if mf:
                flush_block()
                key, val = mf.group(1), mf.group(2).strip()
                val = "" if val == "—" else val.strip("`")
                if key == "status":
                    if val not in ALL_STATUSES:
                        raise LedgerError(
                            f"{path}: task {cur.tid} has unknown status {val!r} "
                            f"(expected one of: {', '.join(ALL_STATUSES)})")
                    cur.status = val
                elif key in ("acceptance", "evidence", "owner"):
                    setattr(cur, key, val)
                continue
            if block_field is not None:
                block_lines.append(raw)
            continue

        if section == "log" and raw.startswith("- "):
            led.log.append(raw[2:])

    flush_block()
    return led


# --------------------------------------------------------------------------- storage


def project_root(start: Path | None = None) -> Path:
    """Nearest ancestor holding .agent/ledger, else .git, else cwd."""
    cur = (start or Path.cwd()).resolve()
    for d in [cur, *cur.parents]:
        if (d / LEDGER_DIR).is_dir():
            return d
    for d in [cur, *cur.parents]:
        if (d / ".git").exists():
            return d
    return cur


def active_path(root: Path | None = None) -> Path | None:
    root = root or project_root()
    af = root / ACTIVE_FILE
    if not af.exists():
        return None
    name = af.read_text(encoding="utf-8").strip()
    if not name:
        return None
    p = root / LEDGER_DIR / name
    return p if p.exists() else None


def load_active(root: Path | None = None) -> Ledger:
    p = active_path(root)
    if p is None:
        raise NoActiveRound("no active round (nothing to enforce). Start one: ledger.py open --title '...'")
    return parse(p)  # a parse failure raises LedgerError, which callers must NOT treat as "no round"


def save(led: Ledger, entry: str | None = None):
    """Persist the ledger, bumping its revision.

    The document does NOT depend on git for history. Its name carries the date, `revision` counts every
    mutation, and the Log section below records what each one was and when. Git adds diffable prior
    states, which is a convenience; a project with no repository still gets a complete, ordered account
    of how the round evolved, which is the thing the ledger exists to preserve.
    """
    try:
        rev = int(led.meta.get("revision", 0)) + 1
    except (TypeError, ValueError):
        rev = 1
    led.meta["revision"] = str(rev)
    led.meta["updated"] = now()
    if entry:
        led.log.append(f"{now()} r{rev} {entry}")
    led.path.parent.mkdir(parents=True, exist_ok=True)
    led.path.write_text(led.render(), encoding="utf-8")


def load_profiles(root: Path | None = None) -> dict:
    root = root or project_root()
    pf = root / PROFILES_FILE
    if pf.exists():
        try:
            user = json.loads(pf.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise LedgerError(f"{pf} is not valid JSON: {e}") from e
        merged = dict(DEFAULT_PROFILES)
        merged.update(user)
        return merged
    return dict(DEFAULT_PROFILES)


def resolve_profile(name: str | None, root: Path | None = None) -> dict:
    profiles = load_profiles(root)
    if name and name != "auto":
        if name not in profiles:
            raise LedgerError(f"unknown profile {name!r} (have: {', '.join(sorted(profiles))})")
        return profiles[name]
    for env, key in (("CLAUDE_AGENT", None), ("CODEX_HOME", "codex"), ("OPENCODE_CONFIG", "opencode")):
        if os.environ.get(env):
            cand = key or os.environ[env]
            if cand in profiles:
                return profiles[cand]
    return profiles["default"]


# --------------------------------------------------------------------------- commands


def cmd_open(a):
    root = project_root()
    slug = re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:40] or "round"
    rid = f"{datetime.now(timezone.utc):%Y-%m-%d}-{slug}"
    path = root / LEDGER_DIR / f"{rid}.md"
    if path.exists() and not a.force:
        raise LedgerError(f"{path} already exists (use --force to overwrite)")
    led = Ledger(path, title=a.title, meta={
        "round-id": rid, "opened": now(),
        "agent": a.agent or os.environ.get("CLAUDE_AGENT", "unknown"),
        "model": a.model or os.environ.get("CLAUDE_MODEL", "unknown"),
        "profile": a.profile or "auto",
    })
    for spec in a.task or []:
        title, _, acc = spec.partition("|")
        led.tasks.append(Task(led.next_task_id(), title.strip(), acceptance=acc.strip()))
    save(led, f"opened round with {len(led.tasks)} task(s)")
    (root / ACTIVE_FILE).parent.mkdir(parents=True, exist_ok=True)
    (root / ACTIVE_FILE).write_text(path.name + "\n", encoding="utf-8")
    print(f"opened {path} ({len(led.tasks)} task(s)); it is now the active round")


def cmd_add(a):
    led = load_active()
    t = Task(led.next_task_id(), a.title, acceptance=a.acceptance or "",
             verbatim=a.verbatim or "", detail=a.detail or "", owner=a.owner or "")
    led.tasks.append(t)
    save(led, f"added {t.tid} {t.title}")
    print(t.tid)


def cmd_inbox(a):
    """Capture a mid-round requirement. Called by the UserPromptSubmit hook, so it must never fail hard."""
    try:
        led = load_active()
    except LedgerError as e:
        print(f"(no active round; not captured: {e})", file=sys.stderr)
        return 0
    text = " ".join(a.text.split())
    if not text:
        return 0
    for i in led.inbox:
        if i.text == text:
            return 0
    item = InboxItem(led.next_inbox_id(), text, now())
    led.inbox.append(item)
    save(led, f"captured {item.iid} into inbox")
    print(item.iid)
    return 0


def cmd_triage(a):
    led = load_active()
    item = led.inbox_item(a.item)
    if a.into:
        led.task(a.into)
        item.resolution = f"folded into {a.into.upper()}"
    elif a.new:
        title, _, acc = a.new.partition("|")
        t = Task(led.next_task_id(), title.strip(), acceptance=acc.strip(), verbatim=item.text)
        led.tasks.append(t)
        item.resolution = f"became {t.tid}"
    elif a.drop:
        item.resolution = f"dropped: {a.drop}"
    else:
        raise LedgerError("triage needs one of --into TID, --new 'title|acceptance', or --drop 'reason'")
    item.resolution = oneline(item.resolution)
    item.triaged = True
    save(led, f"triaged {item.iid}: {item.resolution}")
    print(item.resolution)


def cmd_transition(a):
    led = load_active()
    t = led.task(a.task_id)
    target = {"start": "doing", "done": "done", "block": "blocked", "drop": "dropped"}[a.cmd]
    if target == "done":
        if not a.evidence:
            raise LedgerError(
                f"{t.tid} cannot be marked done without --evidence. Name what proves it: a command and its "
                "output, a file path, a commit. This is the check that stops a round closing on assertions.")
        t.evidence = oneline(a.evidence)
    if target in ("blocked", "dropped"):
        if not a.reason:
            raise LedgerError(f"{t.tid} needs --reason to be marked {target}")
        t.evidence = oneline((t.evidence + " " if t.evidence else "") + f"({target}: {a.reason})")
    t.status = target
    save(led, f"{t.tid} -> {target}")
    print(f"{t.tid} -> {target}")


def cmd_status(a):
    try:
        led = load_active()
    except NoActiveRound as e:
        if a.json:
            print(json.dumps({"active": False, "reason": str(e)}))
        else:
            print(str(e))
        return 0
    except LedgerError as e:
        # A round IS open but unreadable. Report active with an error so no caller mistakes a corrupt
        # ledger for an absent one, and exit non-zero so shell callers notice.
        if a.json:
            print(json.dumps({"active": True, "readable": False, "error": str(e), "can_close": False}))
        else:
            print(f"active round is UNREADABLE: {e}")
        return 1
    if a.json:
        print(json.dumps({
            "active": True, "path": str(led.path), "title": led.title,
            "counts": led.counts(), "blockers": led.blockers(), "can_close": led.can_close(),
            "tasks": [t.to_dict() for t in led.tasks], "inbox": [i.to_dict() for i in led.inbox],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"{led.title} — {led.status_line().replace('**', '')}")
        print(f"  {led.path.resolve()}")
        for b in led.blockers():
            print(f"  open: {b}")
    return 0


def cmd_path(a):
    """Absolute path of the active round document, for embedding as a clickable link in a summary."""
    try:
        led = load_active()
    except NoActiveRound:
        print("no active round", file=sys.stderr)
        return 1
    print(led.path.resolve())
    return 0


def cmd_check(a):
    """Exit 0 if the round may close, 2 if not, 1 if the ledger cannot be trusted.

    The Stop hook turns exit 2 into a blocked stop. Only NoActiveRound may pass silently: a ledger that
    fails to parse must surface as an error, never as an empty round that is trivially complete.
    """
    try:
        led = load_active()
    except NoActiveRound:
        return 0
    blockers = led.blockers()
    if not blockers:
        print(f"round '{led.title}' is complete: {led.status_line().replace('**', '')}")
        return 0
    print(f"ROUND NOT COMPLETE — {led.title}")
    print(f"Ledger: {led.path.resolve()}")
    print("")
    print("These must be settled before this round can end:")
    for b in blockers:
        print(f"  - {b}")
    print("")
    print("Settle each one, do not just report on it:")
    print("  finish it      -> ledger.py done <TID> --evidence '<what proves it>'")
    print("  cannot finish  -> ledger.py block <TID> --reason '<what is missing>'")
    print("  not needed     -> ledger.py drop <TID> --reason '<why>'")
    print("  inbox item     -> ledger.py triage <IID> --into <TID> | --new 'title|acceptance' | --drop '<why>'")
    return 2


def cmd_approvals(a):
    """Print every parked item as a question, for the single end-of-run approval batch.

    Under `rules/autorun-mode` an approval the agent needs is a task it parks, not a turn it ends. The
    parked items ARE the queue, so there is no second artifact to keep in sync. This renders them.
    """
    try:
        led = load_active()
    except NoActiveRound:
        print("no active round")
        return 0
    parked = [t for t in led.tasks if t.status == "blocked"]
    if not parked:
        print("nothing is waiting on you")
        return 0
    if a.json:
        print(json.dumps([t.to_dict() for t in parked], ensure_ascii=False, indent=2))
        return 0
    print(f"{len(parked)} item(s) need you before this round can finish:\n")
    for i, t in enumerate(parked, 1):
        reason = t.evidence or "no reason recorded"
        print(f"{i}. **{t.title}** (`{t.tid}`)")
        print(f"   blocked on: {reason}")
        if t.acceptance:
            print(f"   done when: {t.acceptance}")
        print("")
    return 0


def cmd_brief(a):
    led = load_active()
    prof = resolve_profile(a.profile)
    print(led.brief(a.task_id, prof["brief_includes"]))


def cmd_view(a):
    try:
        led = load_active()
    except NoActiveRound as e:
        print(str(e))
        return 0
    prof = resolve_profile(a.profile)
    print(led.view(compact=a.compact or prof["view"] == "compact"))
    return 0


def cmd_close(a):
    led = load_active()
    if not led.can_close() and not a.force:
        return cmd_check(a)
    save(led, "round closed" + (" (forced)" if a.force else ""))
    root = project_root()
    (root / ACTIVE_FILE).unlink(missing_ok=True)
    print(f"closed {led.path}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="ledger.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    o = sub.add_parser("open", help="start a round and make it active")
    o.add_argument("--title", required=True)
    o.add_argument("--task", action="append", help="'title|acceptance', repeatable")
    o.add_argument("--agent"); o.add_argument("--model"); o.add_argument("--profile")
    o.add_argument("--force", action="store_true")
    o.set_defaults(fn=cmd_open)

    ad = sub.add_parser("add", help="add a task to the active round")
    ad.add_argument("--title", required=True)
    ad.add_argument("--acceptance", required=True)
    ad.add_argument("--verbatim"); ad.add_argument("--detail"); ad.add_argument("--owner")
    ad.set_defaults(fn=cmd_add)

    ib = sub.add_parser("inbox", help="capture a mid-round requirement")
    ib.add_argument("--text", required=True)
    ib.set_defaults(fn=cmd_inbox)

    tr = sub.add_parser("triage", help="resolve an inbox item")
    tr.add_argument("item")
    tr.add_argument("--into"); tr.add_argument("--new"); tr.add_argument("--drop")
    tr.set_defaults(fn=cmd_triage)

    for name, helptext in (("start", "mark a task in progress"), ("done", "mark a task done"),
                           ("block", "mark a task blocked"), ("drop", "drop a task")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("task_id")
        s.add_argument("--evidence"); s.add_argument("--reason")
        s.set_defaults(fn=cmd_transition)

    st = sub.add_parser("status", help="summary of the active round")
    st.add_argument("--json", action="store_true")
    st.set_defaults(fn=cmd_status)

    pa = sub.add_parser("path", help="absolute path of the active round document")
    pa.set_defaults(fn=cmd_path)

    ck = sub.add_parser("check", help="exit 2 if the round cannot close yet")
    ck.set_defaults(fn=cmd_check)

    ap = sub.add_parser("approvals", help="parked items, rendered as the end-of-run approval batch")
    ap.add_argument("--json", action="store_true")
    ap.set_defaults(fn=cmd_approvals)

    br = sub.add_parser("brief", help="full sub-agent prompt for one task")
    br.add_argument("task_id"); br.add_argument("--profile")
    br.set_defaults(fn=cmd_brief)

    vw = sub.add_parser("view", help="render the ledger for agent context")
    vw.add_argument("--compact", action="store_true"); vw.add_argument("--profile")
    vw.set_defaults(fn=cmd_view)

    cl = sub.add_parser("close", help="close the round")
    cl.add_argument("--force", action="store_true")
    cl.set_defaults(fn=cmd_close)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args) or 0
    except LedgerError as e:
        print(f"ledger: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
