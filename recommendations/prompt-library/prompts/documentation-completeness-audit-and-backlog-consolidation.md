---
title: Documentation completeness audit and backlog consolidation
scenarios: audit,docs,planning
tags: audit,backlog,plan-hierarchy,status-markers
source: claude-code
session:
date: 2026-04-21
---

# Documentation completeness audit and backlog consolidation

> Use at a natural checkpoint, when several features have landed quickly and you suspect the docs and the backlog have drifted out of sync with the code.

## Original

```text
首先仔细检查：到现在已实现的所有新功能之间，具体新增了哪些功能？请逐一核查这些功能，是否已经按照我们的配置和要求，完整、正确地进行了文档化，尤其是是否针对不同类别的读者分别进行了清晰说明。同时，需要确认：所有需要人工操作的部分，是否已经在文档中进行了详细说明；并且这些内容是否也已在文档中完整体现；以及在总的 README 中，是否清楚地说明了这些内容分别位于何处。

完成上述所有核查之后，请继续：通过阅读当前 session 中剩余的任务，以及历史中记录的待办任务，特别是结合现有文档中所记录的从中长期一直到当前设想的最远阶段的所有历史任务，将所有待办事项完整整理出来，并按照我们的规则生成一个任务列表。如果某些任务有更详细的内容，请按照现有规则进行拆分。完成这些之后，请使用我们当前最新的规则，对整个项目进行一次全面梳理，把所有未按规则执行的部分全部修正为符合规则的形式；对于无法自动执行、或者必须由我手动完成的部分，请详细列出。

此外，请同时维护一个 update 和计划文件。关于 plan 文件，需要在最开始提供一个清晰定义的任务层级标识体系，并在开头给出完整的计划目录，使用多层级的项目符号结构（至少三层：长期目标、当前 session、具体工作）来清晰展示整体规划。同时，在目录和每一条计划项的开头使用简单标识来表示状态，例如 [✓] 表示已完成，[x] 表示已取消等。请充分思考并设计。另外，这些计划还需要适用于 AI agent 的读取与访问，能够兼容其 harness 系统以及 plan / mem 系统。建议最高层级统一使用一个战略层级标识，第二层级使用 Milestone，第三级为 goal 层级，再往下的层级全部重命名为 Task 层级。完成以上内容后，请据此更新相关的 plan 以及其他相关文档。此外，对于其他文档，也需要提供类似 Master Plan 的、带有清晰层级标识的目录结构。这样，每一次更新都会非常清晰明确。update 为一个 md 文件，以天为单位区分，如果一天内有多次重要更新则使用 v1 v2…。以上内容同时写入规则和本项目 docs 的 readme 作为文档要求。
```

## Optimized

```text
Work through this in three passes and report after each.

Pass 1 — documentation audit. Enumerate every feature added so far. For each one, check whether it is
documented completely and correctly under our conventions, and specifically whether each reader group
is addressed separately. Confirm that every step requiring manual human action is written down, and
that the top-level README says where each of these documents lives. Report the gaps as a table before
fixing anything.

Pass 2 — backlog consolidation. Read the remaining work in this session, the recorded to-do history,
and the long-range plans in existing documents. Produce ONE consolidated task list under our task
conventions, splitting any item that carries enough detail to warrant it.

Pass 3 — conformance sweep. Apply the current conventions across the whole project, correcting
anything that predates them. List separately every item that cannot be corrected automatically and
needs me.

Then maintain two living files:
- A PLAN file. Define its level names up front and give a full table of contents at the top, nested at
  least three deep (strategic level, then milestone, then goal, then task). Prefix every entry, in both
  the table of contents and the body, with a status marker such as [✓] done or [x] cancelled. The file
  must be readable by an agent as well as by me, so keep the identifiers stable and machine-greppable.
- An UPDATE file, one section per day, versioned v1, v2 within a day when there is more than one
  substantial update.

Finally, record these documentation requirements in the project's own conventions so the next
session inherits them.
```

## When to use

Use at a natural checkpoint, when several features have landed quickly and you suspect the docs and
the backlog have drifted out of sync with the code.

- Before onboarding anyone, or before a release.
- When to-do items are scattered across chats, commits and half a dozen documents.
- When you want a plan file that both you and an agent can navigate by stable identifier, which is
  what the hierarchy and status markers are for.

## When NOT to use

Do not run it on a project with only a handful of features. Three passes plus a hierarchy scheme is
heavier than the problem.

Do not run it in the same turn as feature work. The conformance sweep touches many files, and mixing
it with a behaviour change makes the diff unreviewable.

Skip pass 3 if your conventions are themselves in flux, or you will rewrite the whole project to a
standard you are about to change.
