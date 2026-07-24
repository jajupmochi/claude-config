#!/usr/bin/env python3
"""Register existing Claude Code CLI sessions in the Claude Desktop app's Code tab.

Desktop and the CLI already share the transcript store (~/.claude/projects/<enc-cwd>/<cliSessionId>.jsonl).
What Desktop keeps separately is a per-session registry file that drives its sidebar:

    ~/.config/Claude/claude-code-sessions/<accountId>/<workspaceId>/local_<uuid>.json

This script writes one such registry file per CLI session. It never touches a transcript and never
modifies an existing registry file, so undoing it is `rm` on the files it reports.

Dry-run by default. Pass --apply to write.

Known limits, stated up front because they are not obvious:
  * The registry schema is undocumented and was read off one sample the app itself produced. A Desktop
    upgrade may change it.
  * `model` and `effort` are deliberately OMITTED. Desktop spawns `claude --resume <id>` and only adds
    `--model` when the record carries one, so leaving it out keeps the session on whatever the CLI
    would pick rather than silently re-pointing an old session at a different model.
  * Desktop reads this directory at startup, so the app must be restarted for new records to appear.
  * A session the user DELETED in the app leaves a `deleted_<id>` tombstone here; those are skipped
    rather than resurrected. Deleting a session in the app does not delete its transcript.
  * Registering a session that is running in a CLI right now is allowed — it is how you hand one off
    — but the CLI must EXIT before the session is opened in Desktop. Two processes appending to one
    transcript corrupts it. Such records are flagged [RUNNING NOW] with a warning on stderr.
"""
import argparse
import calendar
import json
import os
import sys
import time
import uuid
from pathlib import Path

HOME = Path.home()
PROJECTS = HOME / ".claude" / "projects"
REGISTRY_ROOT = HOME / ".config" / "Claude" / "claude-code-sessions"

# Read at most this many CHARACTERS of a transcript to recover cwd + title. The largest transcripts
# here are 200 MB; the fields we need are in the first few records, so never read the whole file.
# Counted in characters rather than bytes because the file is opened in text mode — the cap is a
# cheap bound on work, not an exact byte budget.
HEAD_CHARS = 512 * 1024


