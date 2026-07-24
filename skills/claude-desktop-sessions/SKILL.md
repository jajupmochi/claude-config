---
name: claude-desktop-sessions
description: Use when Claude Code sessions started in the terminal CLI don't appear in the Claude Desktop app's Code tab, when you want to hand a running CLI session to Desktop (and reach it from the phone via Remote Control), or when asked to "import/migrate my CLI sessions into the desktop app". Registers existing sessions in Desktop's sidebar by writing its per-session registry files, which point at the transcript store both apps already share — no transcript is copied or modified. Lists candidates numbered so you can import a chosen subset.
policy:
  allow_implicit_invocation: true
---

# claude-desktop-sessions

Surface terminal-CLI Claude Code sessions in the **Claude Desktop** app's **Code** tab, and hand a
running session off to Desktop (which also makes it reachable from the phone through Remote Control).

## Why the sessions are missing (the root cause)

Desktop and the CLI keep **separate session lists** but **share one transcript store**. The official
docs say it plainly: coming from the CLI, "each maintains separate session history" while sharing
configuration and `CLAUDE.md`. So a session you started in the terminal is never listed by Desktop,
even though Desktop can read its transcript.

Two facts, both verified against Desktop 1.24012.0 (bundled Claude Code 2.1.215) on Linux:

1. **Shared transcript store.** Both write `~/.claude/projects/<encoded-cwd>/<cliSessionId>.jsonl`.
   Desktop's bundle joins `claudeConfigDir` (default `~/.claude`) with `projects` and names files
   `${cliSessionId}.jsonl` — identical to the CLI. So the transcript never needs to move.
2. **Separate sidebar registry.** Desktop's Code sidebar is driven by one small JSON file per
   session at `~/.config/Claude/claude-code-sessions/<accountId>/<workspaceId>/local_<uuid>.json`.
   That file is the only thing the CLI does not create — this skill creates it.

The obvious built-in path, the in-session `/desktop` command, is **compiled off in current builds**:
its gate function returns a hard `false`, so the command is hidden for everyone regardless of account.
Writing the registry file is the working alternative.

The encoded-cwd directory name is the cwd with every non-`[a-zA-Z0-9]` character replaced by `-`
(e.g. `/media/user/New Volume1/projects/2026.04.29_agent_rules` →
`-media-user-New-Volume1-projects-2026-04-29-agent-rules`). The tool reads the real cwd from inside
the transcript rather than trying to reverse this lossy encoding.

## The tool

`scripts/migrate.py` — dry-run by default, writes nothing until told to. It never touches a
transcript and only ever *adds* registry files, so undo is `rm` on the files it names.

```bash
MIG="$(dirname "$0")/scripts/migrate.py"    # or the skill's scripts/migrate.py

python3 migrate.py --list                    # numbered table of registerable sessions (writes nothing)
python3 migrate.py --pick 1,3,5 --apply      # register those rows from the --list numbering
python3 migrate.py --pick 1-4,7 --apply      # ranges work too
python3 migrate.py --session <cliSessionId> --title "My label" --apply   # one exact session, custom title
python3 migrate.py --apply                   # register ALL registerable sessions (use --max-mb to cap size)
```

`--list` numbering is by conversation start time, newest first, and is stable for a following
`--pick` because it sorts on the transcript's immutable first timestamp, not on the file mtime.

### What it refuses to do, and why

- **Deleted sessions stay deleted.** Deleting a session in Desktop writes a `deleted_<id>`
  tombstone; the tool skips tombstoned ids so a batch run never resurrects them. (Deleting a session
  in Desktop does *not* delete its transcript — verified.)
- **`/tmp` scratch sessions are filtered out.** A cwd of `/tmp` or under it (where throwaway sessions
  accumulate — over a thousand on this machine) is skipped.
- **Already-registered and orphaned sessions are skipped** — no duplicate sidebar rows, and a session
  whose cwd no longer exists is left out.
- **A live session is flagged, not silently registered.** If a session is running in a CLI right now
  (`--list`/output marks it `[RUNNING NOW]` and warns on stderr), you must **exit that CLI before
  opening the session in Desktop**. Two processes appending to one transcript corrupts it — the worst
  outcome this tool can cause.

## Handing a running session to Desktop (the safe order)

1. Register it: `python3 migrate.py --session <id> --title "…" --apply`.
2. **Fully quit and reopen Desktop** — it reads the registry directory only at startup.
3. **Exit the CLI** running that session; confirm no `claude` process is still on it.
4. Open the session in Desktop's Code tab. Its history loads from the shared transcript.

Order matters: the CLI must exit before the session is opened in Desktop (step 3 before step 4).

## Remote Control (reaching it from the phone)

Registering a session does not by itself enable Remote Control. For a session to appear on the phone:

- Set `remoteControlAtStartup: true` in `~/.claude/settings.json` (or run `/config` →
  *Enable Remote Control for all sessions*), **and**
- In the Desktop app, enable **Settings → Claude Code → Enable remote control by default**. The
  settings-file flag alone did not make Desktop-hosted sessions connect; the Desktop toggle was
  required. Once both are on, the session shows in the Claude mobile app's Code list.

Remote Control is disabled when `ANTHROPIC_BASE_URL` points anywhere other than `api.anthropic.com`,
so leave that unset.

## Does the session archiver cover Desktop sessions?

Yes, automatically, and for the same reason the migration works: the archiver
(`claude-session-archiver` / worknroll `daily archive`) globs `~/.claude/projects/*/*.jsonl`, which
is exactly where Desktop-hosted Code sessions write. No change is needed for Desktop coverage —
verified that the glob matches a live Desktop session's transcript and that the daily
`wd-archive.timer` picks it up. (Cowork VM sessions are a separate store and out of scope here.)

## Caveats

- **Undocumented schema.** The registry record shape was read off a sample Desktop itself produced. A
  Desktop upgrade may change it; if a migrated session stops opening, re-run after re-reading one
  freshly-created record.
- **Restart required.** New records appear only after Desktop restarts.
- **Huge transcripts are slow to resume.** Desktop opens a session by spawning `claude --resume`;
  a multi-hundred-MB transcript can be slow or memory-heavy. Use `--max-mb` to cap a batch. A 95 MB
  session was verified to open fine; the largest here are ~200 MB.
- **`model`/`effort` are intentionally omitted** from the record, so a migrated session keeps
  whatever model the CLI would pick rather than being silently re-pointed.

## Tests

`scripts/test_migrate.py` — 18 checks, run `python3 scripts/test_migrate.py`. Two are regressions
that lock out real bugs found while building this: a `/tmp` filter that let a bare `/tmp` cwd through,
and a UTC-vs-local timestamp skew. The timestamp test runs under a non-UTC timezone on purpose,
because the bug is invisible under `TZ=UTC`.
