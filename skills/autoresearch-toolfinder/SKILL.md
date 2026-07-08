---
name: autoresearch-toolfinder
description: Find the right autonomous-research or research-agent tool from Codex using the source agent-harness autoresearch-toolfinder skill. Use when choosing, comparing, or setting up autoresearch tools, AI-scientist systems, research-agent loops, platform ports, or evaluation harnesses.
---

# autoresearch-toolfinder

Codex wrapper for `skills/general/autoresearch-toolfinder/SKILL.md`.

Before acting, read the source skill completely. Resolve paths relative to this wrapper first:

- `../general/autoresearch-toolfinder/SKILL.md`
- `../general/autoresearch-toolfinder/scripts/query.py`
- `../general/autoresearch-toolfinder/data/state.json` only for freshness metadata; never load the full index into context

Follow the source skill token-efficiency rule: run `python3 scripts/query.py "<task keywords>"` from the source skill directory and return only the few relevant results with a short reason for each recommendation.
