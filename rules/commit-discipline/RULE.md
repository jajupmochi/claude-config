---
name: commit-discipline
description: Every git commit MUST follow conventional-commit format (`type(scope): description`) — valid types feat/fix/docs/style/refactor/perf/test/chore/ci/build/revert. No empty or one-word messages; include a scope when the change touches a specific module. For non-native models (DeepSeek etc.) the `commit-msg` hook from scripts/codex_commit_msg.sh enforces it.
scope: universal
---

# commit-discipline

**Priority:** high

Every git commit MUST follow conventional commit format:

```
type[(scope)]: description
```

Valid types: feat fix docs style refactor perf test chore ci build revert

## Rules

1. No empty commit messages.
2. No one-word commits.
3. Always include a scope when the change affects a specific module.
4. Description must be present-tense and descriptive.

## DeepSeek / non-native model enforcement

DeepSeek and other non-native models tend to skip commit messages or use
generic ones. When using these models, the pre-commit hook at
`.git/hooks/commit-msg` (installed via `scripts/codex_commit_msg.sh`) blocks
non-conforming commits. Always verify the hook is installed:

```bash
test -x .git/hooks/commit-msg || cp scripts/codex_commit_msg.sh .git/hooks/commit-msg
```

## Examples

GOOD:
- feat(hooks): add Codex review-gate Stop listener
- fix(ci): update bin check to agent-harness
- docs: rename project to agent-harness

BAD:
- update
- fix
- (empty message)
