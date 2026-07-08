# Templates

> Project starters for two of the author's main project types: Python research packages and static personal sites. Each template is a minimal-but-complete scaffold that the `setup/init-agent-harness` skill (P8) composes with the rules / hooks / skills / tooling from the rest of the lib.

## Master TOC

- [How to use](#how-to-use)
- [Template index](#template-index)
- [Adding a new template](#adding-a-new-template)

## How to use

The recommended path is via the setup skill:

```
/init-agent-harness   # asks: project type, bilingual? primary language? install which? then scaffolds
```

For manual use:

1. Pick a template directory
2. Copy its contents into your new project
3. Replace `<PLACEHOLDERS>` (project name, package name, description, author) with real values
4. Drop the relevant `tooling/python-uv-ruff/pyproject.template.toml` (or other tooling templates) on top
5. Add `@import` lines to `CLAUDE.md` for whichever rules apply to your project type

The template's `TEMPLATE_README.md` documents the specific substitutions per template.

## Template index

| Template | Project type | Includes |
|---|---|---|
| [research-package-py/](research-package-py/TEMPLATE_README.md) | Python research package (uv + ruff + pytest) | CLAUDE.template.md, pyproject.template.toml (with research extras), .gitignore, .claude/settings.template.json (ruff format hook), .claude/skills/verify/ |
| [personal-cite-static/](personal-cite-static/TEMPLATE_README.md) | Static personal academic site (HTML/CSS/JS, i18n) | CLAUDE.template.md (bilingual + Master TOC + visual verification rules), index.template.html (i18n-aware), locales/{en,zh}.template.json, .claude/settings.template.json (jq JSON validity hook), .claude/skills/{preview,verify-visual,i18n-sync}/ |

## Adding a new template

See [`docs/CONTRIBUTING.md`](../docs/CONTRIBUTING.md) §"Adding a template". Each template should:

- Be **minimal-but-complete** — enough that a user can run `setup/init-agent-harness` and get a working project
- Use `<PLACEHOLDER>` markers for project-specific bits (project name, package name, etc.)
- Reference `tooling/` and `rules/` rather than duplicating their content
- Include a `TEMPLATE_README.md` listing the placeholders and any required post-setup steps
