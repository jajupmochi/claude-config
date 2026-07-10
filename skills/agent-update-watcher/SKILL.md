---
name: agent-update-watcher
description: Use to keep up with the fast-moving agent ecosystem (new/updated CLIs, plugins, skills) WITHOUT burning tokens on constant checks. Declares the sources to watch in a config, checks them only when a minimum interval has elapsed, and reports ONLY what actually changed vs the recorded version — you then decide whether to adopt.
policy:
  allow_implicit_invocation: true
---

# agent-update-watcher

Overhaul task 6. New agent plugins/skills/CLIs appear constantly; checking them every turn wastes tokens and
network. This balances **availability / recency** against **cost** with a deterministic checker + a frequency
guard, and surfaces only real changes.

## Use

1. Copy `scripts/sources.example.json` to a local `sources.json`; list what to watch (`name`, `kind`,
   `current_version`, `url`) and set real current versions.
2. Provide latest versions as a `--snapshot {name: latest}` JSON (the thin fetch that turns each `url` into a
   latest version is caller-supplied — kept out of the deterministic checker so it stays testable/offline):
   ```
   python3 scripts/check_updates.py --config sources.json --state state.json --snapshot latest.json --min-interval-days 7
   ```
3. It prints one `UPDATE\t<kind>\t<name>\t<cur> -> <latest>\t<url>` line per changed source, records the
   check time in `state.json`, and **skips cheaply** if re-run within the interval (override with `--force`).

## Why deterministic + interval-guarded

Checking and diffing versions is pure code (no LLM). The interval guard is the token/network balance: a
weekly (default) check is enough for an ecosystem that moves in days, not seconds. The model only *decides
whether to adopt* an update — it never does the polling.

## Relation to autoresearch-toolfinder

`autoresearch-toolfinder` tracks ML-RESEARCH tools (awesome-lists). This watches the AGENT ecosystem itself
(the CLIs/plugins/skills you build on). Different domains, same "track + diff + report, don't reload" idea.

Status: v0.1 (config + interval-guarded diff, `--snapshot`-driven, tested `test_check_updates.py` 6/6). The
real release-feed fetch (url -> latest version) + a scheduled runner are the thin wrappers left to add.
