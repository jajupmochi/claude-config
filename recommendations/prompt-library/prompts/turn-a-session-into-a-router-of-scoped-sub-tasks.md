---
title: Turn a session into a router of scoped sub-tasks
scenarios: orchestration,context,planning
tags: context-window,sub-agents,routing,long-running
source: claude-code
session:
date: 2026-06-23
---

# Turn a session into a router of scoped sub-tasks

> Use at the start of a long-running session that will span many related but separable pieces of work, when you can already feel the context filling up.

## Original

```text
从现在开始，你将被用于专门做 <domain> 的工作。请整理前面我们所做过的各项 <artifacts>。

然后从现在开始，对于所有的任务，请把它们分门别类地放入不同的 <domain> 子任务当中，而不要一次性地把所有的上下文全部都注入到本 session 里。注意这些子任务的内容要是我可以看到的，并且主 session 也是可以访问这些内容的，如果有需要的话。

当有新的任务或者提示词到来的时候，请先分析它是否属于一个已有的子任务并报告；如果没有的话，则新建一个子任务。注意这些子任务的所在目录可能也是不同的。

请将这些作为本 session 的基本设置，随后做完以后给我一个总结。
```

## Optimized

```text
From now on this session is dedicated to <domain>. Start by taking inventory of the <artifacts> we
have already produced in this area.

Then change how you handle work. Route every incoming task into a scoped sub-task rather than pulling
all of its context into this session. The rules:

- Each sub-task keeps its own working files, in its own directory, in a location I can open and read.
- The main session can reach into a sub-task's output when it needs to, but does not carry that
  content by default.
- When a new request arrives, first say which existing sub-task it belongs to and why. Only create a
  new sub-task when it fits none of them, and tell me when you do.
- Sub-tasks may live under different directories. Do not force them into one tree.

Treat this as the standing setup for the session. Confirm with a summary of the sub-tasks you
created and what each one owns.
```

## When to use

Use at the start of a long-running session that will span many related but separable pieces of work,
when you can already feel the context filling up.

- A multi-week effort where a single conversation would otherwise accumulate everything.
- Work that naturally splits by artifact, so each sub-task has a clear owner.
- When you want to see and edit the intermediate state yourself, which the "files I can open"
  requirement gives you.

## When NOT to use

Do not use it for a single focused task. Routing overhead and an extra layer of indirection buy
nothing when there is one thing to do.

Do not use it when the sub-tasks genuinely share state. Forcing separation on tightly coupled work
means the same facts get re-derived, inconsistently, in several places.

Skip it if your tool cannot actually give sub-tasks separate context. Without that, this is just
renaming, and the context still fills up.