def iso_to_epoch_ms(ts):
    """Convert a transcript timestamp to epoch milliseconds.

    Transcript timestamps are UTC (they carry a trailing Z). `time.mktime` would interpret the parsed
    struct as LOCAL time, which silently shifts every createdAt by the machine's UTC offset — two
    hours here. `calendar.timegm` is the UTC counterpart and is the correct one.
    Returns None when the value is missing or unparseable, so the caller can fall back to file mtime.
    """
    if not isinstance(ts, str) or len(ts) < 19:
        return None
    try:
        return int(calendar.timegm(time.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S")) * 1000)
    except ValueError:
        return None

TMP_ROOTS = ("/tmp", "/var/tmp")


def under_tmp(cwd):
    """True for a scratch cwd. Matching on a "/tmp/" prefix alone misses cwd == "/tmp" exactly,
    which is where the ~1000 throwaway sessions live — they would have flooded the sidebar."""
    p = os.path.normpath(cwd)
    return any(p == root or p.startswith(root + os.sep) for root in TMP_ROOTS)


def find_registry_dir():
    """Locate the <accountId>/<workspaceId> directory the app is actually using.

    Prefer a directory that already holds a record — that is provably the live one. Fall back to a
    single unambiguous candidate. Refuse to guess between several, because writing into the wrong
    workspace produces records that silently never show up.
    """
    if not REGISTRY_ROOT.is_dir():
        sys.exit(f"registry root not found: {REGISTRY_ROOT}\n"
                 "Open one session in the Desktop app's Code tab first — that creates it.")
    candidates = [d for d in REGISTRY_ROOT.glob("*/*") if d.is_dir()]
    populated = [d for d in candidates if list(d.glob("local_*.json"))]
    if len(populated) == 1:
        return populated[0]
    if not candidates:
        sys.exit(f"no <account>/<workspace> directory under {REGISTRY_ROOT}")
    if len(candidates) == 1:
        return candidates[0]
    sys.exit("several candidate registry directories; pass --registry explicitly:\n  " +
             "\n  ".join(str(d) for d in sorted(populated or candidates)))


def text_of(content):
    """Flatten a transcript message's content to plain text. It is either a string or a list of
    typed blocks, and only the text blocks are useful for a title."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content
                        if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_real_prompt(t):
    """Reject the wrappers that are not something the user typed. Using one of these as the sidebar
    title would label every session 'Caveat: The messages below...'."""
    t = t.strip()
    if not t:
        return False
    noise = ("<local-command", "<command-name>", "<command-message>", "Caveat:",
             "<system-reminder>", "<user-prompt-submit-hook>", "[Request interrupted")
    return not t.startswith(noise)


def scan(path):
    """Recover (cwd, title, created_ms) from the head of a transcript. Returns None if the file
    carries no cwd, which means it is not a session record we can place."""
    cwd = None
    title = None
    created = None
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            read = 0
            for line in fh:
                read += len(line)
                if read > HEAD_CHARS:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if cwd is None and isinstance(rec.get("cwd"), str):
                    cwd = rec["cwd"]
                if created is None and isinstance(rec.get("timestamp"), str):
                    created = rec["timestamp"]
                if title is None and rec.get("type") == "user":
                    msg = rec.get("message") or {}
                    t = text_of(msg.get("content"))
                    if is_real_prompt(t):
                        title = " ".join(t.split())[:70]
                if cwd and title and created:
                    break
    except OSError as e:
        print(f"  ! unreadable: {path} ({e})", file=sys.stderr)
        return None
    if not cwd:
        return None
    return cwd, (title or Path(cwd).name), iso_to_epoch_ms(created)


def registered_cli_ids(reg_dir):
    """cliSessionIds already present, so re-running the script is a no-op rather than a duplicate.

    A record this function fails to read is a record whose session will be registered a SECOND time,
    producing a duplicate sidebar entry. That is exactly the kind of failure a silent `continue`
    hides, so every unreadable record is reported rather than skipped quietly.
    """
    seen = set()
    for f in sorted(reg_dir.glob("local_*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"  ! unreadable registry record, its session may be registered twice: "
                  f"{f.name} ({e})", file=sys.stderr)
            continue
        if rec.get("cliSessionId"):
            seen.add(rec["cliSessionId"])
    return seen


def live_session_ids():
    """cliSessionIds that a `claude` process is running RIGHT NOW, read from /proc.

    Registering a live session is legitimate — it is how you hand one off to the Desktop app — but
    opening it in Desktop before the CLI exits puts two processes on the same transcript, and that
    file is append-only shared state. Corrupting it loses the conversation, which is the worst
    outcome this tool can cause, so the case is called out at registration time rather than left to
    whoever remembers the warning.

    Linux-only, and best-effort by design: /proc is unreadable in some sandboxes and a session can
    start a moment after the scan. An empty result therefore means "found none", not "there are
    none", so this only ever warns and never blocks.
    """
    live = set()
    proc = Path("/proc")
    if not proc.is_dir():
        return live
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        for source, sep in (("cmdline", "\0"), ("environ", "\0")):
            try:
                blob = (entry / source).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue  # process exited, or not ours — both are normal while iterating /proc
            for field in blob.split(sep):
                if field.startswith("CLAUDE_CODE_SESSION_ID="):
                    live.add(field.split("=", 1)[1])
                elif field.startswith("--resume="):
                    live.add(field.split("=", 1)[1])
    return live


TOMBSTONE_PREFIX = "deleted_"


def tombstoned_ids(reg_dir):
    """ids the app has marked as deleted.

    Deleting a session in the Desktop UI writes `deleted_<id>` next to the records, once for the
    sessionId and once for the cliSessionId, holding a millisecond timestamp. Re-registering a
    tombstoned session resurrects something the user deliberately removed, so a tombstone is a
    reason to skip. (Deleting a session does NOT delete the transcript — verified: the jsonl of a
    deleted session was still on disk afterwards.)
    """
    return {p.name[len(TOMBSTONE_PREFIX):] for p in reg_dir.glob(TOMBSTONE_PREFIX + "*")}


def build_record(cli_id, cwd, title, created_ms, mtime_ms):
    sid = "local_" + str(uuid.uuid4())
    return sid, {
        "sessionId": sid,
        "cliSessionId": cli_id,
        "cwd": cwd,
        "originCwd": cwd,
        "lastFocusedAt": mtime_ms,
        "createdAt": created_ms or mtime_ms,
        "lastActivityAt": mtime_ms,
        "isArchived": False,
        "title": title,
        "titleSource": "auto",
        "permissionMode": "acceptEdits",
        "remoteMcpServersConfig": [],
        "bridgeSessionIds": [],
        "alwaysAllowedReasons": [],
        "sessionPermissionUpdates": [],
        "classifierSummaryEnabled": True,
        "reportFindingsCard": True,
        "spawnSeed": {},
    }


def gather_candidates(reg_dir, only="", min_mb=0.0, max_mb=0.0, session=""):
    """Return (candidates, skipped, live).

    A candidate is a top-level transcript eligible for registration: not already registered, not
    tombstoned, cwd still exists and is not under /tmp, passing the size and substring filters. Each
    is a dict {cli_id, cwd, title, created_ms, mtime_ms, size_mb, live}.

    Ordered newest conversation first — by createdAt descending, tie-broken by id. createdAt is read
    from the transcript's first record and never changes, so the numbers a `--list` prints stay
    stable for a `--pick` that runs against the same tree a moment later, even though a live session's
    file mtime keeps moving. (Only when a transcript has no parseable first timestamp does the sort
    fall back to its volatile mtime; that is rare and affects at most that one row's position.)
    """
    already = registered_cli_ids(reg_dir)
    tombstones = tombstoned_ids(reg_dir)
    live = live_session_ids()
    skipped = {}

    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1

    cands = []
    # Top-level transcripts only. Files under <session>/subagents/ are sub-agent logs, not sessions.
    for f in PROJECTS.glob("*/*.jsonl"):
        cli_id = f.stem
        if session and cli_id != session:
            skip("filtered out by --session")
            continue
        if cli_id in already:
            skip("already registered")
            continue
        if cli_id in tombstones:
            skip("deleted in the app — not resurrecting it")
            continue
        size_mb = f.stat().st_size / 1e6
        if min_mb and size_mb < min_mb:
            skip("below --min-mb")
            continue
        if max_mb and size_mb > max_mb:
            skip("above --max-mb")
            continue
        info = scan(f)
        if not info:
            skip("no cwd in transcript")
            continue
        cwd, title, created_ms = info
        if under_tmp(cwd):
            skip("cwd under /tmp")
            continue
        if only and only not in cwd:
            skip("filtered out by --only")
            continue
        if not Path(cwd).is_dir():
            skip("cwd no longer exists")
            continue
        cands.append({
            "cli_id": cli_id, "cwd": cwd, "title": title, "created_ms": created_ms,
            "mtime_ms": int(f.stat().st_mtime * 1000), "size_mb": size_mb, "live": cli_id in live,
        })
    cands.sort(key=lambda c: (-(c["created_ms"] or c["mtime_ms"]), c["cli_id"]))
    return cands, skipped, live


def parse_pick(spec, count):
    """Turn a --pick spec into sorted 0-based indices, validated against `count`.

    Accepts comma-separated numbers and inclusive ranges: "1,3,5" or "1-4,7". Every out-of-range or
    unparseable token raises ValueError with a specific message, because a --pick typo that silently
    registered the wrong session is exactly the mistake numbered selection is meant to prevent.
    """
    picks = set()
    for part in spec.replace(" ", "").split(","):
        if not part:
            continue
        if "-" in part:
            a, _, b = part.partition("-")
            if not (a.isdigit() and b.isdigit()):
                raise ValueError(f"bad range {part!r}")
            lo, hi = int(a), int(b)
            if lo > hi:
                raise ValueError(f"reversed range {part!r}")
            rng = range(lo, hi + 1)
        elif part.isdigit():
            rng = [int(part)]
        else:
            raise ValueError(f"not a number {part!r}")
        for k in rng:
            if not 1 <= k <= count:
                raise ValueError(f"{k} is out of range 1..{count}")
            picks.add(k - 1)
    if not picks:
        raise ValueError("no numbers given")
    return sorted(picks)


def render_list(cands):
    """A numbered table for the user to pick from. Title goes last and unaligned: it is CJK-wide and
    variable, so column-aligning it would need display-width math for no real benefit."""
    if not cands:
        return "  (nothing registerable — every session is already registered, deleted, or filtered)"
    rows = [f"  {'#':>3}  {'size':>7}  {'date':<10}  project / title"]
    for i, c in enumerate(cands, 1):
        date = time.strftime("%Y-%m-%d", time.gmtime((c["created_ms"] or c["mtime_ms"]) / 1000))
        proj = Path(c["cwd"]).name
        flag = "  [RUNNING NOW]" if c["live"] else ""
        rows.append(f"  {i:>3}  {c['size_mb']:>6.1f}M  {date:<10}  {proj} — {c['title'][:64]}{flag}")
    return "\n".join(rows)


def print_skips(skipped):
    if skipped:
        print("skipped:")
        for k, v in sorted(skipped.items(), key=lambda kv: -kv[1]):
            print(f"  {v:>5}  {k}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true",
                    help="print a NUMBERED table of registerable sessions and exit (writes nothing)")
    ap.add_argument("--pick", default="",
                    help='register sessions by their --list number(s): "1,3,5" or "1-4,7" '
                         "(implies writing; the numbering is the one --list shows)")
    ap.add_argument("--apply", action="store_true", help="write the records (default: dry run)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N sessions (0 = no limit)")
    ap.add_argument("--only", default="", help="only sessions whose cwd contains this substring")
    ap.add_argument("--session", default="",
                    help="register exactly this cliSessionId (the transcript filename without .jsonl)")
    ap.add_argument("--title", default="",
                    help="sidebar title, overriding the one derived from the first prompt; only "
                         "meaningful with --session, since one title cannot describe a batch")
    ap.add_argument("--min-mb", type=float, default=0.0, help="skip transcripts smaller than this")
    ap.add_argument("--max-mb", type=float, default=0.0,
                    help="skip transcripts larger than this (huge ones are slow to resume)")
    ap.add_argument("--registry", default="", help="override the registry directory")
    args = ap.parse_args()

    if args.registry:
        reg_dir = Path(args.registry).expanduser()
        # Validate before scanning. Without this an unwritable or mistyped path is only discovered at
        # the first write, after the run has already reported records it did not actually create.
        if not reg_dir.is_dir():
            sys.exit(f"--registry is not a directory: {reg_dir}")
        if (args.apply or args.pick) and not os.access(reg_dir, os.W_OK):
            sys.exit(f"--registry is not writable: {reg_dir}")
    else:
        reg_dir = find_registry_dir()

    # Guard the incompatible combinations up front, each with a reason, rather than letting one
    # silently override the other.
    if args.title and not args.session:
        sys.exit("--title requires --session: one title cannot describe a batch")
    if args.pick and args.session:
        sys.exit("--pick and --session are two ways to choose the same thing; pass only one")
    if args.list and (args.apply or args.pick):
        sys.exit("--list only prints; drop --apply/--pick to list, or drop --list to write")

    print(f"registry: {reg_dir}")
    cands, skipped, live = gather_candidates(reg_dir, args.only, args.min_mb, args.max_mb, args.session)
    print(f"registerable: {len(cands)}   running now: {len(live)}   skipped: {sum(skipped.values())}\n")

    if args.list:
        print(render_list(cands))
        print()
        print_skips(skipped)
        return

    if args.pick:
        try:
            idxs = parse_pick(args.pick, len(cands))
        except ValueError as e:
            sys.exit(f"--pick: {e}")
        chosen = [cands[i] for i in idxs]
    else:
        chosen = cands[:args.limit] if args.limit else cands

    written = []
    for c in chosen:
        sid, rec = build_record(c["cli_id"], c["cwd"], args.title or c["title"],
                                c["created_ms"], c["mtime_ms"])
        target = reg_dir / f"{sid}.json"
        written.append((target, rec, c["size_mb"], c["live"]))
        if args.apply:
            target.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")

    verb = "wrote" if args.apply else "would write"
    print(f"{verb} {len(written)} record(s):\n")
    for target, rec, size_mb, is_live in written:
        print(f"  {size_mb:7.1f} MB  {rec['cliSessionId']}{'   [RUNNING NOW]' if is_live else ''}")
        print(f"             cwd: {rec['cwd']}")
        print(f"           title: {rec['title']}")
        print(f"            file: {target}\n")
    live_written = [r for _, r, _, is_live in written if is_live]
    if live_written:
        print(f"  !! {len(live_written)} of these is/are running in a CLI right now. EXIT the CLI "
              f"before opening one in Desktop — two processes appending to the same transcript "
              f"will corrupt it.\n", file=sys.stderr)
    print_skips(skipped)
    if not args.apply:
        print("\n(dry run — add --apply to write, or --pick N to write chosen rows)")
    else:
        print("\nRestart the Desktop app: it reads this directory at startup.")


if __name__ == "__main__":
    main()
