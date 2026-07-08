---
name: autoresearch-toolfinder
description: Find the right autonomous-research / autoresearch tool, framework, port, or skill for a research or engineering task. Searches a local cached index of two curated awesome-autoresearch lists (alvinreal + yibie, 550+ entries) and returns only the few matching tools, never loading the whole catalog into context. Use when the user wants to pick, compare, or set up an autoresearch loop, an AI-scientist / research-agent system, a domain or hardware port (Apple Silicon, RTX, RL, trading, materials, bio, vision, kernels...), or an evaluation harness, or asks "is there an autoresearch tool for X".
version: 1.0.0
license: MIT
tags: [autoresearch, research-agents, tool-discovery, scientific-research, token-efficient]
---

# autoresearch-toolfinder

Recommends tools from two curated **awesome-autoresearch** catalogs (550+ entries) WITHOUT
reading the whole list into context. You run a search script and read back only the top matches.

## How to use (token-efficient — follow this; do NOT cat the index)

The catalog is large. **Never read `data/index.json` directly** (that defeats the purpose).
Run the query script from the skill directory; it returns only the top candidates:

```bash
python3 scripts/query.py "<keywords from the user's task>"
# options:  --source alvinreal|yibie   --category "<substring>"   --limit 8   --json
python3 scripts/query.py --list-categories      # see sections + counts first
```

Examples:
- Apple-Silicon / MLX port:   `python3 scripts/query.py "apple silicon mlx mac metal"`
- End-to-end AI scientist:    `python3 scripts/query.py "ai scientist paper literature review" --source alvinreal`
- RL post-training loop:      `python3 scripts/query.py "reinforcement learning grpo post-training"`
- Trading strategy search:    `python3 scripts/query.py "trading strategy backtest" --source yibie`
- Browse a whole section:     `python3 scripts/query.py "" --category "Evaluation"`

Then: read the handful of `name + url + one-liner` results, pick the best 1-3 for the user's
actual context, and say why. Open a specific repo URL (WebFetch) only if the user wants depth.

## When to activate (auto)

Activate when the user is **choosing / comparing / setting up**: an autoresearch or
self-improvement loop; an AI-scientist or research-agent system; a hardware/platform port; a
domain adaptation (bio, materials, finance, vision, RL, kernels, robotics...); or an eval
harness — or asks "what should I use for autonomous research / overnight experiments on X".

Not this skill: to actually *run* a full autonomous research project end-to-end, use the
sibling `autoresearch` orchestration skill. This skill is the **catalog / finder** only.

## Keeping it current (update tracking)

`data/state.json` stores each upstream repo's commit SHA + sync time.

```bash
python3 scripts/check_updates.py     # cheap: 1 API call/repo, compares SHA, exits 1 if stale
python3 scripts/update_index.py      # re-fetch + re-parse both repos, rewrite the index
```

A weekly user systemd timer (`systemd/autoresearch-index.timer`) refreshes automatically;
`query.py` also prints a hint when the local index is older than 30 days.

## Sources
- [alvinreal/awesome-autoresearch](https://github.com/alvinreal/awesome-autoresearch) (CC0)
- [yibie/awesome-autoresearch](https://github.com/yibie/awesome-autoresearch)
