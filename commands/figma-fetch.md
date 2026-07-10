---
description: "Fetch a Figma design node (code/assets/screenshot) to .design-imports/ via the Figma MCP (Path A)"
argument-hint: "[figma-node-url]"
allowed-tools: ["Bash", "Read", "Write", "Skill"]
---

# /figma-fetch

Fetch one Figma design node into the repo using **Path A (agent + MCP, no token)**, following the
`figma-design-fetch` skill. Target node link: **$ARGUMENTS**

Follow the `figma-design-fetch` skill exactly. In short:

1. **Load the skill** — invoke `figma-design-fetch` for the full flow + gotchas before doing anything.
2. **Connect if needed** — if the Figma MCP tools (`mcp__plugin_figma_figma__*`) are not authenticated, call
   `authenticate`, have the **user** authorize in the browser (never enter their password), verify with
   `whoami`. Remember gotcha 1: PKCE expires in minutes.
3. **Parse the link** in `$ARGUMENTS` → `fileKey` (after `/design/`) + `nodeId` (after `node-id=`; `4001-8` ==
   `4001:8`). Refuse if it has no `node-id` (ask the user to select the exact frame and re-copy).
4. **Fetch in order**: `get_metadata` → `get_screenshot` → `get_design_context` → `get_variable_defs` →
   `download_assets` (`defaultFormat=svg` for vector).
5. **Save immediately** to `<frontend-repo>/.design-imports/<feature>/` (create it, ensure it is **gitignored**):
   `export.png` / `design.svg` / `assets/raw_image_*.png` / `link.txt`. `curl` any asset/screenshot URLs to disk
   right away — they expire (gotcha 5).
6. **Report** what was saved and where, then stop — reconstruction is a separate, human-reviewed step (see the
   skill's "Recommended workflow"). Do NOT paste raw `get_design_context` output as production code.

Never hardcode, print, or commit any Figma token or OAuth code.
