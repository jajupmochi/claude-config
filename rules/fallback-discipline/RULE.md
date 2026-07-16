---
name: fallback-discipline
description: A fallback / pass / swallowed exception / broad except / default-substitution is judged by the SCENARIO it runs in. Deployment/production — allowed and often required to prevent a user-facing crash, but it MUST record enough detail to diagnose and fix later (trigger, input, why the primary failed, what the fallback did). Test/development — presumed guilty; if it could hide any bug it must be fixed on the spot OR raised loudly, never silently passed. The dividing question — "if this fallback fires, does someone find out?"
scope: personal
rationale: A silent fallback is either a safety net or a hidden failure, and which one depends entirely on whether firing it is observable. In production an uncaught error is a user-facing crash, so a logged fallback is correct. In a test a swallowed failure turns red into green and is worse than the crash it hid. The same construct is right in one scenario and wrong in the other; the rule is the discriminator.
---

# fallback-discipline

> A fallback is judged by the scenario. Deploy allows it **but must log**; test/dev must **not hide** — fix or raise.

## Master TOC

- [Rule](#rule)
- [Deployment / production](#deployment--production)
- [Test / development](#test--development)
- [The dividing question](#the-dividing-question)
- [Relation to other rules](#relation-to-other-rules)

## Rule

Treat every `pass`, swallowed exception, broad `except`, or default-substitution as scenario-dependent: allowed
(with logging) at runtime, presumed guilty in test/dev.

## Deployment / production

A fallback is **allowed and often REQUIRED** to prevent a user-facing crash (geo-blocked LLM → alternate provider;
missing field → empty state; timeout → cached value). **But it MUST record, at the moment it fires, enough detail
to diagnose + fix + optimize later**: the trigger, the input/context, why the primary failed, and what the fallback
did — a structured error-log entry / event, not just a swallow. *A silent production fallback that nothing logs is
a hidden failure that never gets fixed.*

## Test / development

A fallback (or `pass`, or swallowed exception) is **presumed guilty**. If it could hide ANY bug, edge case, or
wrong value, it must be **fixed on the spot OR surfaced/raised loudly** — never allowed to silently pass. A test
that goes green because a fallback masked the real failure is worse than a red one. When in doubt in test/dev:
**raise, don't fall back.**

## The dividing question

> "If this fallback fires, does someone find out?"

Deploy → yes, via a detailed log. Test/dev → yes, via a loud failure (or the fallback is removed). If the answer is
"no one finds out," it is wrong in both.

## Relation to other rules

- `root-cause-before-fix` — a fallback that hides a regression is the wrong layer.
- `always-on-verification` / `code-verifier` — catch swallowed failures and fake-green before a "it works" claim.
