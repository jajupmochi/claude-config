# agent-harness user guide

> Every capability this harness ships, how you invoke it, a command that proves it works, and whether it is live on this machine.

> **Language:** English | [中文](USER_GUIDE.zh.md)

## Master TOC

1. [Read this first: registered, deployed, fires](#read-this-first-registered-deployed-fires)
2. [What makes each capability run](#what-makes-each-capability-run)
3. [The seven capabilities you asked about](#the-seven-capabilities-you-asked-about)
4. [Added this round](#added-this-round)
5. [Rules](#rules)
6. [Skills](#skills)
7. [Hooks](#hooks)
8. [Slash commands](#slash-commands)
9. [Repository tools](#repository-tools)
10. [Templates, tooling, recommendations, setup](#templates-tooling-recommendations-setup)
11. [How deployment works on this machine](#how-deployment-works-on-this-machine)
12. [Verification log](#verification-log)
13. [Known stale docs](#known-stale-docs)

Every command in this guide is run from the repository root unless the text says otherwise. Every result quoted was produced by running the command on 2026-07-18 against branch `feat/harness-meta-optimization-2026-07-18`.

## Read this first: registered, deployed, fires

A capability passes through three separate states, and treating them as one is the confusion this guide exists to end.

| State | What it means | Where you check it |
|---|---|---|
| Registered | Its path is listed in the canonical inventory that generates every agent's manifest. On its own this changes nothing at runtime. | [`adapters/manifest.source.json`](../adapters/manifest.source.json) |
| Deployed | The file now sits in the directory the agent actually reads. | `~/.claude/skills/`, `~/.claude/hooks/`, `~/.claude/settings.json` |
| Fires | Something causes it to run on a real turn. | A hook event, a slash command you type, or the model deciding to use it |

**Skills and rules reach the model by different routes, and this is the part that bit us.** Claude Code auto-discovers any `SKILL.md` under `~/.claude/skills/`, so for a skill, deployed does mean discoverable. Nothing does the equivalent for a rule. The Claude projector at [`adapters/claude.mjs`](../adapters/claude.mjs) emits no rule loader at all, and its own comment says so, that rules stay in `CLAUDE.md`. The `rules` array inside [`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) is inventory metadata, not a runtime import. A rule reaches the model only when its text sits in a file the agent reads on every turn, which on this machine is `~/.claude/CLAUDE.md`.

The practical consequence is that `design-modes`, `test-first`, `regression-test-on-bugfix`, `incremental-delivery`, `parity-restoration` and `commit-discipline` were registered, shipped and documented for months while never once entering a prompt. [`bin/rule-activation.mjs`](../bin/rule-activation.mjs) closed that gap this round by writing their text into a regeneratable managed block in `~/.claude/CLAUDE.md`. That block is now present and carries all six.

**Deployed still does not guarantee it fires.** A skill sitting in `~/.claude/skills/` is offered to the model, not imposed on it. `code-verifier` has been deployed for months and is named in review-gate form 4, and unverified claims still got through, because nothing forces the model to open it. That is the difference between the two status values below, and it is worth more than any other line in this document.

## What makes each capability run

Status answers one question, what makes this run. The live column answers a different one, whether that mechanism is wired up on this machine right now.

| Status | Meaning |
|---|---|
| `enforced` | A hook event runs it. The model cannot decline. If the hook is a blocking one, the turn does not end until the check passes. |
| `advisory` | Text the model reads, or a tool it may call. It runs when the model chooses to, or when you type the command yourself. |
| `incomplete` | It ships, but a piece needed to do the job it describes is missing, so it cannot do that job unaided. |

Headline inventory, with the detail in the sections that follow.

| Area | Count | Status | Live on this machine |
|---|---|---|---|
| [Rules](#rules) | 27 directories, 26 registered | `advisory` | 26 of 26 reachable in `~/.claude/CLAUDE.md`, verified. `native-capability-first` is the 27th and is inert. |
| [Skills](#skills) | 23 top level plus 11 in the general bucket, 19 registered | `advisory` | 17 reachable by bare name, 4 more only as `agent-harness:<name>`. `doc-writing` is reachable by neither. |
| [Hooks](#hooks) | 6 shipped | `enforced` | 3 wired into `~/.claude/settings.json`. `task-ledger`, `block-env-read` and `typecheck-on-edit` are not. |
| [Slash commands](#slash-commands) | 2 | `advisory` | Both live through the enabled plugin. |
| [Repository tools](#repository-tools) | 9 in `bin/` and `scripts/` | `advisory` | All run. |
| [Templates and tooling](#templates-tooling-recommendations-setup) | 3 templates, 3 tooling packs, 20 recommendation files | `advisory` | Read on demand. |

The one enforcement path that reliably fires today is [review-gate](#review-gate). Everything else in the harness is a suggestion the model can decline, which is the honest summary of the whole system.

## The seven capabilities you asked about

### 1. The two design modes

**What it does.** Names two modes with opposite defaults so a substantial build settles which one it is in before starting. Prototyping buys speed with high autonomy and deferred test breadth. Scaling buys correctness with bounded autonomy, small reviewed steps and full coverage. The rule also covers mixing them per sub-task, the confirmation needed to switch mid-task, and a capability floor that puts a weak model in scaling mode regardless.

**How to invoke it.** You do not. It is rule text in `~/.claude/CLAUDE.md` and is in the model's context on every turn. The trigger inside the rule is that the model asks which mode applies before a substantial build, or states its read when your message already implies one.

**How to test it.** Confirm the text is reachable.

```bash
node bin/rule-activation.mjs --check --verbose --agent claude | grep design-modes
```

Result on this machine: `ok     design-modes                 matched: managed block`.

**Live here.** Yes, through the managed block written this round. Source is [`rules/design-modes/RULE.md`](../rules/design-modes/RULE.md) with the condensed text in [`rules/design-modes/snippet.md`](../rules/design-modes/snippet.md). Status `advisory`.

### 2. Context optimization

**What it does.** There is no context optimization tool. The behaviour is spread across three unrelated pieces, and saying so plainly is more useful than implying a subsystem exists.

1. [`rules/output-brevity`](../rules/output-brevity/RULE.md) cuts what goes into the transcript. It bans echoing tool output back, bans end of batch recaps, and prefers `Edit` over `Write` so only a diff crosses the context rather than a whole file.
2. [`rules/no-reread-files`](../rules/no-reread-files/RULE.md) stops the same file being pulled in twice. Re-read only when the file actually changed.
3. [`skills/memory-flywheel`](../skills/memory-flywheel/SKILL.md) moves detail out of the context window and onto disk, so a long session can drop it and recall it later.

Task 2 of the overhaul, on-demand loading and a token footprint measurement, was designed and never built. Nothing in the repository measures a token footprint.

**How to invoke it.** The two rules load as rule text. The skill is invoked by name, covered in the next entry.

**How to test it.** Check both rules are reachable.

```bash
node bin/rule-activation.mjs --check --verbose --agent claude | grep -E "output-brevity|no-reread"
```

Result: `ok     output-brevity` and `ok     no-reread-files`, both matched by their own headings in `~/.claude/CLAUDE.md`.

**Live here.** The two rules are live. There is no measurement tool to be live or not. Status `incomplete` as a capability, because the piece that would tell you whether context actually got smaller does not exist.

### 3. Cross-session information

**What it does.** [`skills/memory-flywheel/scripts/mem.py`](../skills/memory-flywheel/scripts/mem.py) writes each round of work to a per project directory as a plain Markdown file with frontmatter, then recalls it later by keyword scoring. It is deterministic code with no model in the loop, so recall is cheap and repeatable. Recall is weighted by IDF (inverse document frequency) so a query term that appears in every round does not swamp the ranking.

**How to invoke it.** `Skill(memory-flywheel)`, or call the script directly. Four subcommands, `record`, `index`, `recall` and `link`.

**How to test it.** This writes only under the temporary root you pass.

```bash
mkdir -p /tmp/memdemo
echo "decided to use grep-native files" | python3 skills/memory-flywheel/scripts/mem.py \
  record --root /tmp/memdemo --project demo --kind design \
  --title "Memory layout" --keywords memory,layout
python3 skills/memory-flywheel/scripts/mem.py index  --root /tmp/memdemo --project demo
python3 skills/memory-flywheel/scripts/mem.py recall --root /tmp/memdemo --project demo --query "grep-native"
```

Expected output. `record` prints the path of the round file it wrote. `index` prints nothing and rewrites `INDEX.md`. `recall` prints one scored line, which on this run was `0.001` followed by the path to `0001-design.md`. The full suite is `python3 skills/memory-flywheel/scripts/test_mem.py`, which reported `mem.py: all 11 tests PASS`.

**Live here.** Yes, discoverable as a skill. One caveat covered in [How deployment works](#how-deployment-works-on-this-machine): the deployed copy is a symlink into a separate clone, not this checkout. Status `advisory`.

### 4. Multi-granularity document memory

**What it does.** The same skill, read as two layers. The coarse layer is `INDEX.md`, one table row per round holding id, kind, title and keywords. The fine layer is `rounds/NNNN-<kind>.md`, one file per round holding the verbatim body. The reading protocol is to open the index first and then open only the round files that recall points at, so a long history costs one small table instead of every file.

**How to invoke it.** Same skill. `index` rebuilds the coarse layer, `recall` selects which fine files to open.

**How to test it.** Continue from the previous test and read the two layers.

```bash
cat /tmp/memdemo/demo/INDEX.md
cat /tmp/memdemo/demo/rounds/0001-design.md
```

Expected output. `INDEX.md` holds the heading `# Memory index — demo`, the line `1 round(s). Read this coarse layer first; open only the round files recall points at.` and a four column table whose single row is `| 0001 | design | Memory layout | memory, layout |`. The round file holds frontmatter with `id`, `kind`, `title`, `ts` and `keywords`, then the verbatim body. Both layers were produced by the run above.

**Live here.** Yes, same as the entry above. Status `advisory`.

### 5. Adaptive tooling

**What it does.** [`skills/agent-update-watcher`](../skills/agent-update-watcher/SKILL.md) compares a list of watched sources against the versions you last recorded and prints only what changed, guarded by a minimum interval so re-running it costs nothing.

**It cannot self-drive, and this is the limitation to understand before relying on it.** The skill has a diff engine and no fetcher. It does not reach the network. The latest version of each source has to be handed to it as a `--snapshot` file, and the code that would turn each watched URL into that snapshot was deliberately left to the caller and never written. Nothing in the repository fetches it, and no timer runs it. So it is a comparator you drive by hand, not a watcher that watches.

**How to invoke it.** `Skill(agent-update-watcher)`, or the script directly with a config, a state file and a snapshot.

**How to test it.** This proves both the diff and the interval guard.

```bash
cp skills/agent-update-watcher/scripts/sources.example.json /tmp/sources.json
printf '{"claude-code":"99.99.99","codex":"99.99.99","opencode":"99.99.99"}' > /tmp/latest.json
python3 skills/agent-update-watcher/scripts/check_updates.py \
  --config /tmp/sources.json --state /tmp/state.json --snapshot /tmp/latest.json --min-interval-days 7
python3 skills/agent-update-watcher/scripts/check_updates.py \
  --config /tmp/sources.json --state /tmp/state.json --snapshot /tmp/latest.json --min-interval-days 7
```

Expected output. The first run prints `[agent-update-watcher] 3 update(s) of 3 source(s).` followed by three tab separated lines each starting with `UPDATE`. The second run prints `[agent-update-watcher] skipped: checked 0d ago (< 7d). Use --force to override.` Both were observed. Unit tests: `python3 skills/agent-update-watcher/scripts/test_check_updates.py` reported `check_updates.py: all 6 tests PASS`.

**Live here.** The skill is discoverable and the comparator runs. The capability as a whole is `incomplete`, because the fetcher that would make it adaptive does not exist.

### 6. Automatic plugin curation

**This does not exist.** There is no tool, no script, no hook and no skill that curates plugins.

The claim comes from row 7 of [`docs/OVERHAUL_DELIVERY.md`](OVERHAUL_DELIVERY.md), which reads `Plugin hygiene | rename leftovers, dead-knob templates, malformed-YAML fixes`. Those were three one-off manual edits made during the overhaul, not a capability that runs again. [`docs/strategy/agent-harness-overhaul-2026-07-09/STATUS.md`](strategy/agent-harness-overhaul-2026-07-09/STATUS.md) is the more accurate of the two on this point, marking task 7 partial and naming a periodic cleanup tool as still outstanding.

The nearest thing that does exist is [`recommendations/cc-plugins.md`](../recommendations/cc-plugins.md), a hand maintained list of plugins with no automation attached, and `rules/plugin-preflight`, which tells the model to check a plugin is installed and not deprecated before invoking it. Neither curates anything.

**How to test it.** The honest test is that both searches come back empty. The first looks for anything shipped whose name is about plugins or curation, the second looks for it in the registered inventory.

```bash
ls bin scripts hooks skills commands | grep -i "plugin\|curat"
grep -io "plugin[a-z-]*curation\|curate-plugins\|plugin-hygiene" \
  adapters/manifest.source.json .claude-plugin/plugin.json
```

Result on this machine: no output and exit status 1 from both. A plain search for the word `curate` is not a valid test, because it hits the prompt library docstrings, which curate prompts rather than plugins. Status `incomplete`, in the sense that the feature was described but never built.

### 7. TUI (terminal user interface) tool recommendation

**What it does.** This is the only one of the seven that is finished end to end. [`recommendations/tui-for-agents.md`](../recommendations/tui-for-agents.md) is the survey, written for a machine where full editors crash, covering concurrent sessions, sub-agent switching, diff review and approve or reject flows, and marking each claim verified or unverified. [`skills/tui-installer`](../skills/tui-installer/SKILL.md) turns that survey into an installer for four tools, `zellij`, `claude-squad`, `lazygit` and `delta`. TUI here means terminal user interface. Dry run is the default, `--apply` asks yes or no per tool, and a tool with no clean package is marked manual with its upstream URL rather than given an invented command.

**How to invoke it.** `Skill(tui-installer)`, or the script directly. Read the survey with any reader.

**How to test it.** Read only, installs nothing.

```bash
bash skills/tui-installer/scripts/install-tui.sh --check
```

Expected output on a machine with none of them: four lines each beginning `MISSING`, then `4 of 4 recommended tools missing.` That is what this machine printed, so the stack is recommended and not yet installed. Unit tests: `bash skills/tui-installer/scripts/test_install_tui.sh` reported `install-tui.sh: all 11 checks PASS`.

**Live here.** Yes, discoverable as a skill, and the recommendation file is readable. Status `advisory`, complete.

## Added this round

### rules/native-capability-first

**What it does.** Puts a three question fit check in front of every other harness feature. Is it necessary for this task shape, would following it produce a worse result than unaided ability, and which is actually stronger. It names the cases that are never exempt, which are verification gates, blocking hooks, privacy handling, destructive confirmations and your own instructions. When the model skips a feature it files a feedback entry rather than skipping silently.

**How to invoke it.** Rule text, same as any other rule.

**How to test it.**

```bash
node bin/rule-activation.mjs --check --verbose --agent claude | grep -c native-capability
```

Result on this machine: `0`. **The rule is inert.** It is not in the registered inventory, so `rule-activation.mjs` never considers it, so nothing wrote it into `~/.claude/CLAUDE.md`. Registering it is handled outside this guide. Files are [`rules/native-capability-first/RULE.md`](../rules/native-capability-first/RULE.md) and [`rules/native-capability-first/snippet.md`](../rules/native-capability-first/snippet.md). Status `incomplete` until it is registered and a `--apply` run picks it up.

### hooks/task-ledger

**What it does.** Holds one Markdown document per round of work and refuses to end the round while anything in it is unfinished. `capture.sh` on `UserPromptSubmit` appends every mid-round prompt to an inbox before the model can forget it. `gate.sh` on `Stop` blocks while any task is open, any task is marked done without evidence, or any inbox item is untriaged. `ledger.py` reads and writes the document and generates sub-agent briefs, so a handoff is generated rather than remembered. Marking a task done requires `--evidence`, and blocking or dropping one requires `--reason`.

**How to invoke it.** The two hooks fire on the events above once installed. The command line is `python3 hooks/task-ledger/scripts/ledger.py <subcommand>`, with `open`, `add`, `inbox`, `triage`, `start`, `done`, `block`, `drop`, `status`, `check`, `approvals`, `brief`, `view` and `close`.

**How to test it.**

```bash
python3 hooks/task-ledger/scripts/ledger.py status
npm run test:task-ledger
```

Expected output. `status` prints one line for the active round. This machine printed `Harness meta optimization — 8/16 settled · 8 todo` followed by the open task list, reading the live ledger at [`.agent/ledger/`](../.agent/ledger). The test script reported `task-ledger hooks: all 11 tests PASS` after the 16 Python tests.

**Live here.** The document and the command line work. **The hooks are not installed**, so nothing is blocking on the ledger. `~/.claude/hooks/` holds only `review-gate`, a backup of it, and the ssh-guard state directory. Installing it means copying the three scripts and merging [`hooks/task-ledger/settings.snippet.json`](../hooks/task-ledger/settings.snippet.json) into `~/.claude/settings.json`, per [`hooks/task-ledger/README.md`](../hooks/task-ledger/README.md). Status `enforced` by design, not live.

### `bin/rule-activation.mjs`

**What it does.** Reports which registered rules actually reach each agent, and writes the ones that do not into a managed block delimited by begin and end comment markers. Detection is deliberately generous, matching a rule by name or by its snippet heading against the file, because you hand maintain `~/.claude/CLAUDE.md` and duplicating a rule you already wrote costs tokens on every turn. Rules you have covered in your own words go in an ignore file so the detector's miss is expected rather than repeated forever.

**How to invoke it.**

```bash
node bin/rule-activation.mjs --check                  # report, exit 1 if anything is inert
node bin/rule-activation.mjs --check --verbose        # with the matching evidence per rule
node bin/rule-activation.mjs --apply --dry-run        # show the block without writing
node bin/rule-activation.mjs --apply --agent claude   # write it
```

**How to test it.**

```bash
node bin/rule-activation.mjs --check
npm run test:rule-activation
```

Expected output. The check prints one section per agent. This machine printed `26/26 rules reachable` for claude against `~/.claude/CLAUDE.md`, the same for codex against `~/.codex/AGENTS.md`, and for opencode `loads every rule via instructions glob; nothing to write`, then `all registered rules are reachable` and exit 0. The opencode line is genuine rather than a special case, because its config declares an instructions glob over every rule file. The test script reported `rule-activation.mjs: all 26 checks PASS`.

**Live here.** Yes. The managed block is in `~/.claude/CLAUDE.md` and carries `test-first`, `design-modes`, `regression-test-on-bugfix`, `incremental-delivery`, `parity-restoration` and `commit-discipline`. Status `advisory`, in that you run it, but its output is what makes rules load at all.

### `bin/harness-feedback.mjs`

**What it does.** The write end of the loop that `native-capability-first` opens. When a harness feature does not fit, this appends a structured entry to a queue file so the mismatch is recorded rather than silently absorbed. Three verdicts, `native-better` meaning narrow the trigger or retire it, `needs-update` meaning right in principle and stale in detail, and `missing-capability` meaning the harness should capture something it does not. `/harness-sync` is the read end that drains the queue into real edits.

**How to invoke it.**

```bash
node bin/harness-feedback.mjs --feature rules/phased-planning --verdict native-better \
  --why "forced a 3-phase plan onto a one-line fix" \
  --proposal "narrow the trigger to 3+ files AND 5+ tool calls"
node bin/harness-feedback.mjs --list
node bin/harness-feedback.mjs --list --all
```

**How to test it.** The read path is safe to run against the repository.

```bash
node bin/harness-feedback.mjs --list
npm run test:harness-feedback
```

Expected output. `--list` printed `no open entries`, which is correct, because `docs/harness-feedback/QUEUE.md` has not been created yet. The test script reported `harness-feedback.mjs: all 9 tests PASS`. Filing was separately verified against a scratch copy of the script, which wrote the queue file with its header, verdict table and one entry, and then listed it as `open     native-better       rules/phased-planning`. An invalid verdict is rejected with `--verdict must be one of: native-better, needs-update, missing-capability`.

**Live here.** Yes as a script. Nothing calls it automatically, and the rule that would prompt the model to call it is the inert one above. Status `advisory`.

### skills/doc-writing

**What it does.** Encodes the documentation preferences mined from two real project sessions, 262 prompts reduced to 102 verbatim preferences and 48 consolidated rules, organized by document type. It ships [`scripts/doccheck.py`](../skills/doc-writing/scripts/doccheck.py), a linter for the subset a machine can check: leaked secrets, bare references that should be links, undefined jargon, a missing diagram, missing required sections, tables and lists that will not render, staleness markers, and flat dash lists past three items. Per type required sections and the acronym stoplist live in [`doccheck.config.json`](../skills/doc-writing/doccheck.config.json) so they are tunable without touching the script.

**How to invoke it.** `Skill(doc-writing)` once it is deployed. The linter runs standalone today.

**How to test it.**

```bash
python3 skills/doc-writing/scripts/doccheck.py docs/USER_GUIDE.md --type readme
python3 skills/doc-writing/scripts/test_doccheck.py
```

Expected output. The linter prints one line per finding with level, check name, rule id and line number, then a summary, exiting 0 when clean, 1 on warnings and 2 on errors. The test script reported `doccheck.py: 20/20 tests PASS`.

**Live here.** **The skill is not discoverable by any route.** It is absent from the registered inventory, so the deployer never places it under `~/.claude/skills/`, and it is also absent from the clone the plugin serves, so the `agent-harness:doc-writing` form does not resolve either. It does not appear in the session skill catalog. The linter works when called by path. Status `advisory`, not live.

### skills/prompt-library and its mined corpus

**What it does.** Curates reusable prompts as greppable Markdown, each carrying the original, an optimized rewrite, and a when not to use section that is where the judgement lives. A privacy gate refuses to store anything still holding paths, emails, tokens, usernames or codenames, so the library stays publishable. `plib_mine.py` is new this round and extracts prompts out of local session history. The mined corpus landed at [`recommendations/prompt-library/`](../recommendations/prompt-library/) with 18 entries and an index, covering feature specs, skill authoring, documentation, deployment, data platform work, research design, bug triage, reporting and proposal writing.

**How to invoke it.** `Skill(prompt-library)`, or the script with `scan`, `add`, `index`, `find` or `mine`.

**How to test it.**

```bash
python3 skills/prompt-library/scripts/plib.py find --query "documentation audit"
python3 skills/prompt-library/scripts/test_plib.py
```

Expected output. `find` prints scored paths, highest first. This machine returned four hits led by score `9` on `documentation-completeness-audit-and-backlog-consolidation.md`. The test script reported `plib.py + plib_mine.py: all 24 tests PASS`.

**Live here.** The skill is discoverable, with one gap. `--root` defaults to `recommendations/prompt-library` resolved against the working directory, and the clone the deployed skill points at does not contain that directory, so the default only resolves when you run it from this checkout. Pass `--root` explicitly from anywhere else. Status `advisory`.

### `hooks/review-gate/scripts/statsbar.sh`

**What it does.** Renders a counted breakdown as an aligned coloured bar, so a review that reports twelve files with ten clean, one fixed and one open is read at a glance instead of parsed as a sentence. Two output formats, because the numbers are read in two places. `ansi` is the default on a terminal, `md` is a fenced monospace block for a Markdown reader where colour comes from emoji, since escape codes would render as literal noise. `NO_COLOR` forces plain output. It is the shared renderer, so review-gate, task-ledger and anything else report the same shape.

**How to invoke it.**

```bash
bash hooks/review-gate/scripts/statsbar.sh --title "review-gate" --unit files --total 12 \
  --stat "OK:10:green" --stat "fixed:1:yellow" --stat "open:1:red"
```

Colours are `green`, `yellow`, `red`, `blue` and `grey`, and an omitted colour becomes grey. An omitted `--total` becomes the sum of the stats.

**How to test it.**

```bash
bash hooks/review-gate/scripts/statsbar.sh --help
bash hooks/review-gate/scripts/test_statsbar.sh
```

Expected output. `--help` prints the header comment block including the two format names and the usage example. The test script reported `statsbar.sh: all 20 checks PASS`.

**Live here.** Yes. It is deployed at `~/.claude/hooks/review-gate/statsbar.sh` and is byte identical to the branch copy. Status `advisory`, and it is quoted inside the review-gate brief, which pushes the model to generate the bar rather than hand draw one.

### The review-gate brief file

**What it does.** Claude Code renders a Stop hook's reason string to your terminal verbatim. The review brief is roughly three kilobytes of instructions aimed at the model, not a message for you, and it was being dumped into your terminal on every code changing turn. `core.sh` now writes the brief to a file and returns a short pointer, and the pointer is what gets displayed. The file path is passed in by `gate.sh` as `RG_BRIEF_FILE`, landing under `~/.claude/review-state/` named by session id.

Three further changes shipped in the same edit. The changed file list is one path per line instead of space joined, because a space joined list becomes unsplittable the moment a path contains a space, and this checkout lives under a directory whose name contains one. The review body is now a Markdown table rather than prose bullets, with anything longer than a short clause pushed into numbered notes under the table. And the brief now asks for the counts as a generated `statsbar.sh` bar.

**How to test it.**

```bash
npm run test:review-gate-core
grep -n "RG_BRIEF_FILE" hooks/review-gate/scripts/gate.sh
```

Expected output. The test script reported `core.sh: all 22 checks PASS`. The grep returns the two lines in `gate.sh` where the variable is documented and set.

**Live here.** Yes. `core.sh`, `gate.sh`, `track.sh` and `statsbar.sh` in `~/.claude/hooks/review-gate/` are byte identical to the branch copies. `precommit.sh` differs, and the deployed one is the newer of the two, carrying the ssh-guard work that landed on `main` after this branch was cut. Status `enforced`.

## Rules

27 rule directories, 26 of them registered. All rules are `advisory` by nature, since a rule is text that persuades rather than a mechanism that compels. What varies is whether the text reaches the model at all.

Full descriptions are in [`rules/README.md`](../rules/README.md) and the per rule tables in [`INVENTORY.md`](../INVENTORY.md). This section covers only how a rule reaches the model and how you check it, which is the part no other document states.

Three routes exist, and each agent uses exactly one.

1. **Claude Code** reads `~/.claude/CLAUDE.md`. A rule is present either because you wrote it there yourself, or because `rule-activation.mjs --apply` put it in the managed block, or because it is listed in the ignore file as already covered in your own words.
2. **Codex** reads `~/.codex/AGENTS.md` by the same mechanism.
3. **opencode** declares an instructions glob over every rule file in [`opencode.json`](../opencode.json), so it loads all of them with no block needed.

The single test for all three.

```bash
node bin/rule-activation.mjs --check --verbose
```

Expected output, one block per agent, then `all registered rules are reachable` and exit 0. On failure it lists each unreachable rule and exits 1. Current state on this machine, verified.

| Agent | Target | Reachable | Notes |
|---|---|---|---|
| claude | `~/.claude/CLAUDE.md` | 26 of 26 | 19 matched by your own headings, 6 by the managed block, 1 by the ignore file |
| codex | `~/.codex/AGENTS.md` | 26 of 26 | Same mechanism |
| opencode | [`opencode.json`](../opencode.json) | 26 of 26 | Instructions glob, nothing to write |

The one rule outside this picture is `native-capability-first`, which is not registered and therefore not reachable anywhere. See [its entry above](#rulesnative-capability-first).

The ignore file lives at `~/.claude/agent-harness-rule-activation.ignore` and currently holds one entry, `root-cause-before-fix`, because your own code change engineering principles already carry the full seven step procedure in different words.

## Skills

23 skill directories at the top level, 11 more inside the general bucket, 19 registered. Every skill is `advisory`. Claude Code offers a discovered skill to the model and the model decides whether to open it.

**The two layer layout.** A name that appears both at `skills/<name>/` and at `skills/general/<name>/` is not a duplicate. The general bucket holds the canonical skill, and the top level file is a thin Codex wrapper that tells Codex to read the canonical one and then adapts it to Codex conventions. Compare [`skills/verify-template/SKILL.md`](../skills/verify-template/SKILL.md) at 991 bytes against [`skills/general/verify-template/SKILL.md`](../skills/general/verify-template/SKILL.md) at 2168 bytes to see the pattern.

**How to invoke any skill.** Use the `Skill` tool with the bare name for a skill deployed under `~/.claude/skills/`, or the `agent-harness:<name>` form for one served by the enabled plugin. Several skills are reachable both ways.

**How to test whether a skill is live.**

```bash
ls ~/.claude/skills/ | grep -x doc-writing || echo "not deployed"
node bin/deploy-skills.mjs                     # dry run, shows the plan for every skill
node bin/deploy-skills.mjs --apply             # write the symlinks
```

Current deployment state, verified by the dry run. It reported `plan: link=4 relink=30 ok=0 kept=4 nosrc=0`, meaning 4 targets are absent, 30 exist but point at a different copy of the repository, and 4 are real directories the deployer will not touch because they are your own standalone versions.

Per skill status for the ones with runnable behaviour. Every test command was run and every result is the real one.

| Skill | Test command | Result | Live here |
|---|---|---|---|
| [`memory-flywheel`](../skills/memory-flywheel/SKILL.md) | `python3 skills/memory-flywheel/scripts/test_mem.py` | `all 11 tests PASS` | yes |
| [`memory-flywheel`](../skills/memory-flywheel/SKILL.md) eval harness | `python3 skills/memory-flywheel/scripts/test_mem_eval.py` | `all 3 tests PASS` | yes |
| [`memory-flywheel`](../skills/memory-flywheel/SKILL.md) auto-record hook | `python3 skills/memory-flywheel/scripts/test_supervise.py` | `all 7 checks PASS` | script only, the hook is not installed and is off by default |
| [`prompt-library`](../skills/prompt-library/SKILL.md) | `python3 skills/prompt-library/scripts/test_plib.py` | `all 24 tests PASS` | yes, with the `--root` caveat |
| [`agent-update-watcher`](../skills/agent-update-watcher/SKILL.md) | `python3 skills/agent-update-watcher/scripts/test_check_updates.py` | `all 6 tests PASS` | yes, no fetcher |
| [`tui-installer`](../skills/tui-installer/SKILL.md) | `bash skills/tui-installer/scripts/test_install_tui.sh` | `all 11 checks PASS` | yes |
| [`task-relationship-analysis`](../skills/task-relationship-analysis/SKILL.md) | `python3 skills/task-relationship-analysis/scripts/test_scaffold.py` | `all 6 tests PASS` | yes |
| [`doc-writing`](../skills/doc-writing/SKILL.md) | `python3 skills/doc-writing/scripts/test_doccheck.py` | `20/20 tests PASS` | no, not deployed and not registered |
| [`figma-design-fetch`](../skills/figma-design-fetch/SKILL.md) | `node skills/figma-design-fetch/scripts/test_visual_diff.mjs` | not run, needs the pixelmatch dependency | yes as a skill |

The remaining skills are prose only, with no script to exercise. They are `code-verifier`, `research-critic`, `verify-template`, `preview-template`, `verify-visual`, `privacy-redact`, `long-running-tasks`, `figma-authoring-constraints`, `task-orchestrator`, `end-of-turn-marker`, `agent-config-adapter` and `init-codex-config`. For those, the test is that the model can find them, which you check by listing `~/.claude/skills/` or by asking for the skill by name in a session.

Five of the top level skills are not registered, so `deploy-skills.mjs` never places them under `~/.claude/skills/` and none of them is reachable by its bare name. Four of the five still arrive by the other route, because the enabled plugin serves the clone's whole skill directory, so `task-orchestrator`, `end-of-turn-marker`, `agent-config-adapter` and `init-codex-config` are all callable as `agent-harness:<name>`. `doc-writing` is the exception. It is absent from the clone as well, so neither route reaches it.

**Where `code-verifier` sits, since it is the sharpest example of advisory.** It is deployed, it is a real directory rather than a symlink because it is your own standalone copy, and it is named in review-gate form 4. None of that makes it run. Nothing in the harness blocks a completion claim on having opened it. Treating a deployed verification skill as a guarantee is exactly the mistake this guide is written to prevent.

## Hooks

6 hook directories. Hooks are the only `enforced` mechanism in the harness, and only three of the six are wired into `~/.claude/settings.json` on this machine.

**How to check what is actually wired.**

```bash
python3 -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(json.dumps(d['hooks'],indent=1))"
```

Verified state of that file right now.

| Hook | Event | Matcher | Wired here | Status |
|---|---|---|---|---|
| [`review-gate`](../hooks/review-gate/README.md) tracker | `PostToolUse` | `Write\|Edit` | yes, calls `track.sh` | `enforced` |
| [`review-gate`](../hooks/review-gate/README.md) commit guard | `PreToolUse` | `Bash` | yes, calls `precommit.sh` | `enforced` |
| [`review-gate`](../hooks/review-gate/README.md) stop gate | `Stop` | all | yes, calls `gate.sh` | `enforced` |
| [`ruff-format-on-edit`](../hooks/ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | yes, inline command rather than a script file | `enforced` |
| [`jq-validate-json`](../hooks/jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | yes, inline command | `enforced` |
| [`block-env-read`](../hooks/block-env-read/README.md) | `PreToolUse` | `Read` | no | `enforced` by design, not live |
| [`typecheck-on-edit`](../hooks/typecheck-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | no | `enforced` by design, not live |
| [`task-ledger`](../hooks/task-ledger/README.md) capture | `UserPromptSubmit` | all | no | `enforced` by design, not live |
| [`task-ledger`](../hooks/task-ledger/README.md) round gate | `Stop` | all | no | `enforced` by design, not live |

Two further entries in that file come from outside this branch. `ssh-guard` on `PreToolUse` was added on `main` after this branch was cut and is live. The autopilot session check on `SessionStart` comes from the autopilot skill.

### review-gate

**What it does.** Tracks which files a turn changed, then on `Stop` returns a review brief and blocks the turn from ending until one review round has happened. The brief lists numbered review forms covering correctness, minimal change, modularity, fake run detection, commit and doc hygiene, adversarial inputs, and a red to green regression test when the turn fixed a bug. Per function review is added when a small module changed. It also guards `git commit` and `git push` through the `PreToolUse` matcher on `Bash`.

**How to invoke it.** You do not. It fires on `Stop` for every turn that changed code.

**How to test it.**

```bash
npm run test:review-gate-core
bash hooks/review-gate/scripts/test_precommit.sh
cat ~/.claude/hooks/review-gate/review-gate.conf
```

Expected output. `core.sh: all 22 checks PASS` and `precommit.sh: all 22 tests PASS`. The config file on this machine reads `block_commit=0` and `stop_mode=block`.

**Two settings worth knowing.** `stop_mode=block` is the default and is what makes the review unavoidable, at the cost of the round being labelled a stop hook error by recent Claude Code versions. The label is cosmetic and the review still runs. `stop_mode=feedback` gets a clean label but the review becomes skippable, which is to say advisory. There is no output that both blocks and avoids the label. `block_commit=0` leaves `git commit` free while `git push` stays guarded.

**Cross agent.** The review logic lives in one shared `core.sh` with thin per agent shims, so Claude Code, Codex and opencode run the same review. The Codex shim is [`scripts/codex_review_gate.sh`](../scripts/codex_review_gate.sh) and the opencode one is under [`.opencode/plugin/`](../.opencode/plugin). Test them with `bash scripts/test_codex_review_gate.sh` and `npm run test:opencode-review`, which reported `opencode review helper: all 6 checks PASS`.

### The other five hooks

Each ships with its own README carrying the install snippet, and each has a test.

| Hook | What it does | Test command | Result |
|---|---|---|---|
| [`ruff-format-on-edit`](../hooks/ruff-format-on-edit/README.md) | Runs ruff format and ruff check on a Python file after the model writes it | `bash scripts/test_codex_ruff_format_on_edit.sh` | pass, as part of `npm run verify:codex` |
| [`jq-validate-json`](../hooks/jq-validate-json/README.md) | Blocks the next tool call if invalid JSON was written to a configured path | covered by the inline command in `~/.claude/settings.json` | wired and live |
| [`block-env-read`](../hooks/block-env-read/README.md) | Denies reading any `.env` file so secrets never enter the transcript | `bash hooks/block-env-read/test_block_env.sh` | `block-env.sh: all 12 checks PASS` |
| [`typecheck-on-edit`](../hooks/typecheck-on-edit/README.md) | Runs prettier then a no-emit type check after a TypeScript edit, and a type error blocks the turn | `bash hooks/typecheck-on-edit/test_typecheck.sh` | not run, needs a TypeScript toolchain |
| [`task-ledger`](../hooks/task-ledger/README.md) | Refuses to end a round with unfinished tasks | `npm run test:task-ledger` | `all 11 tests PASS` after 16 Python tests |

## Slash commands

Two commands, both `advisory` since you type them, and both live through the enabled plugin.

| Command | What it does | Test |
|---|---|---|
| `/harness-sync` | Updates agent-harness, shows what changed, recommends the parts relevant to the current task, asks before applying, and activates the latest rules in the current session without a restart. It is also the read end of the harness feedback queue. | Type `/harness-sync` in a session, or read [`commands/harness-sync.md`](../commands/harness-sync.md) |
| `/figma-fetch` | Fetches a Figma design node, meaning its code, assets and screenshot, into a gitignored import directory through the Figma MCP. | Type `/figma-fetch <node-url>`, or read [`commands/figma-fetch.md`](../commands/figma-fetch.md) |

To confirm both are registered with the plugin, check that the `agent-harness` plugin is enabled in `~/.claude/settings.json` under `enabledPlugins`. It is, sourced from a local directory marketplace pointing at the clone described below.

## Repository tools

Nine tools under [`bin/`](../bin) and [`scripts/`](../scripts). All are `advisory` in the sense that you or the model must run them, though two of them are what make other things work at all.

| Tool | What it does | Invoke | Test | Result |
|---|---|---|---|---|
| [`bin/rule-activation.mjs`](../bin/rule-activation.mjs) | Reports and fixes registered but inert rules | `node bin/rule-activation.mjs --check` | `npm run test:rule-activation` | `all 26 checks PASS` |
| [`bin/harness-feedback.mjs`](../bin/harness-feedback.mjs) | Records a harness feature that did not fit | `node bin/harness-feedback.mjs --list` | `npm run test:harness-feedback` | `all 9 tests PASS` |
| [`bin/deploy-skills.mjs`](../bin/deploy-skills.mjs) | Symlinks every registered skill into each agent's global skill directory, additive and non clobbering, dry run by default | `node bin/deploy-skills.mjs --apply` | `npm run test:deploy-skills` | `all 9 checks PASS` |
| [`build.mjs`](../build.mjs) | Regenerates all three agent manifests from the one canonical source | `node build.mjs` | `npm run check:manifests` | `check OK: all manifests match source` |
| [`adapters/test-projection.mjs`](../adapters/test-projection.mjs) | Byte parity gate between the source inventory and each generated manifest | `npm run test:projection` | same | `all 3 parity test(s) PASS` |
| [`scripts/resolve_model.mjs`](../scripts/resolve_model.mjs) | Resolves the model id for an agent and a task tier | `node scripts/resolve_model.mjs claude research` | `npm run test:models` | `all 31 checks PASS`, and the invocation above returned `claude-opus-4-8` |
| [`scripts/install-codex-local.js`](../scripts/install-codex-local.js) | Installs 20 user skills, the plugin entry, user agent instructions, hooks and four custom agent profiles into Codex | `npm run install:codex` | `npm run test:codex-install` | `isolated 20-skill/user-surface install PASS` |
| [`scripts/verify-codex-adapter.js`](../scripts/verify-codex-adapter.js) | Structural checks over the whole Codex adapter | `npm run verify:codex` | same | runs the installer, model, ruff and review-gate tests together |
| [`scripts/codex-update-safe.js`](../scripts/codex-update-safe.js) | Safe Codex updater for release asset rollout windows | `npm run update:codex` | no dedicated test | not exercised |

Two more scripts, [`scripts/actions-budget.mjs`](../scripts/actions-budget.mjs) and the workflow templates under [`templates/actions-frugal-ci/`](../templates/actions-frugal-ci), landed in the same round but are owned by separate work and are not documented here. `node scripts/actions-budget.mjs --help` describes an offline budget check over `.github/workflows` on disk, reporting which workflows fire on a pull request, on a merge and on a schedule, how far each fans out, and the billable minutes floor.

**The one command that runs everything.**

```bash
for t in check:manifests test:projection test:opencode-review test:deploy-skills \
         test:rule-activation test:models test:codex-install test:harness-feedback \
         test:task-ledger test:review-gate-core; do npm run --silent $t >/dev/null 2>&1 \
  && echo "PASS $t" || echo "FAIL $t"; done
```

All ten printed pass on this machine on 2026-07-18.

## Templates, tooling, recommendations, setup

All `advisory`. These are read or copied, never executed against you.

| Area | Contents | Where |
|---|---|---|
| Templates | A Python research package using uv, ruff and pytest; a static personal academic site with internationalization; and a frugal continuous integration workflow set | [`templates/README.md`](../templates/README.md) |
| Tooling | Python with uv and ruff, Node with nvm, and a permissions allowlist snippet | [`tooling/README.md`](../tooling/README.md) |
| Recommendations | 20 files covering plugins, marketplaces, command line tools, UI and animation libraries, auditing, docs, machine learning research, cluster patterns, reference projects, and the terminal stack | [`recommendations/README.md`](../recommendations/README.md) |
| Setup | The interactive scaffold that composes the right subset of everything above into a project | [`setup/init-agent-config/SKILL.md`](../setup/init-agent-config/SKILL.md) |

The scaffold is invoked as `/init-agent-config` or `Skill(init-agent-config)`. It asks about project type, language preferences and context tags, then writes a project specific `CLAUDE.md`, a settings file and starter files. Step by step walkthroughs for a new Python research package, a new static site and an existing project are already in [`USAGE.md`](../USAGE.md), which this guide does not duplicate.

## How deployment works on this machine

This section exists because the answer to whether a change is live depends on a detail that no other document states.

There are two copies of this repository on this machine, and the agent reads the other one.

1. **This checkout**, on branch `feat/harness-meta-optimization-2026-07-18`, is where the work happens.
2. **A separate clone at `~/.claude/agent-harness`**, sitting on `main`, is what the plugin marketplace points at and what every deployed skill symlink resolves into.

So a skill added on this branch is not live until either the clone is updated, or `node bin/deploy-skills.mjs --apply` is run from this checkout to repoint the symlinks. The dry run reports exactly this, with 30 of 38 targets marked for relinking because they currently point into the clone.

**What is live from this branch anyway**, because it was copied or applied by hand during the round.

1. The review-gate scripts `core.sh`, `gate.sh`, `track.sh` and `statsbar.sh`, all byte identical to the branch copies.
2. The managed rules block in `~/.claude/CLAUDE.md`, written by `rule-activation.mjs --apply`.

**What is not live from this branch.** Everything else new this round, which is `rules/native-capability-first`, `hooks/task-ledger`, `bin/rule-activation.mjs`, `bin/harness-feedback.mjs`, `skills/doc-writing` and `recommendations/prompt-library/`. None of them exist in the clone. They all run from this checkout by path.

**One divergence in the other direction.** The deployed `precommit.sh` is newer than the branch copy. It carries the ssh-guard work that landed on `main` after this branch was cut, and this branch does not contain `hooks/ssh-guard` at all. Rebasing onto `main` is tracked separately.

**Codex behaves differently from the other two.** Claude Code and opencode use symlinks and pick up clone updates automatically. The Codex plugin cache is copy based, so it needs `codex plugin remove` followed by `codex plugin add` after each clone update.

**How to check any of this yourself.**

```bash
readlink -f ~/.claude/skills/memory-flywheel        # which copy the agent actually reads
node bin/deploy-skills.mjs                          # the full plan, writes nothing
node bin/rule-activation.mjs --check                # whether rules reach each agent
grep -c "agent-harness:rules:begin" ~/.claude/CLAUDE.md   # 1 if the managed block is present
```

## Verification log

Everything below was run on 2026-07-18 from this checkout. Nothing in this guide is claimed without a run behind it.

| Command | Result |
|---|---|
| `npm run check:manifests` | `check OK: all manifests match source` |
| `npm run test:projection` | `projection: all 3 parity test(s) PASS` |
| `npm run test:opencode-review` | `opencode review helper: all 6 checks PASS` |
| `npm run test:deploy-skills` | `deploy-skills.mjs: all 9 checks PASS` |
| `npm run test:rule-activation` | `rule-activation.mjs: all 26 checks PASS` |
| `npm run test:models` | `resolve_model: all 31 checks PASS` |
| `npm run test:codex-install` | `install-codex-local: isolated 20-skill/user-surface install PASS` |
| `npm run test:harness-feedback` | `harness-feedback.mjs: all 9 tests PASS` |
| `npm run test:task-ledger` | `task-ledger hooks: all 11 tests PASS` |
| `npm run test:review-gate-core` | `core.sh: all 22 checks PASS` |
| `bash hooks/review-gate/scripts/test_statsbar.sh` | `statsbar.sh: all 20 checks PASS` |
| `bash hooks/review-gate/scripts/test_precommit.sh` | `precommit.sh: all 22 tests PASS` |
| `bash hooks/block-env-read/test_block_env.sh` | `block-env.sh: all 12 checks PASS` |
| `python3 skills/doc-writing/scripts/test_doccheck.py` | `doccheck.py: 20/20 tests PASS` |
| `python3 skills/memory-flywheel/scripts/test_mem.py` | `mem.py: all 11 tests PASS` |
| `python3 skills/memory-flywheel/scripts/test_mem_eval.py` | `mem_eval.py: all 3 tests PASS` |
| `python3 skills/memory-flywheel/scripts/test_supervise.py` | `supervise.py: all 7 checks PASS` |
| `python3 skills/prompt-library/scripts/test_plib.py` | `plib.py + plib_mine.py: all 24 tests PASS` |
| `python3 skills/agent-update-watcher/scripts/test_check_updates.py` | `check_updates.py: all 6 tests PASS` |
| `python3 skills/task-relationship-analysis/scripts/test_scaffold.py` | `scaffold.py: all 6 tests PASS` |
| `bash skills/tui-installer/scripts/test_install_tui.sh` | `install-tui.sh: all 11 checks PASS` |
| `node bin/rule-activation.mjs --check` | `all registered rules are reachable`, 26 of 26 for all three agents |
| `node bin/harness-feedback.mjs --list` | `no open entries` |
| `python3 hooks/task-ledger/scripts/ledger.py status` | `Harness meta optimization — 8/16 settled · 8 todo` |
| `bash skills/tui-installer/scripts/install-tui.sh --check` | `4 of 4 recommended tools missing.` |
| `node scripts/resolve_model.mjs claude research` | `claude-opus-4-8` |
| `node bin/deploy-skills.mjs` | `plan: link=4 relink=30 ok=0 kept=4 nosrc=0` |

Two tests were not run, and neither result is claimed. [`hooks/typecheck-on-edit/test_typecheck.sh`](../hooks/typecheck-on-edit/test_typecheck.sh) needs a TypeScript toolchain, and [`skills/figma-design-fetch/scripts/test_visual_diff.mjs`](../skills/figma-design-fetch/scripts/test_visual_diff.mjs) needs the pixelmatch dependency.

## Known stale docs

Found while writing this guide, listed rather than edited, since these files belong to other work.

1. **[`docs/strategy/agent-harness-overhaul-2026-07-09/STATUS.md`](strategy/agent-harness-overhaul-2026-07-09/STATUS.md) contradicts [`docs/OVERHAUL_DELIVERY.md`](OVERHAUL_DELIVERY.md), and both carry the same date.** The status dashboard marks task 8 for the terminal stack and task 9 for the prompt library as not started, tasks 3 and 4 for memory as missing, and task 5 as designed only. The delivery summary says all five shipped, and the code confirms the delivery summary. The status dashboard also lists its own tally as one done, eight partial, two researched and four missing, which no longer describes anything.
2. **The same status dashboard contradicts itself.** Its header states that the review-gate de-fork is complete across all three agents, and its recommended next sequence opens by proposing that same de-fork as the next step.
3. **[`docs/OVERHAUL_DELIVERY.md`](OVERHAUL_DELIVERY.md) undercounts.** It states 16 published skills and 20 rules. The repository now holds 23 top level skill directories and 27 rule directories. Its task 7 row also reads as though plugin hygiene were a shipped capability, when the three items behind it were one off manual edits.
4. **[`INVENTORY.md`](../INVENTORY.md) headline counts are behind its own tables.** The rules section says 14 rules and then lists 26 rows. The skills section says 8 general bucket skills and then lists 11 rows, while omitting `memory-flywheel`, `prompt-library`, `agent-update-watcher`, `tui-installer`, `task-relationship-analysis`, `doc-writing` and `task-orchestrator` entirely. The hooks section says 2 hooks and lists 4, omitting `review-gate` and `task-ledger`. Registration is owned elsewhere, so this guide records the drift rather than repairing it.
5. **[`README.md`](../README.md) section headings are approximate.** They read 15 or more workflow rules and 8 hooks, against 27 rule directories and 6 hook directories.

## Remaining gaps

Collected in one place, each with what it costs you today.

1. **`rules/native-capability-first` is inert.** It is unregistered, so it never enters any agent's context. Everything it governs, including the feedback loop into `harness-feedback.mjs`, is inactive until it is registered and a `--apply` run picks it up.
2. **`skills/doc-writing` is not discoverable.** Unregistered and undeployed, so the model will not find it by name and will keep writing documents without it. The linter still works by path.
3. **`hooks/task-ledger` is not installed.** The round document and its command line work, but nothing blocks on unfinished work, which is the entire point of the hook.
4. **`agent-update-watcher` has no fetcher.** It compares versions you supply. Nothing obtains them and no timer runs it.
5. **Automatic plugin curation does not exist.** No tool was ever built for it.
6. **There is no context footprint measurement.** Task 2 of the overhaul was designed and not built, so no number tells you whether context optimization is working.
7. **This branch is behind `main`.** The deployed `precommit.sh` and the whole `hooks/ssh-guard` directory exist on `main` and not here.
8. **Deployed skills point at a different clone.** Until `deploy-skills.mjs --apply` runs from this checkout, or the clone is updated, nothing new from this branch is reachable by skill name.
