# Template: actions-frugal-ci

> A three tier CI layout that keeps GitHub Actions minutes low. Two local git hook tiers catch failures before a push, one small remote workflow gates the pull request, and the expensive suite runs only behind a label, the default branch, a schedule, or a manual dispatch. Rationale and numbers: [`recommendations/github-actions-frugality.md`](../../recommendations/github-actions-frugality.md).

## What you get

| File | Tier | Purpose |
|---|---|---|
| `git-hooks/pre-commit.template.sh` | 0, local, seconds | Formats staged files, blocks conflict markers and debugger statements |
| `git-hooks/pre-push.template.sh` | 1, local, under 90 s | Runs the same checks as the remote fast tier, then reports the push's Actions cost |
| `lefthook.template.yml` | 0 and 1 | The same two tiers managed in the repository, so a fresh clone gets them |
| `.github/workflows/_checks.reusable.template.yml` | shared | One `workflow_call` job used by both remote tiers, parameterised by `depth` and `runner` |
| `.github/workflows/ci.template.yml` | 2, remote, required | Linux only, concurrency cancelling, documentation only skip via a job gate |
| `.github/workflows/heavy.template.yml` | 3, remote, opt in | Full suite plus the cross-platform matrix, behind a label, the default branch, a weekly cron, or a dispatch |

Drop the two workflow files into `.github/workflows/` and rename them without the `.template` segment. `ci.yml` and `heavy.yml` both call `./.github/workflows/_checks.reusable.yml`, so that name has to match on disk.

## Placeholders to replace

| Placeholder | Replace with | Example |
|---|---|---|
| `<DEFAULT_BRANCH>` | Default branch name | `main` |
| `<NODE_VERSION>` | Runtime version for `setup-node`, or swap the whole step for your language | `22` |
| `<INSTALL_CMD>` | Dependency install | `npm ci` |
| `<LINT_CMD>` | Lint | `npm run lint` |
| `<TYPECHECK_CMD>` | Type check | `npm run typecheck` |
| `<UNIT_TEST_CMD>` | Unit tests | `npm test` |
| `<INTEGRATION_TEST_CMD>` | Integration tests, full depth only | `npm run test:integration` |
| `<E2E_TEST_CMD>` | End to end tests, full depth only | `npm run test:e2e` |
| `<FAST_TIMEOUT_MINUTES>` | Job timeout. Set it to roughly twice the normal duration | `15` |
| `<SOURCE_PATHS>` | Glob for the heavy workflow's paths filter | `src/**` |
| `<SOURCE_PATH_REGEX>` | Regex form of the same thing, for the `changes` gate | `^(src/\|package\.json)` |
| `<HEAVY_LABEL>` | PR label that opts a change into the heavy suite | `full-ci` |
| `<FORMAT_CMD>` | Formatter that rewrites in place | `npx prettier --write` |
| `<LINT_STAGED_CMD>` | Linter that accepts a file list | `npx eslint --fix` |
| `<FORMATTABLE_FILE_REGEX>` / `<FORMATTABLE_GLOB>` | Which files the formatter owns | `\.(ts\|tsx\|js\|json\|md)$` / `*.{ts,tsx,js,json,md}` |
| `<LINTABLE_GLOB>` | Which files the linter owns | `*.{ts,tsx,js}` |
| `<DEBUG_STATEMENT_REGEX>` | Debugger statement to reject | `debugger;\|console\.log(` |

Quick replace, from the project root after copying:

```bash
find .github/workflows git-hooks lefthook.yml -type f -exec sed -i \
  -e "s|<DEFAULT_BRANCH>|main|g" \
  -e "s|<NODE_VERSION>|22|g" \
  -e "s|<INSTALL_CMD>|npm ci|g" \
  -e "s|<LINT_CMD>|npm run lint|g" \
  -e "s|<TYPECHECK_CMD>|npm run typecheck|g" \
  -e "s|<UNIT_TEST_CMD>|npm test|g" \
  -e "s|<INTEGRATION_TEST_CMD>|npm run test:integration|g" \
  -e "s|<E2E_TEST_CMD>|npm run test:e2e|g" \
  -e "s|<FAST_TIMEOUT_MINUTES>|15|g" \
  -e "s|<SOURCE_PATHS>|src/**|g" \
  -e "s|<HEAVY_LABEL>|full-ci|g" \
  {} +
```

Set `<SOURCE_PATH_REGEX>` and the formatter placeholders by hand, since they contain regex metacharacters that `sed` would otherwise interpret.

## Post setup steps

1. **Install the hooks.** `npx lefthook install`, or copy the two scripts into `.git/hooks/` and `chmod +x` them. Raw `.git/hooks` files are per clone and are not shared, which is why lefthook is the default recommendation.
2. **Make `fast checks` a required check**, and nothing else. `heavy.yml` must not be required, because a workflow skipped by a paths filter leaves its check Pending and blocks the merge. GitHub states it plainly: "You should not use path or branch filtering to skip workflow runs if the workflow is required to pass before merging. As an alternative, if a job within a workflow is skipped due to a conditional, it will report its status as Success." ([troubleshooting required status checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/troubleshooting-required-status-checks))
3. **Create the `<HEAVY_LABEL>` label** so reviewers can pull the full suite onto a risky pull request.
4. **Measure before and after.** `node scripts/actions-budget.mjs .` prints the job count, the runner mix, and the projected monthly minutes. Run it once before adopting the template and once after.

## Choices this template makes, and when to reverse them

| Choice | Why | Reverse it when |
|---|---|---|
| One job runs lint, types, and tests in sequence | GitHub rounds every job up to a whole billable minute, so three 20 second jobs bill three minutes and one 60 second job bills one | A step takes more than about two minutes, at which point the wall clock saving from parallelism beats the extra rounded up minute |
| Linux everywhere in tiers 2 and 3 except the `platforms` matrix | macOS bills about 10x and Windows about 1.7x per minute | You ship a macOS or Windows artifact, in which case keep those jobs on the default branch and the schedule rather than on every pull request |
| No paths filter on `ci.yml` | A skipped required check blocks the merge | The workflow is not a required check |
| `cancel-in-progress` only for pull requests | Cancelling a default branch run can abort a publish half way | Nothing on the default branch publishes anything |
| Weekly rather than nightly schedule | A nightly full suite costs about 4x a weekly one and mostly re-tests an unchanged tree | The repository merges daily, where nightly catches drift sooner |
| `fail-fast: true` on the platform matrix | Stops the sibling jobs instead of paying for all of them | You need every platform's result on one run to triage a flaky failure |

## Simpler variant

If a documentation only pull request is rare, delete the `changes` job from `ci.yml` and the `needs`/`if` on `fast`. That removes about 15 lines and one billable minute per pull request, and costs a full fast tier run on documentation changes. The `changes` gate wins once documentation edits are more than roughly one pull request in six.
