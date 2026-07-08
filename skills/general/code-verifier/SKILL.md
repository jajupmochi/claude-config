---
name: code-verifier
description: Use BEFORE claiming any code/test/script runs successfully. Detects FAKE-RUN patterns (hardcoded results, assert True, mocks-only tests, swallowed exceptions, fabricated numbers, dead-code short-circuits). Apply automatically whenever about to claim "test passes", "code works", "results show X", "training converges", or commit/push. Complements superpowers:verification-before-completion (which enforces real-run discipline) by auditing whether the run itself is genuine.
---

# /code-verifier

Audit the GENUINENESS of evidence — not just that a command ran.

## Master TOC

- [Core principle](#core-principle)
- [The Three-Layer Gate](#the-three-layer-gate)
- [Fake-Run Patterns](#fake-run-patterns)
  - [A. Tests that pass without testing](#a-tests-that-pass-without-testing)
  - [B. Scripts that fabricate results](#b-scripts-that-fabricate-results)
  - [C. Pipelines that short-circuit](#c-pipelines-that-short-circuit)
  - [D. ML-research specific](#d-ml-research-specific)
- [When to invoke](#when-to-invoke)
- [Output format when fake pattern found](#output-format-when-fake-pattern-found)
- [Anti-rationalisation](#anti-rationalisation)
- [Companion](#companion)

## Core principle

**"Ran a command" ≠ "verified the work."** A test that always passes (because it asserts `True`) proves nothing. A script that prints `mAP = 0.85` from a hardcoded literal proves nothing. A pipeline that swallows exceptions silently and returns a default proves nothing.

This skill audits the GENUINENESS of evidence — not just that a command ran.

## The Three-Layer Gate

Before any completion claim involving code / tests / results, run all three layers in order:

1. **Layer 1 — Did it really run?** Defer to `superpowers:verification-before-completion`. Run the exact command in this turn; read full output; check exit code. Skip if already cleared in this turn.
2. **Layer 2 — Is the run genuine?** Audit the artifact for the FAKE-RUN patterns below. If any match, the run is NOT genuine and the claim is unsupported until you fix and re-run.
3. **Layer 3 — Does the run exercise the claim?** Even a real run can fail to exercise the claim — e.g. test imports the wrong module, runs with `pytest -k other`. Check that the artifact's scope matches the claim.

## Fake-Run Patterns

### A. Tests that pass without testing

| Pattern | What it looks like | Why fake |
|---|---|---|
| `assert True` / `assert 1 == 1` | Tautological | Passes regardless of code |
| Tests with no assert/expect at all | Just function body | Passes if no exception, not if behavior correct |
| `try: ... except: pass` then assert succeeds | Hides real failures | Real exceptions go silent |
| Mocking the function under test | `mock.patch('module.fn_under_test')` | Tests the mock, not the function |
| Skipped tests counted as passing | `pytest.skip()` everywhere | 0 failures but 0 verifications |
| Hardcoded fixture matching hardcoded output | Fixture pre-stores expected, fn returns same | No real computation |

**Detection commands**:

```bash
# Tautological asserts
grep -rE "assert\s+(True|1\s*==\s*1)" tests/ src/ 2>/dev/null

# Tests with zero assertions
grep -rL "assert\|expect\|self\.assert" tests/ 2>/dev/null

# Bare-except in tests
grep -rE "except\s*:\s*pass|except\s+Exception:\s*pass" tests/ 2>/dev/null

# Skipped tests
grep -rE "@pytest\.mark\.skip|pytest\.skip\(\)" tests/ 2>/dev/null

# Mocking the SUT
grep -rE "mock\.patch.*$(basename module_under_test)" tests/ 2>/dev/null
```

### B. Scripts that fabricate results

| Pattern | Why fake |
|---|---|
| Hardcoded numeric output (`print(f"mAP = {0.85:.2f}")`) | Literal, not computed |
| Default fallback (`result = compute() or 0.85`) | Falls back to plausible number |
| Random numbers as results (`result = np.random.uniform(0.7, 0.9)`) | No deterministic computation |
| Old cached values read without re-run | Could be stale |
| `if DEBUG: result = 0.85` enabled | Debug path active in prod |

**Detection commands**:

```bash
# Suspicious literal numbers near metric prints
grep -rE "(mAP|acc|score|loss|recall|precision)\s*[=:]\s*[0-9.]" outputs/ scripts/ 2>/dev/null | grep -vE "for|while|range|len|shape|return"

# Or-fallback to numeric literals
grep -rE "= [^#]*\(\)\s*or\s+[0-9.]+" src/ scripts/ 2>/dev/null

# np.random in eval scripts (excluding seeded)
grep -rE "np\.random|torch\.rand|random\." scripts/ 2>/dev/null | grep -viE "seed|generator"
```

### C. Pipelines that short-circuit

| Pattern | Why fake |
|---|---|
| Early return with stub (`return {"ok": True}  # TODO`) | No real work |
| Swallowed exceptions (`except: return default`) | Failures invisible |
| `# noqa` / `# pragma: no cover` over real logic | Hides skipped paths |
| `time.sleep + return` | Looks like work |
| `if False:` / `if 0:` blocks around real code | Real path never runs |

**Detection commands**:

```bash
# TODO/stub patterns near returns
grep -rEB1 "return.*#.*TODO|return.*#.*FIXME|return.*#.*placeholder" src/ scripts/ 2>/dev/null

# Swallowed exceptions
grep -rE "except.*:\s*(pass|return\s+(None|default|\{\}|0))" src/ scripts/ 2>/dev/null

# Disabled blocks
grep -rE "if\s+(False|0):" src/ scripts/ 2>/dev/null

# time.sleep outside tests
grep -rE "time\.sleep" src/ scripts/ --exclude-dir=tests 2>/dev/null
```

### D. ML-research specific

| Pattern | Why fake |
|---|---|
| Training loss not actually backpropping (`opt.zero_grad(); opt.step()` without `.backward()`) | Weights unchanged |
| Eval on training set claimed as test (`eval(train_loader)` while paper says test set) | Inflated numbers |
| Cherry-picked seed (best of N undisclosed) | Selection bias |
| Selected metric only (skip lower-scoring metrics) | Cherry-picking |
| Validation == test pool overlap | Leakage |
| Forward-only run on "test" (doesn't include all batches) | Partial eval |
| Plot data manually drawn (`data = [12, 14, 16, 18]` hardcoded) | Not from real run |

**Detection commands**:

```bash
# Training loop without backward
grep -rEB3 "opt(imizer)?\.step\(\)" src/ scripts/ --include='*.py' | grep -A3 "\.step" | grep -L "\.backward" 2>/dev/null

# Eval on train loader
grep -rE "eval\(.*train_loader|test_metric.*train_data" src/ scripts/ --include='*.py' 2>/dev/null

# Cherry-picked seeds — max() over seed reports
grep -rE "best_(of|seed)|max\(.*seeds" src/ scripts/ --include='*.py' 2>/dev/null

# Hardcoded plot data near plt calls
grep -rB3 -A1 "plt\.(plot|bar|scatter)" scripts/ --include='*.py' 2>/dev/null | grep -E "= \[[0-9.,\s]+\]"

# Val/test split overlap
python3 -c "
import json
for p in ['data/splits.json', 'data_split.json']:
    try:
        d = json.load(open(p))
        v = set(d.get('val', d.get('validation', [])))
        t = set(d.get('test', []))
        print(f'{p}: val∩test = {len(v & t)} of {len(v)} val, {len(t)} test')
    except: pass
"
```

## When to invoke

| Situation | Action |
|---|---|
| About to say "tests pass" | Run all three layers |
| About to commit/push | Run Layer 2 on changed files |
| About to write a paper number | Run Layer 2.B + 2.D on the producing script |
| Inheriting test suite from elsewhere | Run Layer 2.A audit before trusting it |
| Reviewing a PR | Run Layer 2 on the diff |
| Hyperparameter search results | Run Layer 2.D on the seed / selection logic |

## Output format when fake pattern found

```
[FAKE-RUN DETECTED]

Pattern: <category>.<subcategory>
File: path/to/file.py:line
Evidence:
  <exact line(s) showing the pattern>

Why this is fake:
  <one sentence explanation>

Required fix:
  <concrete change>

Re-run command after fix:
  <exact command>

Re-running NOT optional — the previous claim of <X> is NOT supported.
```

## Anti-rationalisation

| Excuse | Reality |
|---|---|
| "It's a stub, will fix later" | Stub = fake-run for THIS run |
| "Just for demo purposes" | Demos still claim things |
| "Tests can be added later" | Then don't claim "tested" |
| "The mock is realistic" | Mock = tests the mock |
| "We trust the cache" | Re-compute or document staleness |
| "Random noise is small" | Then derive deterministically |
| "Just to show the pipeline works" | Then say "pipeline runs", not "results show X" |

## Companion

- `superpowers:verification-before-completion` — Layer 1 (real-run discipline)
- `research-critic` — audits inferential chain ON TOP of authentic artifacts
- `always-on-verification` rule (in this lib) — when to invoke

## Provenance

Originally authored as a user-level always-on gate; consolidated into `agent-harness` for cross-project reuse. Pairs with `research-critic` for full claim-defensibility coverage.
