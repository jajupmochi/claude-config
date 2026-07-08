---
name: long-running-tasks
description: Manage long-running commands and multi-step work in Codex. Use when a task may exceed normal turn time, needs a dev server, watcher, training run, crawl, benchmark, or repeated polling.
---

# long-running-tasks

Read `../general/long-running-tasks/SKILL.md` for the original policy, then use
these Codex mappings:

- Claude background Bash -> Codex background `exec_command` session.
- Claude Monitor -> periodic `write_stdin` polling or explicit status command.
- Claude subagent -> Codex subagent only if available and useful; otherwise use
  a focused plan and background terminal.
- Claude "ask before long run" -> Codex approval when the run needs network,
  writes outside the workspace, high cost, or destructive side effects.

Workflow:

1. Estimate duration and side effects.
2. For commands expected to run longer than a normal tool call, start them in a
   background session and keep the session id.
3. Poll at reasonable intervals. Do not spam the transcript with full logs.
4. Stop or clean up sessions that are no longer needed before final response.
5. If a task is too large for one run, leave a concrete continuation state:
   current command, session id, last observed output, and next check.
