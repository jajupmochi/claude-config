---
name: research-critic
description: Use AT EVERY RESEARCH STEP (hypothesis design, experiment setup, result interpretation, conclusion writing) to challenge soundness BEFORE committing the step. Catches confirmation bias, p-hacking, leakage, weak baselines, ungrounded claims, ad-hoc thresholds, survivorship bias. Apply automatically whenever about to write a paper claim, design an ablation, interpret a number, or update a results doc. Pairs with code-verifier (which audits artifact authenticity).
---

# /research-critic

Adversarial review of the inferential chain BEFORE a claim is published.

## Master TOC

- [Core principle](#core-principle)
- [When to invoke](#when-to-invoke)
- [The Six-Question Audit](#the-six-question-audit)
- [Anti-bias checklist](#anti-bias-checklist)
- [Output format when critic flags an issue](#output-format-when-critic-flags-an-issue)
- [Quick check (single line)](#quick-check-single-line)
- [Anti-rationalisation](#anti-rationalisation)
- [Companion](#companion)

## Core principle

A real experiment can still be *interpreted* wrongly. Numbers don't speak for themselves — they require a chain of inference from {data, method, comparison} to {claim}. **Each link is a place to lie to yourself.** This skill challenges each link adversarially before the claim is published.

## When to invoke

Before ANY of:

- Writing a result line in a paper draft / RESULTS.md
- Closing an experiment ticket as "done"
- Adding a number to a table or figure
- Saying "our method beats X" or "our method matches Y"
- Concluding from an ablation
- Committing a "headline" milestone in git
- Sharing results with a collaborator / advisor

## The Six-Question Audit

Run all six. Each `NO` answer is a STOP — fix before claiming.

### Q1. Is the hypothesis falsifiable?

| Sufficient | Insufficient |
|---|---|
| "Method X lifts metric Y by ≥ Z pp over baseline on dataset D, N folds" | "Method X improves Y" (improves how? on what?) |
| "Coverage matches target 1−α within Δ across α∈{...}" | "Calibration works" |

**Red flags**: vague verbs (`improves`, `outperforms`, `works`); no specific magnitude; no specific dataset / metric / comparator.

### Q2. Does the experiment design test the hypothesis?

Check that:

- Independent variable changes ONLY the thing under test
- All other knobs (seed, encoder checkpoint, pool, split, threshold, normalisation) are matched between conditions
- Dependent variable measures what the claim says (mAP vs recall@1 vs precision are different)
- Sample size sufficient for the claimed effect size

**Common breaks**:

- "Method A: 60%, Method B: 65%" but A used 4 folds and B used 1 fold → not comparable
- "Cross-domain transfer X%" but no in-domain baseline at SAME pool size → ambiguous denominator
- "Our method works at scale" tested only on 200 samples
- "Multi-seed × narrow-TTA helps" but no anti-control (variants may anti-compound)

### Q3. Is the comparison fair?

| Fair | Unfair |
|---|---|
| Same pool, same metric, same code path, only the *named* knob differs | Old baseline number from a different setup |
| Both numbers from runs in this commit | One from prior paper, one from new code |
| Statistical test acknowledges variance | "X > Y by 0.1 pp" claimed as a win with σ ≈ 1 pp |

**Anti-pattern: "free improvement" trap.** If method B looks better than A "for free", check whether B was tuned (knob search) while A was the first config tried. Random initialization can give 1-2 pp swings; tuning B but not A is unfair.

### Q4. Could the result be explained by leakage / artifact?

Audit:

- Training set ∩ Test set must be empty (string identity ok; semantic identity not enough — e.g. same writer in train and test still leaks)
- Validation set used to tune hyperparams must be held out from test-set metrics
- Per-class evaluation: are test classes ever seen during training? (Closed-vocab vs open-vocab)
- For ranking metrics: is the ranking model trained on the same query-relevance signal it's evaluated on?
- For cross-domain transfer: truly never exposed to eval domain? (Including via pretrained weights.)

### Q5. Is the conclusion proportional to the evidence?

| Conclusion | Evidence required |
|---|---|
| ✅ "Method X +A pp over Y (N-fold paired test, p<0.05)" | N-fold mean+std, paired test |
| ⚠ "X is the best alignment method" | Tested vs Chamfer & TPS; not vs ICP, RANSAC, all alternatives |
| ❌ "X solves task T" | Single benchmark only |

**Rules of thumb**:

- 1 dataset → "we observe on X"
- 2-3 datasets → "we observe across X, Y, Z"
- 4+ datasets with diverse properties → "generalises" (still hedge: under conditions Z)
- Never: "solves", "best", "universal" without proof of impossibility for alternatives

### Q6. Does the result survive plausible alternative explanations?

For each headline claim, list at least TWO alternative explanations and rule them out:

```
Claim: "Cross-domain transfer is 79.2%"

Alt 1: "Maybe pretrained encoder is doing all the work, not the alignment module"
  Rule out: Run with raw baseline → if comparable, alignment adds nothing
  Status: ✅ raw is 12%, with alignment 13.3% → adds 1.3pp

Alt 2: "Maybe transfer ratio is high because in-domain reference is also poor"
  Rule out: Check absolute in-domain numbers
  Status: ⚠ in-domain is 16.8% → ratio high partly because BOTH are low; reframe

Alt 3: "Maybe noise — single training run"
  Rule out: Multi-seed
  Status: ❌ only 1 seed. Caveat the claim or rerun.
```

If ANY alt is not ruled out, the claim is over-stated.

## Anti-bias checklist

Applies to every result line:

- [ ] Pre-registered prediction? (or at least: designed before seeing data?)
- [ ] All conditions disclosed, not just winners
- [ ] Effect size given, not just "significant"
- [ ] Variance / std reported
- [ ] Random seed disclosure (multi-seed if practical)
- [ ] Baseline strength documented (not a strawman)
- [ ] Code + data available for replication (commit hash, data version)
- [ ] Ablation isolates each contributing component

## Output format when critic flags an issue

```
[RESEARCH CRITIC — FLAG]

Question: Q<N>. <question summary>
Claim under audit:
  "<exact wording from draft / table / commit>"

Issue:
  <which assumption is violated or unverified>

Evidence needed to support claim:
  - <experiment / number / control>
  - <experiment / number / control>

Conservative restatement (if claim cannot be fully supported):
  "<weaker but defensible claim>"

Action:
  [ ] Run additional experiment: <command>
  [ ] OR weaken claim and proceed
```

## Quick check (single line)

Before pasting any number into a paper / RESULTS.md / commit:

> "Can I defend this number against an adversarial reviewer who knows
>  the field, the data, and my code? If not — what's missing?"

If the answer involves wishful thinking ("they probably won't ask", "reviewers usually accept this", "it's standard"), STOP. Fix or weaken.

## Anti-rationalisation

| Excuse | Reality |
|---|---|
| "It's the trend that matters" | Then claim the trend, not the number |
| "Reviewers won't notice" | They will |
| "Standard in the field" | Standard ≠ correct |
| "Just for this draft" | Drafts ossify into papers |
| "It's only 0.1 pp" | Then say "no difference" |
| "Pool size doesn't matter much" | Then test it |
| "Run another seed later" | Run it now or hedge now |

## Companion

- `code-verifier` — audits artifact authenticity (Layer 1-3). Use BEFORE this skill (genuine artifact, then check inferential chain).
- `always-on-verification` rule (in this lib) — when to invoke both.
- The `superpowers:requesting-code-review` skill complements with external review of the code path producing the numbers.

## Provenance

Originally authored as a user-level always-on gate; consolidated into `agent-harness` for cross-project reuse. Pairs with `code-verifier` for full claim-defensibility coverage.
