---
name: figma-design-fetch
description: Use when the user shares a figma.com URL, wants to implement/mock a UI from Figma, or do design-to-code — connect the Figma MCP, fetch the design (code/assets/screenshot) to disk, then rebuild with existing components.
---

# /figma-design-fetch

Connect an official Figma design into the session via the **Figma MCP**, pull code / vector / bitmap /
screenshot to disk, and rebuild the frontend screen by screen with the project's existing components. This is
**agent-assisted, not full-auto** — fetch the design as rich context, then reconstruct with real components and
real data, converging per screen against a visual diff.

## Master TOC

- [When to use](#when-to-use)
- [Prerequisites](#prerequisites)
- [Step 1 — Connect the Figma MCP (OAuth)](#step-1--connect-the-figma-mcp-oauth)
- [Step 2 — Get a node-specific link](#step-2--get-a-node-specific-link)
- [Step 3 — Fetch](#step-3--fetch)
  - [Path A — agent + MCP (no token)](#path-a--agent--mcp-no-token)
  - [Path B — pure script (needs a PAT)](#path-b--pure-script-needs-a-pat)
- [Gotchas (tested — read before fetching)](#gotchas-tested--read-before-fetching)
- [Figma export options ↔ MCP](#figma-export-options--mcp)
- [Recommended workflow](#recommended-workflow)
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
2. **The Figma MCP is available in the session** — deferred tools `mcp__plugin_figma_figma__*`. If not, add it
   (do this yourself only if the user asks; it changes their config):
   ```bash
   claude mcp add --transport http figma https://mcp.figma.com/mcp   # remote, recommended
   # or: claude plugin install figma@claude-plugins-official
   ```

## Step 1 — Connect the Figma MCP (OAuth)

1. Call `authenticate` → it returns an **authorization URL**.
2. The **user** opens that URL, logs into Figma (**never enter the user's password for them**), and clicks
   **Authorize** (grants the read-only `mcp:connect` scope).
3. The redirect is `http://localhost:<port>/callback?code=...&state=...`:
   - Authorized in a browser **on this same machine** → the local listener catches it and auth **completes
     automatically**; the design tools appear on the next turn.
   - Callback errors / authorized on another device → ask the user to paste the **full** address-bar URL back,
     then call `complete_authentication`.
4. **Verify** with `whoami` → shows the account + seat (e.g. `seat: "Full"`).

> ⚠️ **Gotcha 1 — OAuth PKCE expires in minutes.** Authorize **promptly, within a few minutes of
> `authenticate`**. A long gap yields `No OAuth flow in progress` and the callback `code` is orphaned — re-run
> `authenticate` for a fresh URL and retry.

## Step 2 — Get a node-specific link

1. The user selects the **exact frame** in Figma and copies the link, shaped like:
   ```
   https://www.figma.com/design/<fileKey>/<name>?node-id=<1-23>
   ```
2. Extract two things: **`fileKey`** (segment after `/design/`) and **`nodeId`** (after `node-id=`;
   `4001-8` == `4001:8`).

> ⚠️ **Gotcha 2 — wrong node.** The link **must include `node-id`** (a file-only link makes the tool ask for
> one), and it must be the **target frame**, not the file cover (e.g. node `2-10`). Confirm the selection
> before fetching.

## Step 3 — Fetch

### Path A — agent + MCP (no token)

For that `fileKey` + `nodeId`, call **in order**:

| Tool | What you get |
|---|---|
| `get_metadata` | structure / hierarchy / geometry / layer names, incl. the design's **annotation text** (intent) |
| `get_screenshot` | the visual **ground truth** — returns a short-lived URL; `curl` it as the diff baseline |
| `get_design_context` | React + Tailwind reference code + asset URLs |
| `get_variable_defs` | design tokens (may be empty `{}` — see gotcha 3) |
| `download_assets` | png / svg render + **each node's original bitmaps** (`defaultFormat=svg` for vector) |

Save to `<frontend-repo>/.design-imports/<feature>/` — **this dir MUST be gitignored**:
`export.png` / `design.svg` / `assets/raw_image_*.png` / `link.txt`.

### Path B — pure script (needs a PAT)

No agent required, but needs a Figma personal access token:

```bash
export FIGMA_TOKEN=figd_xxx        # Figma → Settings → Personal access tokens
./.design-imports/figma-fetch.sh '<figma-node-url>' <out-dir>
```

Uses the Figma REST API (`/v1/images` for png+svg, `/v1/files/:key/nodes` for metadata). **Limitation**:
`/v1/files/:key/images` returns the **whole file's** image fills, not just this node (the MCP path is finer).

> ⚠️ **Gotcha 5 — asset URLs expire.** The `figma.com/api/mcp/asset/...` links MCP returns are short-lived
> (renders ~minutes, source images ~**7 days**). **`curl` to disk immediately** after fetching; never rely on
> the URLs in docs/code.

> 🔒 **Token safety (hard rule).** Read `FIGMA_TOKEN` from an env var or a **gitignored** `.figma-token` —
> **never hardcode, print, or commit** a token, key, or OAuth `code`.

## Gotchas (tested — read before fetching)

> ⚠️ **1. OAuth PKCE expires in minutes** → authorize promptly after `authenticate`; re-issue if expired
> (`No OAuth flow in progress`).

> ⚠️ **2. Code Connect is paywalled** → a Full/Dev seat emits code, but **auto-mapping designs to your existing
> React components (Code Connect / `get_code_connect_map`) needs an Organization/Enterprise plan**. On
> `starter` it errors; without it the agent **regenerates** code — you map to existing components **manually**.

> ⚠️ **3. `get_variable_defs` returns empty** = the design has **no Figma variables** → no
> "Figma variables → Tailwind tokens" pipeline. Read concrete color values from `get_design_context` code / the
> exported CSS instead.

> ⚠️ **4. Low-fidelity spec mockups** (placeholder screenshots + absolute positioning + hand annotations) →
> `get_design_context` returns a **pixel snapshot** (`absolute left-[x] top-[y]` + `<img>` placeholders), **not
> componentized, non-responsive production code**. Do **not** paste it verbatim.

> ⚠️ **5. Asset URLs expire in 7 days** → save to disk immediately (see above).

> ⚠️ **6. Browser auto-login scraping: not recommended** — the agent can't enter the user's password, Figma's
> canvas is WebGL (not DOM, so unscrapeable), and it's redundant with (and worse than) the official MCP.

## Figma export options ↔ MCP

| Figma option | What it is | MCP equivalent |
|---|---|---|
| PNG | raster render | `download_assets` (default png) / `get_screenshot` |
| SVG | vector export | `download_assets(defaultFormat=svg)` |
| **CSS code** | CSS of the **one selected layer** (Inspect panel) | `get_design_context` (React+Tailwind, not raw single-element CSS) |
| **CSS (all layers)** | flat absolute-positioned CSS dump of the node + every descendant | `get_design_context` (**nested** React+Tailwind, structure preserved, richer) |
| Property / Inspect | dimensions / spacing / typography specs | `get_metadata` (geometry) + `get_variable_defs` (tokens) |
| **iOS / Android code** | native SwiftUI/UIKit, Jetpack Compose/XML | none — **not needed for a web frontend** |

## Recommended workflow

**Agent-assisted + per-screen human review** — not full-auto generation of a whole app:

1. Treat `get_design_context` + `get_screenshot` as **rich design context** (read intent + visual), then
   **rebuild the feature with the project's existing React components + real backend data** — do not paste raw
   output.
2. **Fuse the two source datasets**: MCP (screenshot = truth + structure + reference code) + the exported CSS
   (concrete color values / fonts, filling an empty `get_variable_defs`) + the repo (components + data + design
   system).
3. Render each screen in a browser at the canonical viewport → screenshot → **visual-diff** against the Figma
   screenshot → iterate to convergence.

## References

Do not copy these wholesale — cite them:

- Tutorial (fullest): `neobanker-docs` → `docs/platform/guides/figma-mcp-fetch-tutorial.md` (+ `.en.md`).
- Reusable script: `neobanker-frontend-MVP-V3` → `.design-imports/figma-fetch.sh` (Figma REST API; reads
  `FIGMA_TOKEN`).
- Research background: `neobanker-docs` → `docs/platform/research/figma-to-code-automation.md`.

## Companion

- `verify-visual` — screenshot + 4-axis self-critique against the Figma reference (the per-screen diff loop).
- `ui-iteration-loop` rule — the autonomous visual-convergence loop when a reference image is given.

## Provenance

Distilled from a Neo Horizon design-to-code run where the official Figma MCP was connected and tested
end-to-end. Consolidated into `agent-harness` so any session hitting a Figma design follows the tested flow and
avoids the six gotchas above.
