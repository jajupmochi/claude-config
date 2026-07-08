---
name: preview-template
description: Start or identify the local preview environment from Codex. Use for UI, docs, static site, Vite, Next.js, Storybook, MkDocs, or visual verification workflows.
---

# preview-template

Read `../general/preview-template/SKILL.md`, then adapt it to Codex:

1. Inspect project manifests and `AGENTS.md` for the canonical preview command.
2. Start long-running dev servers in a background exec session when possible.
3. If the default port is occupied, choose another port and state it.
4. Keep the server running only if the user needs to try it or a later
   verification step needs it.
5. End with the actual local URL.

Do not start a server for plain HTML when opening the file directly is enough,
unless browser APIs or module loading require HTTP.
