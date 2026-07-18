# Hooks

> Reusable hook recipes — deterministic shell commands that run on Claude Code lifecycle events. Drop the `settings.snippet.json` of each hook into a project's `.claude/settings.json` to enable.

## Master TOC

- [How to install a hook](#how-to-install-a-hook)
- [Hook index](#hook-index)
- [Adding a new hook](#adding-a-new-hook)

## How to install a hook

In a project's `.claude/settings.json`, merge the hook's `settings.snippet.json` under the `hooks` key. If the project has no settings.json yet, the snippet IS the file.

For merging into an existing settings.json:

```bash
# from project root, given <hook-name>:
jq -s '.[0] * .[1]' .claude/settings.json hooks/<hook-name>/settings.snippet.json > .claude/settings.json.new && mv .claude/settings.json.new .claude/settings.json
```

Verify the merge with `cat .claude/settings.json | jq .` (any error → fix syntax before continuing).

## Hook index

7 hooks, matching `inventory.hooks` in [`adapters/manifest.source.json`](../adapters/manifest.source.json).

| Hook | Event | Matcher | Context | Why |
|---|---|---|---|---|
| [`ruff-format-on-edit`](ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | research-pkg / any Python project | Auto-format Python files after Claude edits them |
| [`jq-validate-json`](jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | static-site (i18n) / any JSON-config project | Block next tool call if Claude wrote invalid JSON to selected paths |
| [`typecheck-on-edit`](typecheck-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | frontend / any TypeScript project | After a `.ts(x)` edit: `prettier --write` then `tsc --noEmit`; type errors **exit 2** and block the turn. Ships `typecheck.sh` + tests |
| [`block-env-read`](block-env-read/README.md) | `PreToolUse` | `Read` | any repo carrying secrets | Deny reading `.env` / `.env.*` / `*.env` so secrets stay out of the transcript (exit 2). Ships `block-env.sh` + tests |
| [`ssh-guard`](ssh-guard/README.md) | `PreToolUse` | `Bash` | any project with SSH access to hosts | Block SSH username-probing — a 2nd distinct `user@host` in a short burst — the pattern that trips fail2ban and IP-bans you (and your human, via the shared egress IP). Same-user retries pass. Exit 2. Ships `ssh-guard.sh` + 13 tests |
| [`review-gate`](review-gate/README.md) | `PostToolUse` + `Stop` + `PreToolUse` | `Write\|Edit`, `Bash` | any repo where an agent writes code | Un-skippable review of every code-changing turn, the layer skills and rules cannot cover because they are model discretion. T0 logs each changed file, T1 blocks the `Stop` until linters are clean and one review round has produced a Markdown report, T2 leaves `git commit` free but blocks remote publishing unless the project is on `push-whitelist.txt`. Every block is exit 2, so the agent keeps working on everything else |
| [`task-ledger`](task-ledger/README.md) | `Stop` + `UserPromptSubmit` | — | any round with more than about ten sub-tasks | One task document per round, since the failure being fixed is the model's memory rather than its care. The `Stop` gate refuses to end the round while a task is open, a task is marked done without evidence, or a mid-run requirement is untriaged; the `UserPromptSubmit` capture records mid-round requirements before they can be forgotten |

## Adding a new hook

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a hook". Each hook lives under `hooks/<kebab-name>/` with:

- `README.md` — what it does, which event/matcher, install steps, gotchas, variants
- `settings.snippet.json` — drop-in JSON to merge into a project's `.claude/settings.json`
- `verify.sh` (optional) — script to test the hook manually

Hooks are sensitive — pipe-test the raw command first, then wrap in JSON. The `update-config` skill (Anthropic-official) has the canonical hook construction flow including pipe-test → JSON-wrap → live-proof.
