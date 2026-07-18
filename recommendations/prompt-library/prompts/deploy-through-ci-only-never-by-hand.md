---
title: Deploy through CI only, never by hand
scenarios: deployment,infra,policy
tags: cicd,no-ssh,consistency,standing-rule
source: claude-code
session:
date: 2026-07-17
---

# Deploy through CI only, never by hand

> Use on any project with more than one contributor, or any deployed system where drift between environments is expensive to debug.

## Original

```text
此后除非特别说明，或遇到 rate limit 等限制，严格拒绝任何 ssh 部署，必须走 cicd 并解决其问题，不可绕过 —— 因为可能存在更新带来的 bug，并造成和他人的不一致。ssh 只走可能的一次性前置，并且必须在执行前说明并获批。

请检查当前 actions 挂掉的原因。

另外，建议 cache version 不要写死吧？如果以后再更新呢？是否可以直接换缓存？
```

## Optimized

```text
Standing rule for this project, from now on.

Never deploy over SSH. Every deployment goes through the CI pipeline. When the pipeline fails, fix the
pipeline — do not work around it by hand. The reason is not purity: a manual deploy skips whatever the
pipeline does on update, and leaves the running system inconsistent with what everyone else has.

The only exception is a genuine one-time bootstrap step that cannot exist in CI. State what you intend
to run and why, and wait for my approval before running it. A rate limit or an outage counts as an
exception only if you say so at the time.

Right now: diagnose why the current pipeline run is failing, and fix the cause.

Separately: pinned cache versions look like a future trap. Check whether they can be derived or
invalidated automatically instead of hardcoded.
```

## When to use

Use on any project with more than one contributor, or any deployed system where drift between
environments is expensive to debug.

- After someone has fixed a deploy by hand and the next automated deploy broke.
- When onboarding an agent that has SSH access and will happily take the fast path.
- As a standing rule rather than a per-task instruction, since its value is in never being waived
  quietly.

Stating the reason matters. An agent that knows WHY the shortcut is banned makes better calls at the
edge cases than one following a bare prohibition.

## When NOT to use

Do not apply it to a solo prototype with no CI. The rule presumes a pipeline exists.

Do not apply it during an active incident where the pipeline itself is down and a manual fix restores
service. Declare the exception, do it, then repair the pipeline.

Do not use it as a substitute for permissions. If manual deploys must be impossible, remove the
access — a prompt is a policy, not a control.
