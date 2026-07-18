# Consumption

> Three ways to use this library in a downstream project. Choose at `setup/init-agent-config` time, or mix.

> **Language:** English | [中文](CONSUMPTION.zh.md)

## Master TOC

- [Option A: Raw URL imports](#option-a-raw-url-imports)
- [Option B: Local clone + @ imports](#option-b-local-clone--imports)
- [Option C: Plugin install](#option-c-plugin-install)
- [Comparison](#comparison)
- [Mixing modes](#mixing-modes)

## Option A: Raw URL imports

Your project's `CLAUDE.md` includes lines like:

```markdown
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/pre-edit-confirmation/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/phased-planning/snippet.md
```

**Pros:** always live (any rule update lands without action), no clone, easy to discover (Claude follows the link), zero local setup.

**Cons:** requires network on session start; rate-limit risk if you import many; harder to override locally without forking.

## Option B: Local clone + @ imports

Once:

```bash
git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness
```

Then in a project's `CLAUDE.md` (or `~/.claude/CLAUDE.md` for global):

```markdown
@~/.claude/agent-harness/rules/pre-edit-confirmation/snippet.md
```

**Pros:** faster session start (no network), offline-friendly, easy to override locally (edit the cloned file), can pin to a specific commit/tag.

**Cons:** manual `git pull` to get updates; out-of-sync risk if you edit locally and forget.

## Option C: Plugin install

Once Phase 10 ships `.claude-plugin/plugin.json`:

```bash
/plugin install jajupmochi/agent-harness
```

**Pros:** most native — exposes the setup skill as `/init-agent-config` slash command, registers selected rules / hooks / skills automatically, marketplace-managed updates.

**Cons:** only works after Phase 10. Adds an indirection; debugging "where does this rule come from" is one step harder.

## Comparison

| Axis | A: Raw URL | B: Local clone | C: Plugin |
|---|---|---|---|
| Network at session start | required | none | partial |
| Update mechanism | automatic (live) | `git pull` | `/plugin update` |
| Override locally | requires fork | edit clone | requires fork |
| Setup skill exposed as `/`-command | no | partial (manual call) | yes |
| Available today (Phase 1) | yes | yes | not yet |
| Pin a version | requires URL pinning | `git checkout <tag>` | requires plugin version |

## Mixing modes

You can combine. Common pattern:

- **Global** `~/.claude/CLAUDE.md` uses **Option B** (cloned) for stability and offline use.
- **Per-project** `CLAUDE.md` uses **Option A** (raw URL) to import only the project-relevant subset (e.g. just the static-site rules).
- **Once C ships**, swap one or both to plugin form for slash-command UX.

The `setup/init-agent-config` skill (Phase 8) writes the right form into a new project's `CLAUDE.md` based on the user's preference.
