---
name: privacy-redact
description: Scan and redact private details before publishing or committing text. Use for usernames, absolute paths, secrets, project codenames, private URLs, and local machine details.
---

# privacy-redact

Read `../general/privacy-redact/SKILL.md`, then apply it in Codex:

1. Inspect only the files requested or the files being promoted publicly.
2. Redact secrets, usernames, absolute local paths, private hostnames, and
   project codenames with stable placeholders.
3. Preserve technical meaning and line structure where practical.
4. Never print suspected secrets back to the user.
5. Re-run a narrow search after edits to verify no obvious private tokens
   remain.
