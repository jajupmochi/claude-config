---
title: Ship changes with clickable local test links and screenshots
scenarios: frontend,backend,reporting,agent-tooling
tags: api,preview,screenshot,summary-format
source: claude-code
session:
date: 2026-06-27
---

# Ship changes with clickable local test links and screenshots

> Use as a standing instruction for any session that produces API or UI work.

## Original

```text
我现在有很多设计前后端，包括一些 FastAPI 的内容。如果遇到这种内容的话，请做以下处理：首先，对每次新设计出来的 API 做一个列表放到文档里，并且放到总结里，然后这个列表最好能够通过本地的一些测试工具（比如 Storybook 等等）可以直接点击跳转过去进行测试。

第二，如果有一些前后端新的功能设计出来，可以通过前端展示的方式看出区别的话，那就把这个展示部分的链接（这里也是本地的链接）完整地发送出来，让我点击就可以跳过去；这个也同步写到文档和总结里。同时把有更改的部分截图发到总结和文档里，让我能够看到。

第二个问题依然是关于输出的格式可读性：这应该对所有 session 起作用。因为我们现在用的工具会把总结性质的内容和前面调用工具的输出混在一起，所以有时候非常难以看清楚最终总结的部分是从哪里开始的，最好能够加一个什么东西把最终总结的部分很明显地区分出来。另外这个总结的部分文字也比较多、比较杂乱。建议使用一些表格或者嵌套式的 bullet points，非常清晰、重点突出地把总结的内容整理下来，使得一看重点就知道是什么样子，然后相对细节的东西可以不那么突出，但也放在文本里。比如在内容特别复杂的时候，先输出一个简单的目录做总结，然后再写具体的内容；或者在 bullet points 里面把重点内容像标题一样标成加粗，然后具体内容换行再写，这样可能会更清晰。你也可以想想有没有其他方案，直接执行。
```

## Optimized

```text
Whenever you design or change an API or a visible interface, deliver it like this.

For APIs: list every new or changed endpoint as `METHOD /path — purpose`, in both the document and
your summary. Each entry must be a full clickable LOCAL link that opens the endpoint's own test tool
(for example the interactive docs page for that operation), and you must state the command and port
that start the server.

For anything visible: give the full clickable LOCAL URL of the exact route that changed, say how to
start it, and attach a screenshot of the changed surface. For a modification, show before and after.
The links and images go in the document AND in the summary, so I can click through and see the change
without hunting for it.

For the summary itself: mark clearly where the final summary begins, so it does not blend into the
tool output above it. Lead with a one-line takeaway or a short table of contents when the content is
complex. Prefer a table or bold-keyed nested bullets over a wall of prose: the headline point reads
like a heading, the detail sits on the following line. Keep the detail, just stop it from competing
with the point.
```

## When to use

Use as a standing instruction for any session that produces API or UI work. It turns "I added five
endpoints" into something you can actually click and verify in under a minute.

- Full-stack work where the agent cannot show you the running result directly.
- Reviewing an agent's work asynchronously, where a screenshot is faster than rebuilding locally.
- Any project where the summary is the artifact a teammate will read.

## When NOT to use

Skip it for changes with no runtime surface: a refactor, a docs edit, a config change. Demanding a
preview link for those produces invented URLs.

Skip the screenshot requirement for a headless service or a library. There is nothing to see, and the
agent will burn time trying.

Do not fold it into a single request. It is a habit, so it belongs in your standing configuration —
restating it per turn is the failure mode it is meant to remove.
