# CC Marketplaces + Skill Bundles

> 4 third-party Claude Code marketplaces + 9 skill bundles installed via `npx skills add`. **Context: always** for marketplaces; per-bundle context for skill packs.

## Master TOC

- [Marketplaces](#marketplaces)
- [Skill bundles via `npx skills add`](#skill-bundles-via-npx-skills-add)
- [Install order](#install-order)

## Marketplaces

Add to `~/.claude/settings.json` `extraKnownMarketplaces` block (or via `/plugin marketplace add <github-repo-or-url>`):

| Marketplace | Source | Adds |
|---|---|---|
| `superpowers-marketplace` | `obra/superpowers-marketplace` (GitHub) | `superpowers@claude-plugins-official` and others |
| `minimax-skills` | `MiniMax-AI/skills` (Git) | MiniMax skill pack |
| `garden-skills` | `ConardLi/garden-skills` (GitHub) | web-design / image-gen / knowledge-base |
| `ui-ux-pro-max-skill` | `nextlevelbuilder/ui-ux-pro-max-skill` (GitHub) | UI/UX-focused skills |

**Install:**

```bash
# Interactive:
/plugin marketplace add obra/superpowers-marketplace
/plugin marketplace add MiniMax-AI/skills
/plugin marketplace add ConardLi/garden-skills
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
```

Or directly edit `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "superpowers-marketplace": { "source": { "source": "github", "repo": "obra/superpowers-marketplace" } },
    "minimax-skills":          { "source": { "source": "git",    "url": "https://github.com/MiniMax-AI/skills.git" } },
    "garden-skills":           { "source": { "source": "github", "repo": "ConardLi/garden-skills" } },
    "ui-ux-pro-max-skill":     { "source": { "source": "github", "repo": "nextlevelbuilder/ui-ux-pro-max-skill" } }
  }
}
```

## Skill bundles via `npx skills add`

The `npx skills add <repo>` CLI clones a repo and arranges symlinks under `~/.agents/skills/`. The lock file is `~/.agents/.skill-lock.json`.

| Bundle | Source | What it adds | Context |
|---|---|---|---|
| `gsap-skills` | `https://github.com/greensock/gsap-skills` | Official GSAP animation skills (gsap-core, gsap-timeline, gsap-scrolltrigger, gsap-utils, gsap-react, gsap-frameworks, gsap-plugins, gsap-performance) | `3d-or-animation` |
| `shadcn/ui` | `shadcn/ui` | shadcn-ui add / install / diagnose component skill | `ui-project` |
| `impeccable` | `pbakaus/impeccable` | High-end design plugin (`/impeccable colorize`, `typeset`, `bolder`, `polish`, `harden`, `layout`, `distill`, `critique`) | `ui-project` |
| `huashu-design` | `alchaincyf/huashu-design` | High-fidelity HTML prototyping, slides, animations, design exploration | `ui-project` |
| `remotion-best-practices` | `remotion-dev/skills` | Remotion video creation in React | `optional` |
| `baoyu-skills` | `jimliu/baoyu-skills` | 20+ baoyu-* skills: image-gen, infographics, comics, slide-deck, translation, posting to socials | `optional` |
| `taste-skill` | `Leonxlnx/taste-skill` | Design taste / aesthetic guidance | `ui-project` |
| `ui-skills` | `ibelick/ui-skills` | Frontend UI patterns | `ui-project` |
| `algorithmic-art` | `plurigrid/asi` (algorithmic-art skill) | Algorithmic art with p5.js, seeded randomness | `optional` |

**Install (canonical):**

```bash
# Required: Node + npm (via nvm or system)
which npx || (echo "install Node first"; exit 1)

# Bundles are installed individually:
npx skills add https://github.com/greensock/gsap-skills
npx skills add shadcn/ui
npx skills add pbakaus/impeccable
npx skills add alchaincyf/huashu-design
npx skills add remotion-dev/skills
npx skills add jimliu/baoyu-skills
npx skills add Leonxlnx/taste-skill
npx skills add ibelick/ui-skills
npx skillfish add plurigrid/asi algorithmic-art   # alternate CLI for this bundle
```

After install, the skills appear under `~/.agents/skills/` and are symlinked into `~/.claude/skills/` for CC discovery.

## Install order

For a fresh setup:

1. **Marketplaces first** — they unlock the official `claude-plugins-official` plugins.
2. **`/plugin install` workflow plugins** (see [cc-plugins.md](cc-plugins.md)).
3. **`npx skills add` bundles** based on project type — UI projects get GSAP + shadcn + impeccable + huashu; ML projects skip these.

The `setup/init-agent-config` skill (P8) decides which bundles fit a new project's selected context tags.
