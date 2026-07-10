---
name: figma-design-fetch
description: Use when the user shares a figma.com URL, wants to implement/mock a UI from Figma, or do design-to-code — connect the Figma MCP, fetch the design (code/assets/screenshot) to disk, then rebuild with existing design-system components and visually self-verify against the Figma screenshot.
---

# /figma-design-fetch

The full Figma → code pipeline via the **official Figma MCP**: connect, fetch the design (code / vector /
bitmap / screenshot) to disk, rebuild the screen with the project's **existing token-mapped components + real
data**, and **visually self-verify** against the Figma screenshot until it converges. Agent-assisted with a
**mandatory verification gate** — never paste raw generated code as production UI.

> The reliability of design-to-code comes less from the MCP than from three things you control: **(a)** a
> token-driven, mappable component library, **(b)** this fixed workflow with a **mandatory visual gate**, and
> **(c)** deterministic non-LLM hooks (typecheck, prettier). None depend on your Figma plan.

## Master TOC

- [When to use](#when-to-use)
- [Prerequisites](#prerequisites)
- [Setup A — Connect the Figma MCP (OAuth)](#setup-a--connect-the-figma-mcp-oauth)
- [Setup B — Get a node-specific link](#setup-b--get-a-node-specific-link)
- [Pre-fetch design pre-check lint (gate)](#pre-fetch-design-pre-check-lint-gate)
- [The 5-step pipeline (each step is mandatory)](#the-5-step-pipeline-each-step-is-mandatory)
- [Deterministic hooks (the quality spine)](#deterministic-hooks-the-quality-spine)
- [Gotchas (tested — read before fetching)](#gotchas-tested--read-before-fetching)
- [Figma export options ↔ MCP](#figma-export-options--mcp)
- [References](#references)
- [Companion](#companion)
- [Provenance](#provenance)

## When to use

- The user pastes a `figma.com/design/...` (or `/file/...`) URL.
- The user asks to implement / mock / rebuild a UI *from a Figma design*, or says "design-to-code".
- You need a screen's visual truth, structure, reference code, tokens, or assets to reconstruct it.

## Prerequisites

1. **Figma account + seat**: at least a **Full or Dev seat**. A `starter` (free) tier + Full seat is enough for
   `get_design_context` to emit code; **Code Connect requires an Organization/Enterprise plan** (see gotcha 2).
2. **The Figma MCP is available** — deferred tools `mcp__plugin_figma_figma__*`. If not (do this only if the
   user asks — it changes their config):
   ```bash
   claude mcp add --transport http figma https://mcp.figma.com/mcp   # remote, recommended
   ```
3. **A token-mapped component library** in the target repo (a component barrel + design tokens). The pipeline
   maps Figma values onto these, never hardcoded hex.

> **PAT + local stdio fallback (tradeoff).** The default is the **official remote MCP** (OAuth). Its PKCE flow
> expires in minutes (gotcha 1); if re-auth is too painful you *may* instead run a local stdio server with a
> Personal Access Token — `npx figma-developer-mcp --figma-api-key=<PAT> --stdio` — which has no minute-expiry.
> Cost: a **different, non-official tool surface** (no `get_code_connect_map`, different fetch shape) and you
> hold a PAT. Adopt only if OAuth churn blocks you, and **never commit/print the PAT** (read it from env / a
> gitignored `.figma-token`).

## Setup A — Connect the Figma MCP (OAuth)

1. Call `authenticate` → it returns an **authorization URL**.
2. The **user** opens it, logs into Figma (**never enter the user's password**), clicks **Authorize**
   (read-only `mcp:connect` scope).
3. Redirect `http://localhost:<port>/callback?code=...`: same-machine browser → the local listener auto-completes;
   otherwise the user pastes the **full** address-bar URL back and you call `complete_authentication`.
4. **Verify** with `whoami` → account + seat.

> ⚠️ **Gotcha 1 — OAuth PKCE expires in minutes.** Authorize **within a few minutes of `authenticate`**, else
> `No OAuth flow in progress` → re-run `authenticate`.

## Setup B — Get a node-specific link

`https://www.figma.com/design/<fileKey>/<name>?node-id=<1-23>` → extract `fileKey` (after `/design/`) and
`nodeId` (after `node-id=`; `4001-8` == `4001:8`). The link **must include `node-id`**, and it must be the
**target frame**, not the file cover.

## Pre-fetch design pre-check lint (gate)

**Before generating any code**, check the frame and **warn / stop** if the design won't produce clean code —
these mean it violates the authoring constraints (see the `figma-authoring-constraints` skill) and
`get_design_context` will degrade to a rigid pixel snapshot:

1. **Unbound-variable colors** — colors not bound to Figma variables (→ `get_variable_defs` returns `{}`; you'd
   be forced to eyeball hex).
2. **Default layer names** — `Frame\d+` / `Group\d+` (no semantic structure).
3. **Pure image / rasterized nodes** — a flattened mockup has no semantics → pixel snapshot only.
4. **Absolute-positioned children** — no auto layout → no responsive intent, won't map to flexbox.

On a hit: report it and either go back to Figma to fix the design, or get the user's explicit OK to proceed
with a **degraded (pixel-snapshot) result**. Do not silently generate from a non-conformant frame.

## The 5-step pipeline (each step is mandatory)

### 1. Extract (real values, never estimate from the image)

For the `fileKey` + `nodeId`, call **in order** and record the **real** values (do NOT guess from the picture):

| Tool | What you get |
|---|---|
| `get_design_context` | React + Tailwind reference code + structure + asset URLs |
| `get_metadata` | dimensions / padding / fills / hierarchy / layer names + **annotation text** (intent) |
| `get_variable_defs` | design tokens (**use them if present**; empty `{}` → gotcha 3) |
| `get_screenshot` | the visual **ground truth** (short-lived URL; `curl` it now, it's the diff baseline) |
| `download_assets` | real bitmaps / logos (`defaultFormat=svg` for vector) — **7-day URLs, save now** |
| `get_code_connect_map` | Figma→code component mapping — **only on an Org/Enterprise plan** (gotcha 2) |

Produce a **per-frame design doc** in `<frontend-repo>/.design-imports/<feature>/` (**gitignored**):
spacing(px), fonts, colors (hex → *token TBD*), radius/shadow/opacity, layout, component hierarchy + states,
and a **hand-annotation → requirement** table. Save `export.png` / `design.svg` / `assets/raw_image_*.png` /
`link.txt`.

### 2. Map to the design system (Need→Token contract)

Map **before** writing code — never recreate what exists:

- Open the component **barrel** (e.g. `components/src/index.ts`), enumerate **existing** components, and pick one
  existing wrapper for each Figma element.
- Map Figma colors/spacing onto **tokens** (`primary.main`, `theme.spacing(n)`, …). **Never hardcode
  `#xxx` / `rgb()`.**
- **Code Connect needs Org/Enterprise.** Without it, keep a hand-maintained **`Need → Token` markdown table +
  the component barrel** as the mapping contract (this is what the reference project does). Keep the table even
  if you later get Code Connect — it's the human-readable fallback. Empty `get_variable_defs` → read concrete
  values from `get_design_context` code / the exported CSS and record them in this table.

### 3. Implement

Use **only design-system components**; split by domain; put logic in `use-*.ts` hooks; wire **real backend
data** (not placeholders). Do not paste raw `get_design_context` output as production code — it's context.

### 4. Visual self-check (mandatory gate)

1. Start the local app → Playwright `browser_navigate` to the route →
   **`browser_resize` to the Figma frame's EXACT dimensions** (critical — only same-size images compare) →
   `browser_take_screenshot` → `get_screenshot` for the same node → compare layout / spacing / fonts / colors /
   radius / shadow / states → **on any difference, go back to step 3 and loop until aligned.**
2. **Objective gate (our hardening over "the model eyeballs it").** On top of the model's judgment, run a
   numeric check at the exact frame size + a **fixed DPR**: `pixelmatch` (or SSIM) with a **numeric pass
   threshold**, so "matches" is not just the model's subjective opinion. A helper is provided:
   ```bash
   node skills/figma-design-fetch/scripts/visual-diff.mjs <impl.png> <figma.png> [--threshold 0.02] [--dpr 2]
   #  → exits non-zero if the mismatch fraction exceeds the threshold; writes a diff PNG next to the inputs.
   ```
   Capture both PNGs at the **same pixel dimensions and DPR**, or the metric is meaningless.

### 5. Report

New/changed components · the token mapping (Figma value → token) · anything that did **not** map cleanly · the
visual-diff result (mismatch fraction vs threshold).

## Deterministic hooks (the quality spine)

Wire these agent-harness hooks in the frontend repo so quality doesn't depend on the model remembering:

- **`typecheck-on-edit`** (`PostToolUse`) — after a `.ts(x)` edit, `prettier --write` then `tsc --noEmit`;
  **type errors `exit 2` and block the turn**. `hooks/typecheck-on-edit/`.
- **`block-env-read`** (`PreToolUse`) — deny reading `.env*` so secrets stay out of the transcript.
  `hooks/block-env-read/`.
- Keep git / destructive shell off the agent's tool allowlist.

## Gotchas (tested — read before fetching)

> ⚠️ **1. OAuth PKCE expires in minutes** → authorize promptly; re-issue on `No OAuth flow in progress`.

> ⚠️ **2. Code Connect is paywalled** → auto-mapping to your React components (`get_code_connect_map`) needs
> **Org/Enterprise**. Without it, map **manually** via the Need→Token table + barrel.

> ⚠️ **3. `get_variable_defs` returns empty** = the design bound **no Figma variables** → read concrete values
> from `get_design_context` / exported CSS. Fix at the design side (see `figma-authoring-constraints`).

> ⚠️ **4. Low-fidelity spec mockups** → `get_design_context` returns a **pixel snapshot** (`absolute` +
> `<img>`), not componentized code. Do not paste verbatim. This is what the pre-check lint catches.

> ⚠️ **5. Asset URLs expire in ~7 days** (renders ~minutes) → `curl` to disk immediately. Prefer
> token/component rendering; use `download_assets` only for real bitmaps/logos, consumed at once.

> ⚠️ **6. Browser auto-login scraping: not recommended** — can't enter the user's password, Figma's canvas is
> WebGL (unscrapeable), and it's redundant with (and worse than) the official MCP.

## Figma export options ↔ MCP

| Figma option | What it is | MCP equivalent |
|---|---|---|
| PNG | raster render | `download_assets` (default png) / `get_screenshot` |
| SVG | vector export | `download_assets(defaultFormat=svg)` |
| **CSS code** | CSS of the one selected layer | `get_design_context` (React+Tailwind, not raw single-element CSS) |
| **CSS (all layers)** | flat absolute-positioned dump of the subtree | `get_design_context` (**nested** React+Tailwind, richer) |
| Property / Inspect | dimensions / spacing / typography | `get_metadata` + `get_variable_defs` |
| **iOS / Android code** | native SwiftUI / Compose | none — not needed for a web frontend |

## References

Cite, don't copy:

- Pipeline (Part A flow + Part B design constraints): `neobanker-docs` →
  `docs/platform/guides/figma-to-code-pipeline.md`.
- Fetch flow + the 6 gotchas: `neobanker-docs` → `docs/platform/guides/figma-mcp-fetch-tutorial.md`.
- Reusable REST-API script (PAT): `neobanker-frontend-MVP-V3` → `.design-imports/figma-fetch.sh`.
- Reference implementation (method, not code): <https://github.com/aliafsahnoudeh/figma-to-code-claude-pipeline>.

## Companion

- `figma-authoring-constraints` — the Figma-side design constraints (Part B) that make a design cleanly
  code-able; the pre-check lint above enforces a subset as a gate.
- `verify-visual` — screenshot + self-critique loop (step 4).
- `typecheck-on-edit`, `block-env-read` — the deterministic hooks referenced above.
- `ui-iteration-loop` rule — the autonomous visual-convergence loop.

## Provenance

Distilled from a Neo Horizon design-to-code run (official Figma MCP, tested end-to-end) plus the
aliafsahnoudeh reference pipeline, adapted to the official MCP. Consolidated into `agent-harness` so any session
hitting a Figma design follows the tested flow, maps to the design system instead of eyeballing pixels, and
verifies its own work against an objective gate.
