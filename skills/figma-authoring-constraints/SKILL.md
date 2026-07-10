---
name: figma-authoring-constraints
description: Use when a designer asks how to structure a Figma file so it produces clean code, when a design keeps yielding pixel-snapshot output, or when get_variable_defs comes back empty — the 20 Figma-side authoring constraints that make a design cleanly code-able via the Figma MCP.
---

# /figma-authoring-constraints

Figma-side rules that make a design **clean and code-able** *before* it reaches an agent. These are the design
half of the pipeline: the `figma-design-fetch` skill fetches + implements + verifies; **this** is what makes the
fetch worth anything. If a design breaks these, `get_design_context` degrades to a rigid pixel snapshot and
`get_variable_defs` comes back empty — no amount of agent effort fixes a design authored as a flat mockup.

Authoritative source: Figma's [Structure your Figma file for better code](https://developers.figma.com/docs/figma-mcp-server/structure-figma-file/).
Each rule is one executable sentence + a reference. Give this to designers; the `figma-design-fetch`
**pre-fetch lint** enforces a subset (unbound colors · default names · raster nodes · absolute positioning) as
a hard gate.

## Master TOC

- [Variables / tokens (1–5)](#variables--tokens-15)
- [Auto layout (6–9)](#auto-layout-69)
- [Components / variants (10–12)](#components--variants-1012)
- [Naming (13–15)](#naming-1315)
- [Dev Mode / Code Connect readiness (16–18)](#dev-mode--code-connect-readiness-1618)
- [Don't use raster placeholders (19–20)](#dont-use-raster-placeholders-1920)
- [How these map to the MCP gotchas](#how-these-map-to-the-mcp-gotchas)
- [Companion](#companion)
- [Provenance](#provenance)

## Variables / tokens (1–5)

1. **Bind every color, spacing, radius, and font size to a Figma variable — never a bare literal.** This is
   exactly what `get_variable_defs` returns; unbound values force the agent to eyeball hex.
   ([Figma](https://developers.figma.com/docs/figma-mcp-server/structure-figma-file/), [variables guide](https://help.figma.com/hc/en-us/articles/15339657135383-Guide-to-variables-in-Figma))
2. **Build two token tiers: primitive → semantic.** Primitives hold raw values (color ramps / spacing steps);
   semantics alias them by UI role (page background / primary action / danger text).
   ([zeroheight](https://zeroheight.com/blog/figma-variables-and-design-tokens-part-one-variable-architecture/))
3. **Name semantic tokens by *intent*, not appearance** — `text/subdued` (survives dark mode), not `text/gray`
   (breaks the moment a mode is added).
4. **Prefer variables over styles for anything tokenizable** (variables carry modes/themes, scoping, and
   code-syntax handoff); reserve styles for what variables can't express — gradients / compound fills / shadows.
   ([Figma](https://help.figma.com/hc/en-us/articles/18490793776023-Update-1-Tokens-variables-and-styles))
5. **Set a "code syntax" on variables** so handoff / MCP emits the real code-side token name, not the Figma label.

## Auto layout (6–9)

6. **Every container uses auto layout — no absolute positioning.** Auto layout is what tells the agent the
   responsive intent, and it maps cleanly to flexbox.
   ([Figma](https://developers.figma.com/docs/figma-mcp-server/structure-figma-file/), [auto layout guide](https://help.figma.com/hc/en-us/articles/360040451373-Guide-to-auto-layout))
7. **Set padding / gap / direction / alignment in the auto-layout panel, don't hand-nudge** — they map directly
   to `padding` / `gap` / `flex-direction` / alignment.
8. **Use hug vs fill deliberately** (buttons/cards hug = content-sized; sections fill = `flex-grow:1`); don't mix
   fill children under a hug parent.
9. **Nest auto-layout frames to express the real DOM hierarchy** (header + content each with its own padding/gap).

## Components / variants (10–12)

10. **Componentize anything reused** (button / card / input / nav item).
11. **States of one thing = variants; genuinely different things = different components**; organize by named
    properties (Size / State). ([variants](https://help.figma.com/hc/en-us/articles/360056440594-Create-and-use-variants))
12. **Make every interactive state a variant** (default / hover / active / focus / disabled) so the agent has an
    implementable state to build.

## Naming (13–15)

13. **Replace default names with intent names**: `Frame1268` / `Group5` → `CardContainer` / `ProductImage` /
    `CTA_Button`.
14. **Match component names to what developers call them in code**, encoding hierarchy with `/`
    (`Button/Primary/Default`); write the convention down before the first component.
    ([LogRocket](https://blog.logrocket.com/ux-design/design-to-code-with-figma-mcp/))
15. **Give pages / sections / frames clear, navigable names** — think about how a developer or agent finds this
    frame. ([Dev Mode guide](https://help.figma.com/hc/en-us/articles/15023124644247-Guide-to-Dev-Mode))

## Dev Mode / Code Connect readiness (16–18)

16. **Use Code Connect to link Figma components to real code** — Figma calls it the first path to consistent
    code-side reuse; without it the model can only guess. (Needs Org/Enterprise; without it, use the markdown
    `Need→Token` contract from #2/#13.)
17. **Use annotations + dev resources** to convey intent visuals can't (behavior / alignment / responsiveness;
    link to the real component / doc).
18. **Select small frames (one Card, one Header), not big heavy frames** — small selections keep the MCP context
    controllable and the output predictable.
    ([custom rules](https://developers.figma.com/docs/figma-mcp-server/add-custom-rules/))

## Don't use raster placeholders (19–20)

19. **Never hand the agent a flattened / rasterized mockup or a pure-image frame** — an image has no semantics,
    so the model only produces a pixel snapshot that drifts from the design system. Build with real layers +
    variables + components. ([LogRocket](https://blog.logrocket.com/ux-design/design-to-code-with-figma-mcp/))
20. **Avoid unnamed / deeply-nested layers mixed with tokens** (the inverse of #13/#2).

## How these map to the MCP gotchas

- **Empty `get_variable_defs`** = the design bound no variables (not an MCP bug). #1–#5 are the fix; the
  `figma-design-fetch` pre-fetch lint makes "variables bound" a gate before code-gen.
- **`get_design_context` quality tracks structure** — auto layout / componentization / semantic names / Code
  Connect are exactly what make it emit componentized code instead of a div-soup.
- **Low-fidelity mockup → pixel snapshot** = breaking #19; the fix is entirely on the design side.
- **Code Connect paywall** (needs Dev/Full seat + Org/Enterprise): when you lack it, #2/#13's markdown
  `Need→Token` table + component barrel is the substitute mapping contract.

## Companion

- `figma-design-fetch` — the agent-side pipeline that consumes a design authored to these rules; its pre-fetch
  lint enforces #1 / #6 / #13 / #19 as a gate.

## Provenance

The Figma-side (Part B) half of the Figma→code pipeline, distilled from Figma's official "structure your file"
guidance + the aliafsahnoudeh reference project. Kept as a standalone designer-facing spec so the design and the
agent-side pipeline evolve together.
