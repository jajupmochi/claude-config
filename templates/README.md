# Templates

> Project starters for the author's two main project types, Python research packages and static personal sites, plus one add-on for repositories that already exist. Each template is a minimal-but-complete scaffold that the `setup/init-agent-config` skill (P8) composes with the rules / hooks / skills / tooling from the rest of the lib.

## Master TOC

- [How to use](#how-to-use)
- [Template index](#template-index)
- [Adding a new template](#adding-a-new-template)

## How to use

The recommended path is via the setup skill:

```
/init-agent-config   # asks: project type, bilingual? primary language? install which? then scaffolds
```

For manual use:

1. Pick a template directory
2. Copy its contents into your new project
3. Replace `<PLACEHOLDERS>` (project name, package name, description, author) with real values
4. Drop the relevant `tooling/python-uv-ruff/pyproject.template.toml` (or other tooling templates) on top
5. Add `@import` lines to `CLAUDE.md` for whichever rules apply to your project type

The template's `TEMPLATE_README.md` documents the specific substitutions per template.

## Template index

3 templates, matching `inventory.templates` in [`adapters/manifest.source.json`](../adapters/manifest.source.json).

| Template | Project type | Includes |
|---|---|---|
| [research-package-py/](research-package-py/TEMPLATE_README.md) | Python research package (uv + ruff + pytest) | CLAUDE.template.md, pyproject.template.toml (with research extras), .gitignore, .claude/settings.template.json (ruff format hook), .claude/skills/verify/ |
| [personal-cite-static/](personal-cite-static/TEMPLATE_README.md) | Static personal academic site (HTML/CSS/JS, i18n) | CLAUDE.template.md (bilingual + Master TOC + visual verification rules), index.template.html (i18n-aware), locales/{en,zh}.template.json, .claude/settings.template.json (jq JSON validity hook), .claude/skills/{preview,verify-visual,i18n-sync}/ |
| [actions-frugal-ci/](actions-frugal-ci/TEMPLATE_README.md) | Any repo with GitHub Actions (add-on, not a project starter) | Four tier CI that keeps Actions minutes low: `git-hooks/{pre-commit,pre-push}.template.sh` (both refuse to run half-substituted), `lefthook.template.yml`, `.github/workflows/{ci,heavy,_checks.reusable}.template.yml`. Rationale: [`recommendations/github-actions-frugality.md`](../recommendations/github-actions-frugality.md) |

## Adding a new template

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a template". Each template should:

- Be **minimal-but-complete** — enough that a user can run `setup/init-agent-config` and get a working project
- Use `<PLACEHOLDER>` markers for project-specific bits (project name, package name, etc.)
- Reference `tooling/` and `rules/` rather than duplicating their content
- Include a `TEMPLATE_README.md` listing the placeholders and any required post-setup steps
