---
name: publish
description: Tag a new version of agent-harness, push to GitHub, and create a GitHub release. Use when shipping a meaningful update (new rules, new templates, etc.). Asks for SemVer bump and writes release notes from git log.
disable-model-invocation: true
---

# /publish

Cut a new release of `agent-harness`.

## Usage

```
/publish [<patch|minor|major>]
```

If no bump type is given, asks interactively.

## Pre-flight

- Verify the working tree is clean (`git status` — no uncommitted changes)
- Verify on `main` branch (not a feature branch)
- Verify origin is `git@github.com:jajupmochi/agent-harness.git` (or HTTPS equivalent)
- Verify `gh` CLI is authenticated (`gh auth status`)

## Steps

1. **Determine current version**:

   ```bash
   git tag --list 'v*' --sort=-v:refname | head -1
   ```

   If no tags exist, current version is `v0.0.0`.

2. **Ask user** for bump type (or use the argument):
   - `patch` (v0.1.0 → v0.1.1) — bug fix, doc tweak, no API change
   - `minor` (v0.1.0 → v0.2.0) — new rule / skill / hook / recommendation, no breaking change
   - `major` (v0.1.0 → v1.0.0) — breaking change to consumer interface (rare)

3. **Compute new version** and confirm with user.

4. **Generate release notes** from git log since last tag:

   ```bash
   git log <prev-tag>..HEAD --oneline | grep -E '^\w+ (feat|fix|docs|chore|refactor)' > /tmp/release-notes.md
   ```

   Group by Conventional Commit type. Edit if needed.

5. **Run final verification**:
   - `jq empty` on every `*.json` in the repo
   - Markdown link check (best-effort): `find . -name "*.md" -exec grep -l "](" {} +` — manually skim suspicious entries
   - Privacy scan: invoke `/privacy-redact` on key files (README, INVENTORY, recommendations/) — should report 0 findings before publish

6. **Create the tag**:

   ```bash
   git tag -a <new-version> -m "Release <new-version>"
   git push origin main
   git push origin <new-version>
   ```

7. **Create GitHub release**:

   ```bash
   gh release create <new-version> \
     --title "agent-harness <new-version>" \
     --notes-file /tmp/release-notes.md
   ```

8. **Optional**: announce the release (Telegram channel, blog, etc. — out of this skill's scope).

## Anti-patterns

- ❌ Tagging without first running the privacy scan — public release, can't easily redact later
- ❌ Skipping the git status check — committing pending work in a release tag is messy
- ❌ Force-pushing the tag (`git push --force origin <tag>`) — breaks any consumer pinning to the version

## Companion

- `docs/CONTRIBUTING.md` — Conventional Commits convention
- `skills/general/privacy-redact/SKILL.md` — required pre-publish scan
