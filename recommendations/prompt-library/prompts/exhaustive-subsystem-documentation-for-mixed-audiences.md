---
title: Exhaustive subsystem documentation for mixed audiences
scenarios: docs,architecture,handover
tags: documentation,diagrams,verifiable,non-technical
source: claude-code
session:
date: 2026-07-17
---

# Exhaustive subsystem documentation for mixed audiences

> Use when a subsystem turned out to be much harder than expected and the knowledge is spread across commits, chat history and one person's head.

## Original

```text
整理 <subsystem> 的所有内容并生成完整的文档到 <docs-repo>，如果已有则更新，其他相关文档都可整理在一起。要求技术细节足够详细，但大面上如图表解释等，非技术人员（如数据分析人员）也能看懂；注意使用自然语言表达，去除 AI 味。

文档包括但不限于以下内容：所有之前遇到的问题、如何修复、以前的设计是什么样的、有什么问题；有哪些专用的相关代码及完整链接；有哪些相关的数据库和数据属性，这些库和属性是什么样的、举例说明；有哪些已有的 <subsystem> 数据，如后端本地副本，以及它们是何时、通过什么方式获取的；新的整个 <subsystem> 系统（如果缓存和持久化方案都存在则都写）的 mermaid 架构图、数据流图、存储方案图 / 位置 / 缓存等所有有用的图；存储格式说明（举例）；名称解释；哪些代码 / 数据库内容被使用以及是如何使用的（在图表中给出正确的位置）；整个流程是否可以自动、或者自动 + 手动完成（不依靠 AI agent），如果可以给出完整流程，如果不行说明哪些地方需要专门处理；当前 <entities> 按照使用哪种方式获取的详细分类列表和统计图表，各种方式的准确度，哪些需要特别关注或人工验证；真的处理不了的 <entities> 记录下来且说明是怎么回事以及如何修复；<upstream> 限流是怎么回事及如何破解；如果新的 <entities>（之后的几千个）加入后该流程是否可以扩展过去；可能的优化方向；剩余任务（突出这一点）包括脏数据等；外部源变动应对方案有何问题及可能的优化方向；如何连接 <downstream> 的方案规划；调研其他类似工具功能的实现方案；以及其他有用的内容。

所有内容不要猜测，要可验证，各项里说明数据等人员如何验证（例如测试人员可以确认某个 <entity> 是否是持久化的），如果实在无法验证则说明。这是一个非常有意思的例子：最开始我以为 <task> 是一件非常容易的事情，但是后来发现有很多工程和现实问题。这也是未来其他自动化获取可能遇到的问题。
```

## Optimized

```text
Write the complete documentation for <subsystem> into <docs-location>, updating what already exists
and merging scattered related pages rather than adding another one.

Audience: the technical detail must be full enough to work from, but the overview, and every diagram
caption, must be readable by a non-engineer on the team. Write plain sentences.

Cover at least:
- History: what the earlier design was, what went wrong with it, and how each problem was fixed.
- Code: which modules implement this, with a link to each.
- Data: which tables and fields are involved, with a concrete example row.
- Existing artifacts: what data we already hold, when it was acquired, and by what route.
- Diagrams (mermaid): architecture, data flow, and storage/caching layout. If both a cache and a
  persistence path exist, document both.
- Storage format, with an example, and a glossary for every term of art.
- Whether the pipeline can run automatically, or automatically plus a manual step, WITHOUT an agent
  in the loop. If yes, give the runbook. If no, name the steps that block it.
- A breakdown of how each <entity> was actually acquired, per method, with accuracy per method, and
  which ones need human verification.
- The items that could not be handled at all, each with the reason and the proposed fix.
- Upstream rate limits: what they are and how we work within them.
- Whether the approach scales to <N times more entities>.
- Remaining work, called out prominently, including known dirty data.
- What happens when the external source changes, and where that plan is weak.
- How this connects to <downstream system>.
- How comparable tools solve the same problem.

Rules: do not guess. Every claim must be verifiable, and each section must say HOW a
non-engineer verifies it. Where something genuinely cannot be verified, say so explicitly.
```

## When to use

Use when a subsystem turned out to be much harder than expected and the knowledge is spread across
commits, chat history and one person's head. The framing that makes it work is "not just the design,
but the history of what failed" — that is what makes the document worth more than reading the code.

- Handing a subsystem to teammates, or to your future self after a long gap.
- Non-engineers need to reason about the same system, so numbers and diagrams must be legible to them.
- You need a written scaling verdict before committing to a much larger dataset.

## When NOT to use

Skip it for a subsystem that is still moving. Documentation this exhaustive is expensive, and rewriting
it after the next design change wastes the effort. Wait until the shape is stable.

Skip the per-entity breakdown when the entity count is small enough to read directly.

Do not use it as a substitute for a code walkthrough on something simple. If the module fits on a
screen and does what its name says, this produces bulk rather than clarity.
