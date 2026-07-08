# PUBLISHING.md — How to publish agent-harness to external directories

> Status of each publishing channel and the exact steps to complete it. Some are automated end-to-end; others require manual form-fill due to platform constraints (Anthropic doesn't accept GitHub PRs to the official plugin marketplace; npm requires interactive `npm login`).

## Master TOC

- [Status overview](#status-overview)
- [1. awesome-claude-code (PR — almost auto, one click left for you)](#1-awesome-claude-code-pr--almost-auto-one-click-left-for-you)
- [2. Anthropic plugin marketplace (manual form)](#2-anthropic-plugin-marketplace-manual-form)
- [3. claudemarketplaces.com / buildwithclaude.com (likely auto)](#3-claudemarketplacescom--buildwithclaudecom-likely-auto)
- [4. npm registry (manual `npm login` + `npm publish`)](#4-npm-registry-manual-npm-login--npm-publish)
- [5. GitHub Topics (auto via gh CLI)](#5-github-topics-auto-via-gh-cli)

## Status overview

| Channel | What was auto-done by the assistant | What you need to do manually |
|---|---|---|
| 1. awesome-claude-code (`hesreallyhim/awesome-claude-code`) | Forked the repo, added a row to `THE_RESOURCES_TABLE.csv`, pushed branch `add-agent-harness` to fork | **Click the URL in §1 below to open the PR** (gh CLI hit a cross-repo permission quirk; one click in browser finalizes it) |
| 2. Anthropic plugin marketplace (clau.de form) | Nothing — Anthropic doesn't accept programmatic submissions | **Fill in the form at https://clau.de/plugin-directory-submission** with the prepared text in §2 |
| 3. claudemarketplaces.com / buildwithclaude.com | Nothing — these auto-aggregate from GitHub repos with `.claude-plugin/plugin.json` | Probably auto-listed within ~24h. Check the site after a day. Optional: fill any form to expedite |
| 4. npm registry | Created `package.json` + `bin/install.js`; verified name `agent-harness` is available on npm | **Run `npm login` + `npm publish`** in `~/.claude/agent-harness` (must be you — npm 2FA requires your token in keychain) |
| 5. GitHub Topics | Nothing — needs `gh repo edit` (could be auto if you want; see §5 for the command) | Run the `gh repo edit` one-liner in §5 |

---

## 1. awesome-claude-code (PR — almost auto, one click left for you)

The Awesome Claude Code list at [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) (41k+ stars) accepts community contributions via PR. New entries are added to a single CSV file (`THE_RESOURCES_TABLE.csv`) which their CI then propagates to the README and 35 alternative sorted views.

### What I did automatically

1. Forked `hesreallyhim/awesome-claude-code` into `jajupmochi/awesome-claude-code`
2. Synced the fork with upstream main
3. Created branch `add-agent-harness`
4. Appended one CSV row with the resource metadata (ID, name, category=`Agent Skills`, sub-category=`General`, link, description, license=`MIT`, dates, etc.)
5. Committed with message: `Add resource: agent-harness`
6. Pushed the branch to the fork

### Why I couldn't open the PR programmatically

`gh pr create` and the REST API both returned a permission error for cross-repo PR creation despite the auth token having the `repo` scope. This is a known gh CLI quirk for forks where the upstream has specific PR-from-fork settings. **The fork + branch are ready; one click in the browser finalizes the PR.**

### What you need to do (one click)

**Open this URL in your browser:**

> https://github.com/jajupmochi/awesome-claude-code/pull/new/add-claude-config

GitHub will pre-fill the source/target. **Use the prepared title + body below** (or just confirm the auto-generated ones — the commit message already matches the PR title format their maintainers expect).

### PR title

```
Add resource: agent-harness
```

### PR body (paste this if not auto-filled)

````markdown
### Resource Information

- **Display Name**: agent-harness
- **Category**: Agent Skills
- **Sub-Category**: General
- **Primary Link**: https://github.com/jajupmochi/agent-harness
- **Author Name**: jajupmochi
- **Author Link**: https://github.com/jajupmochi
- **License**: MIT

### Description

Curated Claude Code config library: 9 workflow rules (pre-edit confirmation, phased planning, plugin preflight, autonomous UI iteration loop with chrome-devtools, output brevity, tool proactivity, no-reread-files, chinese-output, bilingual-docs), 5 skills (verify-template, preview-template, long-running-tasks, verify-visual, privacy-redact), 2 hooks (ruff format-on-edit + jq JSON validity), 12 plugin/tool recommendation lists, and 2 project templates (Python research package + static personal site). Run `/init-agent-harness` post-install to scaffold any project with the matching subset.

Six install methods verified by a GitHub Actions install matrix: npx, /plugin interactive, /plugin install direct, local clone, raw URL @imports, copy-paste prompt. Privacy/secret scan workflow with gitleaks + custom patterns. Bilingual top-level docs, 4 meta-skills for self-extension.

### Automated Notification

- [x] This is a GitHub-hosted resource and will receive an automatic notification issue when merged
````

After clicking "Create pull request", their automated review checks the CSV format. Maintainers usually merge within a few days.

---

## 2. Anthropic plugin marketplace (manual form)

Per [the official docs](https://code.claude.com/docs/en/plugins) and confirmed via web search:

> ⚠️ **Anthropic does NOT accept GitHub PRs** to `anthropics/claude-plugins-official`. Direct PRs to that repo are auto-closed. **All submissions go through their submission form.**

### Submission URL

**Use exactly one** of these:

- **Web form**: https://clau.de/plugin-directory-submission
- **In-app**: https://platform.claude.com/plugins/submit (login with your Anthropic account)

### What to fill in

The form fields (based on the official docs and example submissions) are typically:

| Field | Value |
|---|---|
| **Plugin name** | `agent-harness` |
| **GitHub repository URL** | `https://github.com/jajupmochi/agent-harness` |
| **Plugin manifest path** | `.claude-plugin/plugin.json` |
| **Version** | `0.1.0` |
| **Author / GitHub handle** | `jajupmochi` |
| **License** | `MIT` |
| **Category** | `Skills` (primary) — or `Tooling` if "Skills" doesn't fit |
| **Tags / keywords** | `claude-code`, `skills`, `hooks`, `scaffold`, `config`, `workflow`, `rules`, `templates` |
| **Short description** (one-liner) | `Curated Claude Code configuration: workflow rules, skills, hooks, plugin recommendations, tooling preferences, and project templates. Run /init-agent-harness to scaffold any project.` |
| **Long description** | (Use the awesome-claude-code description from §1 above — it covers the same ground) |
| **Documentation URL** | `https://github.com/jajupmochi/agent-harness#readme` |
| **Issue tracker URL** | `https://github.com/jajupmochi/agent-harness/issues` |
| **Demo / video URL** | (optional — leave blank unless you record one) |
| **Screenshots** | (optional — could attach the README "Build history" table or the install matrix CI badge) |

### Review process

1. Anthropic runs **automated review** (CSV-style checks: manifest validity, links resolve, etc.) — should pass since the install-verify CI already validates `.claude-plugin/plugin.json` and all linked paths
2. Anthropic may run **manual quality + security review** — if it passes, you get the **"Anthropic Verified"** badge
3. The plugin appears in the official marketplace, accessible via `/plugin` interactive browser

Timeline: per Anthropic's docs, "basic automated review" → minutes to hours. "Verified" review → days to weeks.

### Status check after submission

After submitting, you can check the plugin's appearance at:
- https://claude.com/plugins (official directory)
- https://github.com/anthropics/claude-plugins-official/blob/main/.claude-plugin/marketplace.json (raw marketplace manifest — search for `agent-harness`)

---

## 3. claudemarketplaces.com / buildwithclaude.com (likely auto)

These third-party directories aggregate Claude Code plugins from GitHub:

- [claudemarketplaces.com](https://claudemarketplaces.com/) — claims "4,200+ skills, 770+ MCP servers, 2,500+ marketplaces"; sorted by installs and GitHub stars
- [buildwithclaude.com](https://buildwithclaude.com/) — similar plugin marketplace directory

Most likely they **auto-discover** any GitHub repo with `.claude-plugin/plugin.json` and the `claude-code` topic on the repo. Should appear within ~24 hours of meeting both conditions.

### What to do

1. Make sure GitHub Topics are set on the repo (see §5) — especially `claude-code`, `skills`, `hooks`
2. Wait ~24 hours, then check:
   - https://claudemarketplaces.com/ → search for `agent-harness`
   - https://buildwithclaude.com/ → search for `agent-harness`
3. If not auto-listed after 48h, look for a "Submit" button on each site (some have a form)

No action prepared in advance because the auto-discovery may already cover us.

---

## 4. npm registry (manual `npm login` + `npm publish`)

The package name `agent-harness` is **available on npm** (verified — `npm view agent-harness` returns 404). The repo already has a valid `package.json` + `bin/install.js`.

### Why it's manual

`npm publish` requires:
1. An npm account (free at https://www.npmjs.com/signup)
2. `npm login` (interactive — typically OTP via email or 2FA app, can't be scripted from this assistant)
3. The npm CLI to find the auth token in your keychain at publish time

I can prepare everything but the actual publish must come from your machine after `npm login`.

### Steps for you

```bash
# 1. (One time) Create an npm account at https://www.npmjs.com/signup if you don't have one

# 2. Log in (interactive — opens browser or prompts for OTP)
cd ~/.claude/agent-harness   # or wherever you've cloned
npm login

# 3. Verify you're logged in as the right user
npm whoami

# 4. Publish (verify package.json looks right first)
cat package.json | jq '{name, version, bin, files}'
npm publish --access=public

# 5. Verify
npm view agent-harness
```

After publish, the install command becomes:

```bash
# Old (from GitHub):
npx github:jajupmochi/agent-harness

# New (from npm — slightly faster, registered):
npx agent-harness
```

You should update `README.md` / `USAGE.md` to mention the new npm-registry path as preferred. (Or run `/init-agent-harness` in `~/.claude/agent-harness` and let CC do it for you.)

### Versioning going forward

For future releases, bump the version in `package.json` AND in `.claude-plugin/plugin.json` AND tag the release:

```bash
# Use the /publish meta-skill defined in .claude/skills/publish/SKILL.md
cd ~/.claude/agent-harness
claude
/publish patch    # or minor / major

# Then publish to npm (one extra step beyond what /publish does):
npm publish
```

(Future enhancement: bake `npm publish` into the `/publish` meta-skill — it currently only handles git tag + GitHub release.)

---

## 5. GitHub Topics (auto via gh CLI)

GitHub Topics make the repo discoverable in GitHub search and on third-party aggregator sites. The `claude-code` topic is the canonical one for this ecosystem.

### Run this once

```bash
gh repo edit jajupmochi/agent-harness \
  --add-topic claude-code \
  --add-topic claude-skills \
  --add-topic agent-harness \
  --add-topic claude-plugin \
  --add-topic scaffold \
  --add-topic workflow-rules \
  --add-topic ai-coding \
  --add-topic developer-tools
```

(Run from anywhere — gh CLI uses your auth.)

### Verify

```bash
gh repo view jajupmochi/agent-harness --json repositoryTopics -q '.repositoryTopics[].name'
```

After topics are set, the repo will start appearing in:
- GitHub topic pages: https://github.com/topics/claude-code
- claudemarketplaces.com (if their crawler keys off topics)
- GitHub search filters

This is the only step in this whole list that I (the assistant) can do for you with no friction. Tell me to run it and I will, or run it yourself.

---

## Maintenance: keep the manifests in sync

Three files contain version + metadata that need to stay aligned:

- `package.json` — `name`, `version`, `description`, `bin`, `files`
- `.claude-plugin/plugin.json` — `name`, `version`, `description`, declared skills/rules/hooks
- `README.md` (build-history table) — commit hashes per phase

When publishing a new version (`/publish patch|minor|major`), bump version in both manifests and re-run install-verify CI.

The `/publish` meta-skill in `.claude/skills/publish/SKILL.md` handles the git tag + GitHub release. Currently you also need to manually:
1. Update `package.json` version
2. Update `.claude-plugin/plugin.json` version
3. After tag + release: `npm publish`

Future enhancement: extend `/publish` to do all 3 manifest bumps + npm publish in one shot.

---

## Quick reference

| Channel | Action | URL / Command |
|---|---|---|
| **awesome-claude-code** | Click to open the prepared PR | https://github.com/jajupmochi/awesome-claude-code/pull/new/add-claude-config |
| **Anthropic plugin marketplace** | Fill the submission form | https://clau.de/plugin-directory-submission |
| **3rd-party aggregators** | Wait + verify | https://claudemarketplaces.com/ + https://buildwithclaude.com/ |
| **npm publish** | Run `npm login` + `npm publish` | `npm whoami && npm publish --access=public` |
| **GitHub Topics** | Add discoverability tags | `gh repo edit jajupmochi/agent-harness --add-topic claude-code …` (full command in §5) |
