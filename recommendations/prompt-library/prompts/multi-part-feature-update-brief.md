---
title: Multi-part feature update brief
scenarios: feature-spec,planning,agent-tooling
tags: brief,batch,acceptance,autorun
source: claude-code
session:
date: 2026-07-18
---

# Multi-part feature update brief

> Use when you have accumulated several unrelated changes for one project and want them handled in a single autonomous run rather than five separate conversations.

## Original

```text
对 <tool> 做以下优化：

1. 随着模型和 agent 能力的不断提升，<tool> 里写的这些内容有时反而会变成负面约束。加一个全局的、最优先的要求：对于所有功能，不限 skills/插件/hooks，模型和 agent 应该先判断当前的工具是否有必要用、会不会造成反面约束。有必要则用；没必要则使用 agent 和模型的原生能力。如果原生能力强过功能约束，则结合已有的自我优化功能，把新的能力和流程融入并更新原始功能，否则回退到原始功能。

2. 对 <session-A> 和 <session-B> 两个 session 的 jsonl，用程序化方法整理出本月以来用户所有的输入提示词，整理为两个文件，path 发给我。然后从这两个文件中整理出和生成文档相关的所有要求，优化整理成一个子功能。注意这个功能指的是我的偏好；实际写文档时文档类型不同、内容不同，可进一步优化，并且应该在需要的时候根据实际写作实时优化这个子功能。

3. 对 autorun 功能加一个要求：默认尽量自动解决所有问题；没有其他方案、一定需要用户批准的，全部压到最后询问，且不要堵塞其他内容。autorun 的执行形式应该是长时间无打扰自动运行，并且自动纠错、解决遇到的问题，直到所有任务彻底完成。

4. 当前 agent 有一个问题：子任务超多（例如十几个）时，执行时间长了以后会偏移或忘记，执行过程中补充的提示词和要求往往会丢，分配给子代理时任务细节可能不全。请做一个功能专门处理这个问题，针对不同的 agent 和模型给出各自最优的方案，且可以跟着 agent 和模型的进化而进化。要求实时给出一个任务文档（一轮任务合在一起），agent 和人类都可以读，agent 运行时参考这个文档，所有已有任务都必须完成、全部 check 才算结束，中途补充则插入这个文档。请把这个功能设计成硬执行（hooks、代码或其他方案），而不是简单靠提示词约束。

5. 之前提到过的要求，请确认已经设计、部署并测试：[...]

以上内容完成后全部 push PR 且部署给本机所有 agents 和 sessions。此外 [...] 这些功能我好像都没有遇到过执行，请确认它们都实际存在且部署了，并且告诉我每一项功能具体如何执行和测试。请在仓库中写一个专门的用户使用文档（可以同时整理已存在的文档）。autorun
```

## Optimized

```text
Apply the following updates to <tool>. Treat every numbered item as a separate deliverable
and report on each one individually.

1. <change> — <why it is needed, in one or two sentences>. <the behaviour you want, including the
   fallback when the new behaviour does not apply>.
2. <change> — <why>. <behaviour>. Note this encodes MY preference, so leave room to refine it as
   real usage shows what is missing.
3. <change> — <why>. <behaviour>.
4. <problem you keep hitting, described as a symptom> — design a feature that addresses it.
   Give the best variant per agent/model rather than one lowest common denominator, and make it
   survive future model upgrades. Implement it as a hard mechanism (hook, script, generated file),
   NOT as prompt wording that a long run can drift away from.
5. <item from an earlier round> — confirm it is designed, deployed and tested; if it is not, say so
   rather than assuming.

Acceptance for the whole batch:
- Every item lands on a branch with its own commit and an opened PR. Do not merge.
- For each item, tell me how to run and test it by hand.
- List anything you could NOT verify and why, instead of reporting it as done.
- Write or update a user-facing guide covering the new behaviour, folding in existing docs rather
  than adding a parallel one.
```

## When to use

Use when you have accumulated several unrelated changes for one project and want them handled in
a single autonomous run rather than five separate conversations.

- The batch is 3 to 8 items that share a codebase but not a call path.
- You want each item's rationale recorded, so the agent can judge trade-offs instead of pattern-matching.
- You want an explicit "confirm this earlier item actually shipped" slot — that is the item that most
  often catches silent regressions.

## When NOT to use

Skip it when the items depend on each other in sequence. A brief like this invites parallel work,
and an agent that reorders dependent steps will produce a half-migrated repo.

Also skip it when you have not yet decided WHY a change is wanted. Item 1 above works because it
carries its own reasoning; an item that is only "make X better" produces a guess.

Do not use it for anything irreversible (deleting data, force-pushing, deploying to production) —
the batch framing pushes toward autonomy, which is the wrong mode for one-way doors.
