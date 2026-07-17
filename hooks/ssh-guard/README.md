# ssh-guard

A **PreToolUse(Bash)** hook that blocks **SSH username-probing** — trying several different usernames
against one host in a short burst. That pattern trips fail2ban's sshd jail and IP-bans you from the
host; because an agent and its human usually share one egress IP, it locks the human out too.

Enforces the [`no-ssh-username-probing`](../../rules/no-ssh-username-probing/RULE.md) rule. Deterministic, no LLM.

## What it does

- Watches `ssh` / `scp` / `sftp` commands for `user@host` tokens.
- Records, per host, which usernames were used (in a small state dir).
- **Blocks the 2nd _distinct_ username to the same host within a window** (default 30 min) — the
  brute-force signature fail2ban reacts to. Exit 2 blocks the tool call and prints why.
- **Allows** same-user retries (that's a retry, not probing), a first username to a new host, bare
  `ssh host` (no explicit user), and everything non-SSH.
- **Fail-open**: any parse/tooling error exits 0 (allow). A guard must never wedge unrelated shell work.

## Why

See the rule doc for the full story. Short version: on 2026-07-17 an agent probed candidate usernames
against a prod box, fail2ban banned the shared egress IP on port 2222, and it looked like an outage
while also locking out the human. The correct username was in the repo's `deploy.yml` all along.

## Install

Merge `settings.snippet.json` into your `~/.claude/settings.json` (or the project `.claude/settings.json`),
or add the equivalent `PreToolUse` matcher for `Bash` pointing at `ssh-guard.sh`.

## Override (rare)

If `user@host` is a genuinely separate legitimate account (not probing), allow exactly one:

```bash
touch "$HOME/.claude/agent-harness/hooks/ssh-guard/.state/allow-ssh-user-once"   # consumed on the next SSH
```

## Config (env vars)

- `SSH_GUARD_STATE` — state dir (default `hooks/ssh-guard/.state`).
- `SSH_GUARD_WINDOW` — probing window in seconds (default `1800`).

## Known scope

- Detects the `user@host` form (the incident's pattern). The `-l <user> <host>` form and bare
  `ssh host` (default user) are not tracked — the former is a small gap, the latter can't probe.
- State is per-host TSV files; they accumulate harmlessly (tiny). Delete `.state/` to reset history.

## Test

```bash
bash test_ssh_guard.sh    # 13 cases: allow/block/override/email-not-probing/fail-open
```
