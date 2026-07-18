# GitHub Actions Frugality

> How to stop burning remote Actions minutes without giving up the checks that catch real bugs. Verified 2026 billing facts, a tiered scheme with an explicit default, and a check script that measures a repository before and after. **Context:** `always` (any repository that has workflows).

## Master TOC

- [The short version](#the-short-version)
- [The billing model, verified](#the-billing-model-verified)
- [What changed in 2026](#what-changed-in-2026)
- [The multiplier question, honestly](#the-multiplier-question-honestly)
- [The levers, ranked](#the-levers-ranked)
- [Verdicts on the five candidate ideas](#verdicts-on-the-five-candidate-ideas)
- [The tiered scheme](#the-tiered-scheme)
- [Which profile fits your repository](#which-profile-fits-your-repository)
- [Which account is being billed](#which-account-is-being-billed)
- [Worked example with real numbers](#worked-example-with-real-numbers)
- [Self-hosted runners](#self-hosted-runners)
- [Running workflows locally with act](#running-workflows-locally-with-act)
- [Pre-push local gates](#pre-push-local-gates)
- [The check script](#the-check-script)
- [What I could not verify](#what-i-could-not-verify)
- [Sources](#sources)

## The short version

1. **If the repository is public, stop reading.** Standard GitHub-hosted runners are free in public repositories, so none of this saves money. Optimise for feedback latency instead.
2. **Get non-Linux jobs off the pull request path.** A macOS minute costs 10.33 Linux minutes at list price. This is usually the single biggest number in the bill and it is a one line change.
3. **Add `concurrency` with `cancel-in-progress` to every workflow a pull request can trigger.** Without it, pushing three times in five minutes pays for three full runs.
4. **Never pair an unfiltered `on: push` with `on: pull_request`.** That runs everything twice per push to a PR branch. Filter push to the default branch.
5. **Remember the per job rounding.** GitHub "rounds the minutes and partial minutes each job uses up to the nearest whole minute", so nine 20 second jobs bill nine minutes while one 3 minute job bills three.
6. **Move the expensive suite behind a label, the default branch, a schedule, or a manual dispatch.** A job skipped by an `if:` never gets a runner and costs nothing.
7. **Run the same checks locally before the push.** A failed remote run is a run you paid for twice.

Measure rather than guess:

```bash
node scripts/actions-budget.mjs /path/to/repo
```

## The billing model, verified

Included allowance per month, for **private** repositories only ([GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)):

| Plan | Included minutes | Artifact storage | Cache storage |
|---|---|---|---|
| Free | 2,000 | 500 MB | 10 GB |
| Pro | 3,000 | 1 GB | 10 GB |
| Team | 3,000 | 2 GB | 10 GB |
| Enterprise Cloud | 50,000 | 50 GB | 10 GB |

Standard runner rates since 1 January 2026 ([Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)):

| Runner | USD per minute | Ratio to Linux x64 |
|---|---|---|
| Linux 1-core x64 | 0.002 | 0.33x |
| Linux 2-core x64 | 0.006 | 1x (the baseline) |
| Linux 2-core arm64 | 0.005 | 0.83x |
| Windows 2-core x64 | 0.010 | 1.67x |
| Windows 2-core arm64 | 0.010 | 1.67x |
| macOS 3-core or 4-core | 0.062 | **10.33x** |
| macOS 12-core | 0.077 | 12.83x |
| macOS 5-core M2 Pro | 0.102 | 17x |

The ratio column is arithmetic on the published rates, not a figure GitHub prints.

Facts that change how you design a workflow:

- **Public repositories are free** on standard GitHub-hosted runners. "The use of standard GitHub-hosted runners is free: In public repositories; For GitHub Pages; For Dependabot." Larger runners are **not** free for public repositories.
- **Self-hosted runners are free** today. "GitHub Actions usage is free for standard GitHub-hosted runners in public repositories, and for self-hosted runners." See [What changed in 2026](#what-changed-in-2026) before relying on that.
- **Every job rounds up.** "GitHub rounds the minutes and partial minutes each job uses up to the nearest whole minute." A workflow's floor cost is its job count in minutes, whatever the jobs actually do.
- **A job with no `timeout-minutes` can run for 6 hours** before GitHub kills it, and you pay for all of it ([usage limits](https://docs.github.com/en/actions/reference/limits)).
- **A skipped job costs nothing.** It never gets a runner. That is what makes `if:` gating free.
- **arm64 standard runners are public repository only.** "These runners are only available in public repositories and will not work in private repositories." Since public repositories are already free, the 0.83x arm64 rate is not a lever for a private repository unless you are on Team or Enterprise and use arm64 larger runners.
- **Concurrent job caps** are 20 on Free, 40 on Pro, 60 on Team, 500 on Enterprise, with macOS capped at 5 (50 on Enterprise). A wide matrix queues rather than fanning out.
- **Cache** is 10 GB per repository by default with entries evicted after 7 days without a read. Since November 2025 the limit can be raised, and storage above the default is charged.
- **`[skip ci]` only works on `push` and `pull_request`.** Accepted forms are `[skip ci]`, `[ci skip]`, `[no ci]`, `[skip actions]`, `[actions skip]`, and the `skip-checks: true` trailer. It will not stop a `pull_request_target` or `schedule` run.

## What changed in 2026

Two things, one of which reversed:

1. **Hosted runner prices fell by up to 39% on 1 January 2026**, with a new 0.002 USD per minute cloud platform charge already folded into the reduced rates. GitHub says "96% of customers will see no change to their bill".
2. **A 0.002 USD per minute charge for self-hosted runners was announced for 1 March 2026, then postponed.** GitHub's own words: "We're postponing the announced billing change for self-hosted GitHub Actions to take time to re-evaluate our approach." The reversal came less than a day after the announcement. Public repository usage stays free either way, and the hosted price cut went ahead.

The practical reading is that self-hosted runners are free today and that their free status is a policy decision GitHub has already tried once to change. Do not build a strategy whose only saving is "self-hosted is free".

## The multiplier question, honestly

The widely repeated rule is Linux 1x, Windows 2x, macOS 10x. Here is the current state, because this is the number most worth getting right:

- GitHub's documentation URL `/billing/reference/actions-minute-multipliers` now redirects to `/billing/reference/actions-runner-pricing`, which lists per-minute prices and no multiplier table.
- The December 2025 changelog describes the change as replacing OS-based multipliers with direct per-minute rates.
- Derived from the published rates, the real ratios are **Windows 1.67x** and **macOS 10.33x**. The folklore figure for macOS is close enough. The folklore figure for Windows overstates it by about 20%.
- What I could **not** find in current documentation is a sentence stating exactly how the included minutes allowance is drawn down for a non-Linux job. The billing and usage page says only that "GitHub Actions usage metrics do not apply minute multipliers to the metrics displayed", which is about the metrics dashboard rather than about billing. The changelog says self-hosted usage would "consume available usage based on list price the same way that Linux, Windows, and MacOS standard runners work today", which implies the allowance is drawn down in proportion to list price.

Both readings agree that macOS costs about ten times Linux, so the guidance does not change. The check script uses the list price ratio and prints its rate card date so the assumption is visible rather than buried.

## The levers, ranked

Ranked by saving per unit of effort, with the arithmetic that produces the saving.

| # | Lever | Typical saving | Effort |
|---|---|---|---|
| 1 | Move macOS and Windows jobs off the pull request path | Up to 90% of those jobs' cost (`1 - 1/10.33`) | One `if:` or a move to another workflow |
| 2 | `concurrency` + `cancel-in-progress` on PR workflows | Everything spent on superseded runs. On a branch pushed 3 times before CI finishes, up to 67% | Four lines per workflow |
| 3 | Filter `on: push` to the default branch when `on: pull_request` is also set | Exactly 50% of that workflow | One line |
| 4 | Collapse tiny jobs into one job | `(jobs - 1)` minutes per run, from the per job round-up | Restructuring |
| 5 | Gate the heavy suite behind a label, schedule, or dispatch | The whole difference between the fast and full suite on ordinary PRs | A job level `if:` |
| 6 | Cache dependencies | Often 30 to 60 seconds per job | A `cache:` input |
| 7 | Trim the matrix, keep `fail-fast: true` | Proportional to the combinations removed | Editing the matrix |
| 8 | `timeout-minutes` on every job | Nothing on average, up to 6 hours per hung job | One line per job |
| 9 | Weekly rather than nightly schedules | About 75% of the scheduled cost | One cron field |
| 10 | Local pre-push gate | Every remote run that would have failed | A hook plus the discipline to keep it fast |

Levers 1 to 3 are where nearly all of the money is in a small repository, and all three are single line changes.

## Verdicts on the five candidate ideas

These were the starting hypotheses. Three hold, one is partly right, one is usually wrong.

| Idea | Verdict | Why |
|---|---|---|
| **(a)** Test big features locally, push less often | **Holds, with a ceiling** | It removes *failed* runs and reduces push count. It does not reduce the per-PR baseline, because a PR still needs at least one remote run. Pair it with (b) rather than treating it as the whole answer. |
| **(b)** Do not run the full set for an incomplete change | **Holds, and it is the core of the scheme** | This is the tier split. One caveat below on required checks. |
| **(c)** Run some workflows only under specific conditions | **Holds** | A job skipped by an `if:` never gets a runner. Label gating a heavy suite is free when the label is absent. |
| **(d)** Do it locally with Actions tooling before the push | **Partly** | `act` is good for authoring workflows, poor as a CI substitute. See below. The better version of this idea is to run the *commands* locally in a pre-push hook, not to emulate the workflow. |
| **(e)** Self-hosted runner so it does not consume included minutes | **Usually wrong as a first move** | True today, but it saves nothing at all on a public repository (already free) while adding a real security exposure, and GitHub has already tried once to start charging. See below. |

The caveat on (b): **do not use a `paths` filter to skip a workflow that is a required check.** GitHub is explicit: "You should not use path or branch filtering to skip workflow runs if the workflow is required to pass before merging. As an alternative, if a job within a workflow is skipped due to a conditional, it will report its status as Success." A workflow skipped by a paths filter leaves its check Pending forever and blocks the merge. Gate the *jobs* with `if:`, or keep paths filters to workflows that are not required.

## The tiered scheme

Four tiers. The first two never touch GitHub's runners.

| Tier | Where | Budget | What belongs here |
|---|---|---|---|
| **0** | `pre-commit`, local | Under 5 seconds | Formatter on staged files, conflict markers, debugger statements, whitespace, JSON and YAML validity |
| **1** | `pre-push`, local | Under 90 seconds | Lint the whole tree, type check, unit tests, the actions budget check |
| **2** | Pull request, remote | Under 5 minutes, Linux only | Install, lint, type check, unit tests. One job. The only required check |
| **3** | Merge, schedule, label, dispatch | No limit | Integration and end to end tests, the cross-platform matrix, long fuzzing, release builds, dependency audits |

Rules that make the tiers hold:

- **Tier 1 and tier 2 run the same commands.** When they drift, the hook stops predicting the remote result and people stop trusting it.
- **Tier 1 needs an escape hatch** (`SKIP_PREPUSH=1`). A hook people cannot bypass is a hook people delete.
- **Only tier 2 is a required check.** Tier 3 is deliberately skippable, so it must not be required.
- **Tier 2 is one job, not four.** Four 30 second jobs bill 4 minutes. One 2 minute job bills 2. Split a job out only when a step exceeds roughly two minutes, where the wall clock saving beats the extra rounded up minute.
- **Tier 3 pays for the cross-platform matrix once per merge**, not once per push.

Ready to use: [`templates/actions-frugal-ci/`](../templates/actions-frugal-ci/TEMPLATE_README.md).

## Which profile fits your repository

The right answer differs by repository, so pick a profile rather than applying one scheme everywhere.

| Profile | When | Scheme | Expected outcome |
|---|---|---|---|
| **A. Small private repository on Free or Pro** ← **the default** | 1 to 8 developers, private, 2,000 to 3,000 included minutes | All four tiers, tier 3 weekly and label gated, Linux only except a weekly platform check | Comfortably inside the allowance |
| **B. Public repository** | Open source, any size | Tiers 0 to 2 for speed, skip the frugality work entirely | Minutes are free. Optimise feedback latency and reviewer attention |
| **C. Team or Enterprise with a large suite** | Paid plan, long test suite, many merges | Add a merge queue, and consider self-hosted for the sustained Linux load | Merge queue trades minutes for correctness, see below |
| **D. Private repository needing macOS or Windows regularly** | Desktop or mobile targets | Tiers 0 to 2 Linux only, all non-Linux work in tier 3, then evaluate a self-hosted macOS box | macOS is where self-hosted pays back fastest |

Profile C's merge queue is a genuine trade rather than a saving. Every pull request runs checks on its own branch and then again in the merge group, so you pay roughly twice per change in exchange for never merging an untested combination. It is worth it when a broken default branch is expensive, and not worth it on a repository with three merges a week.

## Which account is being billed

The allowance is attached to the **account that owns the repository**, not to the person who pushed.
A personal repository draws on the personal account's allowance; a repository owned by an organisation
draws on that organisation's, at that organisation's plan. Someone with a personal Pro plan pushing to
an organisation's Free repository gets the organisation's Free allowance, not their own Pro one.

Three things follow, and they are why one global answer to "should I self-host" does not exist.

1. **Two accounts means two separate budgets.** Exhausting one does not touch the other, and a change
   that helps one does nothing for the other.
2. **Visibility decides whether minutes are billed at all.** Standard hosted runners are free on public
   repositories regardless of plan. On a private repository the same job draws down the allowance and
   then bills.
3. **Therefore the correct scheme differs per repository**, not per person. A public repository needs
   none of this work. A private repository on a Free organisation is where every lever in this document
   earns its keep, and where a self-hosted runner stops being pointless and starts saving real money.

Work out which case each repository is in before applying anything here:

```bash
# Owner and visibility, per repository
gh repo view <owner>/<repo> --json nameWithOwner,visibility,isPrivate

# Actual minutes used against the allowance, per account. The first is your personal account;
# the second is an organisation you belong to. They are separate ledgers.
gh api /users/<your-login>/settings/billing/actions
gh api /orgs/<org>/settings/billing/actions

# Which plan each account is on, which sets the allowance in the table above
gh api /users/<your-login> --jq .plan.name
gh api /orgs/<org> --jq .plan.name
```

| Repository | Owner | Visibility | Minutes billed? | What to apply |
|---|---|---|---|---|
| Personal, public | personal account | public | No | Nothing here. Tune for feedback latency instead |
| Personal, private | personal account | private | Yes, against the personal allowance | The full tiered scheme |
| Organisation, public | organisation | public | No | Nothing here |
| Organisation, private | organisation | private | Yes, against the ORGANISATION's allowance | The full tiered scheme, and self-hosted becomes worth costing out |

`actions-budget.mjs` assumes a private repository when run offline, because reporting a cost that turns
out to be free is safer than reporting free minutes that are actually billed. Pass `--visibility public`
to state it, or `--live` to have `gh` report the real value.

## Worked example with real numbers

A realistic small team repository: 5 developers, 10 pushes a day to pull request branches, 1 merge a day, 30 days, Free plan, private.

**Before**, a naive but common layout. One workflow, `on: [push, pull_request]`, three jobs (lint, test, build), each on a three OS matrix, no concurrency group, no caching:

```
one PR update (pull_request + branch push)       18 jobs    312 Linux-equivalent min   $1.872
push/merge to main                                9 jobs    156 Linux-equivalent min   $0.936
runner mix per PR update: linux=6  macos=6  windows=6
monthly estimate                                        98,280 min   (4,914% of Free)
```

**After**, `templates/actions-frugal-ci` applied unchanged:

```
one PR update (pull_request + branch push)        3 jobs     12 Linux-equivalent min   $0.072
push/merge to main                                5 jobs     60 Linux-equivalent min   $0.360
runner mix per PR update: linux=3
monthly estimate                                         5,622 min   (281% of Free)
```

That is **96% off the per pull request cost** and **94% off the monthly projection**, at 4 minutes per job. Reproduce both numbers with:

```bash
node scripts/actions-budget.mjs <repo> --minutes-per-job 4 --pushes-per-day 10 --merges-per-day 1
```

Now the honest part. The "after" figure still exceeds the Free allowance, because 10 pushes a day at 4 minutes a job is a lot of CI for a 2,000 minute plan. The result depends heavily on assumptions, so here is the sensitivity rather than one flattering number:

| Configuration | min per job | pushes per day | Monthly estimate | Share of Free |
|---|---|---|---|---|
| Before | 4 | 10 | 98,280 | 4,914% |
| Before | 2 | 10 | 49,140 | 2,457% |
| After | 4 | 10 | 5,622 | 281% |
| After | 2 | 10 | 2,811 | 141% |
| After | 2 | 5 | 1,911 | 96% |
| After, no cross-platform matrix | 4 | 10 | 3,977 | 199% |
| After, no cross-platform matrix | 2 | 10 | 1,989 | 99% |
| After, no cross-platform matrix | 2 | 5 | 1,089 | 54% |

Read that table as the actual finding: **the tiered scheme buys a factor of 17 to 25, and whether that lands inside the Free allowance still depends on job duration and push frequency.** A repository that needs 4 minute jobs and 10 pushes a day is going to pay for a plan, and the honest advice there is that Team at 3,000 minutes plus this scheme is cheaper than fighting to fit into Free. The scheme's job is to make the bill proportional to the work, not to make it zero.

The floor column matters too. At 10 pushes a day the "after" floor is about 1,470 minutes a month before any job does anything, purely from the per job round-up. Below roughly one minute of real work per job, cutting job *count* saves more than making jobs faster.

## Self-hosted runners

**GitHub's warning, verbatim:** "We recommend that you only use self-hosted runners with private repositories. This is because forks of your public repository can potentially run dangerous code on your self-hosted runner machine by creating a pull request that executes the code in a workflow."

The exposure is not limited to public repositories. On a private or internal repository, anyone who can fork and open a pull request, which generally means anyone with read access, can compromise the runner, including the secrets and the `GITHUB_TOKEN` available to it.

**When it is worth it.** Break even against a machine costing 20 USD a month:

| Runner class | Rate | Minutes per month to break even |
|---|---|---|
| Linux 2-core | 0.006 | ~3,300 |
| Windows 2-core | 0.010 | ~2,000 |
| macOS standard | 0.062 | **~320** |

So a self-hosted macOS box pays for itself at about 5 hours of macOS CI a month, while a self-hosted Linux box needs roughly 55 hours before it beats hosted, and that ignores your time maintaining it. That asymmetry, not a general principle, is why macOS is the classic self-hosted case.

**When it is a mistake.**

1. **On a public repository it saves nothing**, because hosted runners are already free there, while adding the fork risk in full. This is the case where the idea is purely negative.
2. **On a private repository with outside collaborators**, where read access is enough to attack the runner.
3. **When the volume is low.** Below the break even minutes above, you are paying in maintenance for a smaller bill.
4. **As the only saving.** GitHub announced a self-hosted charge for March 2026 and withdrew it. It is free by policy, not by guarantee.

If you do run one, keep it to private repositories, prefer ephemeral single job runners so state cannot leak between runs, scope it with runner groups, and require approval before workflows run for first time contributors. See [secure use reference](https://docs.github.com/en/actions/reference/security/secure-use).

## Running workflows locally with act

[`act`](https://github.com/nektos/act) (v0.2.89, June 2026) runs workflows locally in Docker.

**What it is good for:** iterating on workflow YAML without a push-and-wait cycle, and debugging a single Linux job.

**What it does not do**, from the project's own [unsupported list](https://nektosact.com/not_supported.html):

- `concurrency` is ignored
- `job.timeout-minutes` is ignored
- `job.permissions` is ignored
- `job.continue-on-error` is ignored
- `job.environment` is ignored, and environment scoped secrets are unsupported
- the OpenID Connect URL is undefined
- `GITHUB_STEP_SUMMARY` output is discarded, problem matchers and annotations are ignored
- the `github` context is incomplete, step cancellation is unimplemented
- Docker context will not be implemented

Beyond that list: the default images do not carry everything GitHub's runner images do, jobs run in containers rather than virtual machines so anything needing systemd fails, the artifact server is not started by default, `--matrix` cannot add values that are not already in the workflow, and `exclude` takes precedence over it. macOS and Windows runners cannot be emulated at all.

**Verdict on idea (d).** `act` shortens the loop for *changing a workflow*. It does not lower your steady state minutes, because the expensive thing on every pull request is your test suite, and you can run that directly with no emulation layer. Use `act` when editing workflow YAML. Use a pre-push hook for everything else.

## Pre-push local gates

The point of tier 1 is that a check which fails locally never becomes a remote run.

| Tool | Runtime needed | Parallel | Best for |
|---|---|---|---|
| [lefthook](https://github.com/evilmartians/lefthook) | None, single Go binary | Yes | **Default.** Polyglot repositories, because a Go or Python developer does not need Node installed to commit |
| [pre-commit](https://pre-commit.com) | Python | Yes | The largest catalogue of ready made hooks, and it isolates each hook's runtime |
| [husky](https://typicode.github.io/husky/) + [lint-staged](https://github.com/lint-staged/lint-staged) | Node | No, sequential by default | Pure JavaScript repositories, the most widely documented setup |
| Raw `.git/hooks` | None | No | A solo repository. They are per clone and are not shared, so they are a suggestion rather than a policy |

Recommendation: **lefthook** for anything with more than one language, **pre-commit** for Python centred repositories, **husky plus lint-staged** for pure JavaScript. Whichever you pick, the hooks must be installed by a command in the repository, or half the team will not have them.

Two rules that decide whether this works:

1. **Keep tier 1 under 90 seconds.** Past that, people reach for the escape hatch, and a hook that gets bypassed saves nothing.
2. **Keep tier 1 and tier 2 running the same commands.** The moment they diverge, the hook stops predicting CI.

Templates for both hooks are in [`templates/actions-frugal-ci/git-hooks/`](../templates/actions-frugal-ci/TEMPLATE_README.md). Both refuse to run if a placeholder was left unsubstituted, because a hook that silently checks nothing is worse than no hook.

## The check script

[`scripts/actions-budget.mjs`](../scripts/actions-budget.mjs) reads `.github/workflows/*.yml` from disk and reports what a push actually costs.

```bash
node scripts/actions-budget.mjs .                      # human readable
node scripts/actions-budget.mjs . --json               # machine readable
node scripts/actions-budget.mjs . --plan team          # compare against a different allowance
node scripts/actions-budget.mjs . --fail-on warn       # non-zero exit, for a hook or a CI gate
node scripts/actions-budget.mjs . --live               # add repository visibility and billing usage via gh
```

It reports the jobs a pull request update and a merge each start, with the matrix expanded, local reusable workflows followed, and jobs whose `if:` cannot fire for that event dropped. It converts everything to Linux-equivalent minutes and USD, and projects a month against the plan allowance. It flags workflows with no `paths` filter, no `concurrency`, a non-Linux runner, a `push` and `pull_request` double run, no `timeout-minutes`, a self-hosted runner, and the per job rounding tax. Cron schedules are expanded exactly.

Design decisions worth knowing:

- **Offline by default.** No network access unless you pass `--live`.
- **Two columns, not one.** *Floor* is the job count times the one minute round-up, which is billed no matter what. *Estimate* applies a duration assumption you can set with `--minutes-per-job`. Only the floor is assumption free.
- **Rates live in [`scripts/actions-budget.rates.json`](../scripts/actions-budget.rates.json)**, not in the code, so a price change is a config edit. Every entry is reachable by the classifier, so there are no unused knobs.
- **Unknown means unknown.** A runner label the classifier does not recognise is priced as `unknown` and reported, never silently priced as Linux. A workflow it cannot parse is an `error` finding, never zero jobs.
- **Every figure is an upper bound.** A job with an `if:` the tool cannot decide, such as a label check, is counted at full cost and reported separately.
- **`--live` degrades with a stated reason.** GitHub retired the per-product Actions billing endpoint, which has returned zeros since 27 March 2025, and the replacement usage API is scoped to organisation and enterprise administrators. For a personal account there is often no readable live quota, and the script says so rather than printing a plausible zero.

The parser covers the subset of YAML that workflow files use. Anchors, aliases, and multi-document files are reported as errors rather than guessed at.

Wire it into tier 1:

```bash
node scripts/actions-budget.mjs . --fail-on warn
```

## What I could not verify

Stated plainly, because the rest of this document is only as good as its weakest claim.

1. **How the included minutes allowance is drawn down for non-Linux runners after the January 2026 repricing.** No current documentation sentence states it. Both plausible readings agree macOS is about 10x, so the guidance is unaffected, but the exact mechanism is unconfirmed.
2. **Whether the self-hosted runner charge returns, and at what rate.** GitHub said it is re-evaluating and gave no date.
3. **That `on: push` (unfiltered) plus `on: pull_request` produces two runs for a same repository branch.** This follows from the documented behaviour of each trigger and is universally observed, but I found no single documentation sentence stating it. The recommendation to filter push to the default branch is safe regardless.
4. **Live per repository minute attribution.** The `/actions/runs/{id}/timing` endpoint is marked as closing down, and the legacy billing endpoint returns zeros. I could not find a reliable current API for a personal account, which is why the script is offline first.

Judgment calls, not facts, flagged as such:

- The tier boundaries, and the 90 second pre-push budget. These come from what people tolerate before bypassing a hook, not from measurement.
- The default assumptions in the rate card: 2 minutes per job, 10 pushes a day, 1 merge a day. They are visible and overridable precisely because they are guesses about your repository.
- "Weekly rather than nightly" for scheduled suites. Right for a repository that merges a few times a week, wrong for one that merges hourly.
- Recommending lefthook over pre-commit as the default. Both are good. lefthook wins on not needing a language runtime, which matters more in mixed repositories than the size of pre-commit's hook catalogue.

## Sources

Primary, GitHub documentation and changelogs:

- [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
- [Actions runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing)
- [Billing and usage concepts](https://docs.github.com/en/actions/concepts/billing-and-usage)
- [GitHub pricing](https://github.com/pricing)
- [Usage limits](https://docs.github.com/en/actions/reference/limits)
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Control workflow concurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
- [Skip workflow runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs)
- [Dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)
- [Troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks)
- [Adding self-hosted runners](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/add-runners)
- [Managing access to self-hosted runners using groups](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access)
- [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [REST API endpoints for billing usage](https://docs.github.com/en/rest/billing/usage)
- [Update to GitHub Actions pricing (changelog, 16 December 2025)](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)
- [Pricing changes for GitHub Actions](https://github.com/resources/insights/2026-pricing-changes-for-github-actions)
- [Updates to GitHub Actions pricing (community discussion 182186)](https://github.com/orgs/community/discussions/182186)
- [arm64 hosted runners for public repositories are now generally available (7 August 2025)](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/)
- [GitHub Actions cache size can now exceed 10 GB per repository (20 November 2025)](https://github.blog/changelog/2025-11-20-github-actions-cache-size-can-now-exceed-10-gb-per-repository/)
- [Managing a merge queue](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)

Tools:

- [nektos/act](https://github.com/nektos/act) and its [unsupported features list](https://nektosact.com/not_supported.html)
- [lefthook](https://github.com/evilmartians/lefthook)
- [pre-commit](https://pre-commit.com)
- [husky](https://typicode.github.io/husky/) and [lint-staged](https://github.com/lint-staged/lint-staged)

Secondary, used for context and cross-checking rather than as authority:

- [GitHub bends to criticism and delays paid self-hosting of runners (Techzine)](https://www.techzine.eu/news/devops/137396/github-bends-to-criticism-and-delays-paid-self-hosting-of-runners/)
- [Understanding GitHub Actions runner costs in 2026 (StackTrack)](https://stacktrack.com/posts/understanding-github-actions-runner-costs-in-2026/)
- [Cut your GitHub Actions CI bill (Mergify)](https://mergify.com/blog/cut-your-github-actions-ci-bill)
