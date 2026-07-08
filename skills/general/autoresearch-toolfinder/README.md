# autoresearch-toolfinder

A research-focused Claude skill that recommends the right tool from two curated
**awesome-autoresearch** lists, on demand, **without ever loading the whole catalog into an
agent's context**.

- [alvinreal/awesome-autoresearch](https://github.com/alvinreal/awesome-autoresearch) (CC0)
- [yibie/awesome-autoresearch](https://github.com/yibie/awesome-autoresearch)

## Why / design goals

| Requirement | How it is met |
|---|---|
| Pick the right tool for a research task | `query.py` ranks the catalog by the task's keywords and returns the top few |
| **Save tokens** — never load both full lists | The 550+ entries live in `data/index.json` on disk; only `query.py`'s short result list (a handful of `name + url + one-liner`) ever enters context. `SKILL.md` is intentionally tiny and tells the agent **not** to read the index directly. |
| **Track upstream updates** | `data/state.json` stores each repo's commit SHA; `check_updates.py` compares against GitHub HEAD (1 cheap API call per repo); a weekly user systemd timer re-runs `update_index.py`. |
| **Auto-decide when to use it / which tools** | Claude Code auto-loads the skill from its `description` when the task matches; the agent then runs `query.py` so only the *relevant* tools surface — selection is per-task, not "load everything". |

## Layout

```
autoresearch-toolfinder/
├── SKILL.md                      # tiny; the only thing loaded into context on trigger
├── README.md                     # this file
├── scripts/
│   ├── update_index.py           # fetch + parse both repos -> data/index.json (+ SHAs)
│   ├── query.py                  # search the index, print top-N only
│   └── check_updates.py          # cheap SHA comparison vs upstream HEAD
├── data/
│   ├── index.json                # generated catalog (compact)  [committed snapshot]
│   └── state.json                # per-source SHA + sync time + counts
└── systemd/
    ├── autoresearch-index.service
    └── autoresearch-index.timer  # weekly refresh
```

## Usage

```bash
# from the skill directory
python3 scripts/query.py "apple silicon mlx"            # find a Mac/MLX port
python3 scripts/query.py "ai scientist paper" --source alvinreal
python3 scripts/query.py "" --category Finance          # browse a section
python3 scripts/query.py --list-categories              # sections + counts

python3 scripts/check_updates.py                        # is the catalog stale?
python3 scripts/update_index.py                         # refresh it
```

Stdlib-only Python 3 (no pip dependencies).

## Install (user level)

```bash
bash install.sh        # copies the skill to ~/.claude/skills/ and enables the weekly timer
```

or manually: copy this directory to `~/.claude/skills/autoresearch-toolfinder/`, run
`python3 scripts/update_index.py` once, then
`systemctl --user enable --now autoresearch-index.timer` (after linking the unit files).

## Relationship to the `autoresearch` skill

The sibling `autoresearch` skill *runs* an end-to-end autonomous research project. This skill
only *finds the tools* — they compose: use the finder to choose a framework, then the
orchestrator (or the chosen tool) to run it.
