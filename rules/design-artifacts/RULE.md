---
name: design-artifacts
description: When you design/implement APIs or frontend features, surface them as a list of clickable LOCAL test/preview links (Swagger /docs, Storybook, the running app route) and embed screenshots of the changed UI — in BOTH the doc and the summary — so the user can click straight in to test and SEE the change.
scope: personal
rationale: The user does a lot of frontend/backend + FastAPI design. A summary that just says "added 6 endpoints" is useless — they want to click into the running test tool and the live preview, and SEE the visual change, not read about it.
---

# design-artifacts

> Designed an API or a UI change? Don't describe it — make it CLICKABLE and SHOW it. List every new endpoint with a link straight into its local test tool; for any visible UI change, give the live local preview link AND a screenshot. In the doc AND the summary.

## Master TOC

- [When this applies](#when-this-applies)
- [APIs — a clickable test list](#apis--a-clickable-test-list)
- [Frontend / visible changes — preview link + screenshot](#frontend--visible-changes--preview-link--screenshot)
- [Companion rules](#companion-rules)

## When this applies

Any turn that designs or implements **API endpoints** (FastAPI / REST / GraphQL …) or **frontend features** whose effect is visible in a UI. Then produce the artifacts below in **both** the per-run / design doc **and** the in-session summary.

## APIs — a clickable test list

For each new or changed endpoint, list `METHOD /path — one-line purpose` **and a full clickable LOCAL link that opens its test tool**, so the user clicks once and is testing it:

- **FastAPI / OpenAPI** → Swagger UI deep link: `http://localhost:<port>/docs#/<tag>/<operationId>` (or ReDoc `http://localhost:<port>/redoc#operation/<operationId>`). Always state the port + how to start the server (`uvicorn app:app --reload`) so the link is live.
- **Storybook component** → `http://localhost:6006/?path=/story/<story-id>` (state `npm run storybook`).
- **Other local test UIs** (a `/playground`, a GraphQL `/graphql`, a custom harness) → the full local URL.

Put the list in the doc and the summary; never just say "added N endpoints" with no links.

## Frontend / visible changes — preview link + screenshot

If a frontend/backend change is visible in the UI:

1. **Live preview link** — the full clickable LOCAL URL of the exact route/page that changed: `http://localhost:<port>/<route>` (state how to start it, e.g. `npm run dev`). In the doc AND the summary.
2. **Screenshot** — it has to become a real FILE and actually reach the user:
   - **Capture to a FILE on disk** — Playwright `browser_take_screenshot` with an explicit output `filename`/path (any screenshot tool that WRITES a file, not one that only returns image data inline). Do NOT rely on **claude-in-chrome inline screenshots**: those come back inline in the tool result, are NOT written to disk, so there is no file to link or commit AND they do not render on the user's end (this exact trap made a run's screenshots invisible). Save under the repo's `images/` folder.
   - **In the committed doc**: embed inline with a repo-relative path (`![...](images/<name>.png)`) — renders on GitHub / in the repo.
   - **In the in-session summary (chat / phone)**: never a bare relative filename or a relative `![](…)` (no cwd to resolve → shows nothing). Give a **clickable ABSOLUTE path to the PNG** (`/media/.../images/<name>.png`) AND **actually deliver the image with `SendUserFile`** so it surfaces WITH the summary — don't count on a mid-run send the user scrolled past, and note that an un-pushed repo has no working GitHub image URL, so the local file + `SendUserFile` is the only way they SEE it.
   - Before/after when the change is a modification. The user must be able to SEE the difference without running anything.

## Companion rules

Builds on [`clickable-links`](../clickable-links/RULE.md) (every link full + clickable) and [`human-readable-output`](../human-readable-output/RULE.md) (the list/summary is readable, key points first).
