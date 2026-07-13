# Global agent-harness guidance

- Use installed agent-harness skills proactively when their descriptions match; announce the skill briefly before using it.
- For non-trivial work, follow research -> design -> plan -> execute -> verify, with evidence before success claims.
- Preserve user changes and avoid destructive git or file operations without explicit approval.
- Prefer `rg`/`rg --files`, concise human-readable output, and Chinese for final user-facing replies unless requested otherwise.
- Run relevant tests and validation before claiming code, scripts, or results work; add regression coverage for bug fixes.
- Keep durable repo-specific instructions in the nearest `AGENTS.md`; keep this global file small.
- Delegate only bounded, independent work when the user or applicable instructions request parallel agents.
- Model routing: main thread `gpt-5.6-sol` at `xhigh`; explorer and worker agents `gpt-5.6-terra` at `high`; reviewer `gpt-5.6-terra` at `xhigh`; mechanical work `gpt-5.6-luna` at `medium`.
- User hooks are installed in `~/.codex/hooks.json`. Trust them with `/hooks`; an already-running task may still require manual equivalent checks or a new task before lifecycle events fire.
