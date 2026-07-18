# task-ledger

> One markdown document per round of work, enforced by a Stop hook that refuses to end the round while anything in it is unfinished.

## Master TOC

- [The problem](#the-problem)
- [How it works](#how-it-works)
- [The document](#the-document)
- [Commands](#commands)
- [Install](#install)
- [Per agent and per model](#per-agent-and-per-model)
- [Composing with review-gate](#composing-with-review-gate)
- [Tests](#tests)

## The problem

Three failures show up on any round with more than about ten sub-tasks, and none of them is fixable by
telling the model to be more careful, because the failure *is* the model's memory.

1. **Drift.** By task nine the agent has lost the shape of tasks one through four. It reports the round
   done having settled six of twelve.
2. **Mid-round requirements evaporate.** The user adds a requirement in passing at turn 30. At turn 60 it
   is far outside the working context and nothing on disk remembers it was ever said.
3. **Sub-agent handoffs lose detail.** The dispatching agent retypes the task from memory, and the user's
   original wording and the acceptance bar are the first things dropped.

## How it works

State lives in a file, and a hook checks the file. The agent's recollection is never what decides whether
a round is finished.

| Piece | Event | What it does |
|---|---|---|
| `scripts/capture.sh` | `UserPromptSubmit` | Appends every mid-round user prompt to the ledger's Inbox, before the agent has a chance to forget it. |
| `scripts/gate.sh` | `Stop` | Runs `ledger.py check`. While any task is open, any task is marked done without evidence, or any inbox item is untriaged, it returns `{"decision":"block"}` and the round continues. |
| `scripts/ledger.py` | CLI | Reads and writes the document. Also generates sub-agent briefs, so a handoff is generated rather than remembered. |

Three properties are deliberate:

- **The markdown file is the single source of truth.** No sidecar JSON, so nothing can drift out of sync,
  and a human editing the file by hand is a supported path.
- **A ledger that fails to parse fails CLOSED.** An unreadable ledger blocks with the parse error. The
  alternative — reading a corrupt file as an empty, trivially complete round — is the one outcome that
  would defeat the entire tool.
- **A missing dependency fails OPEN.** No `jq`, no `python3`, no ledger: the hook exits silently. Broken
  infrastructure must never wedge a session.

`done` requires `--evidence`, and `block` and `drop` require `--reason`. There is no path that closes a
task on an assertion alone, and there is always an honest way out that records why.

## The document

Lives at `.agent/ledger/<round-id>.md`, with `.agent/ledger/ACTIVE` naming the current round.

```markdown
# Round: Harness meta optimization

<!-- task-ledger: v1 -->

> **7/12 settled** · 2 doing · 3 todo · 1 inbox untriaged

## Meta
| field | value |
|---|---|
| round-id | 2026-07-18-harness-meta-optimization |

## Inbox
- [ ] `I1` 2026-07-18T17:02:11Z — also make the docs bilingual

## Tasks
### `T3` Bilingual docs
- **status**: `todo`
- **acceptance**: both README.md and README.zh.md exist and cross-link
- **evidence**: —
- **verbatim**:
  > also make the docs bilingual
```

`verbatim` is the requirement of record. It is what `ledger.py brief` hands a sub-agent, and where the
brief and a paraphrase disagree, the verbatim text wins.

## Commands

```bash
L=~/.claude/hooks/task-ledger/ledger.py

python3 $L open --title "Harness overhaul" --task "Wire the gate|it blocks on open work"
python3 $L add --title "Docs" --acceptance "README renders" --verbatim "写个用户文档" --detail "..."
python3 $L start T2
python3 $L done  T2 --evidence "python3 test_ledger.py -> 16 passed"
python3 $L block T5 --reason "waiting on the org's Actions billing"
python3 $L drop  T7 --reason "superseded by T3"

python3 $L triage I1 --new "Bilingual docs|both files exist"   # or --into T3, or --drop "why"

python3 $L status            # one line
python3 $L status --json     # machine readable
python3 $L check             # exit 2 while anything is unfinished
python3 $L view --compact    # what to hold in context on a long round
python3 $L brief T3          # a complete sub-agent prompt for one task
python3 $L close
```

## Install

```bash
mkdir -p ~/.claude/hooks/task-ledger
cp scripts/{ledger.py,gate.sh,capture.sh} ~/.claude/hooks/task-ledger/
chmod +x ~/.claude/hooks/task-ledger/*
```

Then merge `settings.snippet.json` into `~/.claude/settings.json`. Optionally copy
`task-ledger.conf.example` to `~/.claude/hooks/task-ledger/task-ledger.conf` and
`profiles.example.json` to a project's `.agent/ledger/profiles.json`.

The gate only acts when a round is open, so installing it does not change ordinary turns.

## Per agent and per model

`profiles.example.json` controls how much ledger a given agent or model tier gets, and which sections
survive into a sub-agent brief. It is data, so supporting a new agent or a newly released model is an edit
to that file rather than a code change — which is what lets this keep pace as agents and models change.

`brief_includes` is ordered by what to drop first. `verbatim` and `acceptance` should survive every
budget: they are the user's own words and the bar for being finished. `detail` and `siblings` go first
when context is tight.

Codex needs its own shim because its Stop hook speaks `{continue, stopReason, systemMessage}` rather than
`{decision}`. See `scripts/codex_task_ledger.sh`.

## Composing with review-gate

Both register a `Stop` hook and both follow the same contract, so they compose: empty stdout allows the
stop, and either one can block. `review-gate` asks whether the code was reviewed; `task-ledger` asks
whether the round is finished. They answer different questions and neither supersedes the other.

## Tests

```bash
python3 scripts/test_ledger.py   # 16 tests — parsing, transitions, fail-loud, profiles
bash    scripts/test_hooks.sh    # 11 tests — the decision JSON, capture, loop guard, fail-closed
```
