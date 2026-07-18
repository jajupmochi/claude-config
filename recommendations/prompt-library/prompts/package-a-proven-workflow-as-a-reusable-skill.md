---
title: Package a proven workflow as a reusable skill
scenarios: skill-authoring,agent-tooling,docs
tags: skill,workflow,acceptance,gotchas
source: claude-code
session:
date: 2026-07-10
---

# Package a proven workflow as a reusable skill

> Use right after you have manually proven a workflow that you expect to repeat, while the failures are still fresh.

## Original

```text
# 任务：把 <workflow> 工作流封装成 <harness> 的 skill

## 背景
在另一个 session 里，我们已经把 <integration> 接入并实测跑通了 <workflow>：[...]。现在要把这套流程沉淀成一个可复用的 skill，加进 <harness>，让以后任何 session 遇到 <trigger> 时按它走、并避开我们踩过的坑。

## 权威来源（先读，作为提炼依据；读不到就用本提示词内嵌的内容）
- 教程（最全）：<repo> → <path>
- 可复用脚本：<repo> → <path>
- 研究背景：<repo> → <path>

## 要创建的 skill
- 名称建议：<name>（kebab-case，可自定更贴切的名）
- 位置：放到 <harness> 现有 skill 的同一位置（先确认现有 skill 在哪），并沿用现有 skill 的 SKILL.md 结构与风格。
- 格式：文件开头 YAML frontmatter：name 为 kebab-case，description 是 "Use when..." 触发式。正文用英文。

## skill 正文必须编码的内容（可从上面教程提炼；下面是自包含要点）
1) 前置条件：[...]
2) 接入步骤：[...]
3) 参数怎么取：[...]
4) 主路径的工具调用序列 + 产物落盘位置（该目录必须 gitignore）
5) 备选路径（脚本 / API），凭据从 env 或 gitignored 文件读，绝不硬编码、打印或提交
6) 必须写成醒目 warning 的 N 大坑：[...]
7) 能力对照表：<外部工具的导出选项> ↔ <本流程的工具调用>
8) 推荐落地工作流（写清"不是全自动"）：agent 辅助 + 逐步人工复核

## 结构建议（SKILL.md 章节）
When to use（触发条件）→ Prerequisites → Step 1 → Step 2 → Step 3 → Gotchas（N 条 warning）→ 对照表 → Recommended workflow → References（链接到上面的教程/脚本，不要整段复制教程，引用即可）。

## 验收标准
- SKILL.md frontmatter 合法：name 为 kebab-case，description 是 "Use when..." 触发式且涵盖全部触发场景。
- 上述要点 + N 大坑全部覆盖，坑写成醒目 warning。
- 引用（而非整段复制）教程与脚本路径。
- 若同时要做成 plugin：加一个 slash command；hook 可选，不强求。
- 建好后按 <harness> 的方式注册/使其可被发现，并跑一次自检确认能被发现。

## 硬约束
- 绝不把任何 token/密钥/OAuth code 写进 skill 或提交进仓库。
- 不改 main 分支；skill 若涉及仓库改动放在功能分支。
- 沿用现有 skill 的写法与目录约定，别另立一套。
```

## Optimized

```text
# Task: package the <workflow> workflow as a reusable skill for <harness>

## Background
In an earlier session we got <workflow> working end to end: <one paragraph on what was proven, and
what it produced>. Turn that into a skill so any future session hitting <trigger> follows it and
avoids the traps we already paid for.

## Authoritative sources (read these first; if they are unreachable, use what is inlined below)
- <path to the fullest write-up>
- <path to any reusable script>
- <path to the background research>

## The skill to create
- Suggested name: <kebab-case-name> (pick a better one if you find it).
- Location and format: match the existing skills in <harness> exactly — same directory, same
  frontmatter shape, same section style. Do not invent a second convention.
- `description` must be trigger-shaped ("Use when the user ..."), covering every entry point.

## Content the skill body must encode
1. Prerequisites, including any account tier or permission that gates the workflow.
2. Connection or setup steps, naming who does what (the agent must never enter the user's credentials).
3. How to derive the required identifiers from whatever the user pastes in.
4. The main path: the exact call sequence, and where artifacts land on disk (that directory must be
   gitignored).
5. The fallback path, and where its credential is read from. Never hardcode, print or commit it.
6. Every trap we hit, written as a visible warning with the symptom first, so a future agent
   recognizes it from the error rather than from the cause.
7. A mapping table from the external tool's own vocabulary to our call sequence.
8. The recommended workflow, stated honestly — say plainly which parts are not automatic.

## Structure
When to use, Prerequisites, numbered Steps, Gotchas, mapping table, Recommended workflow, References.
Reference the source documents; do not paste them in.

## Acceptance
- Frontmatter valid, name kebab-case, description trigger-shaped and covering all triggers.
- Every item above present; each trap rendered as a warning.
- Sources referenced by path, not copied.
- Registered the way <harness> registers skills, plus one self-check proving it is discoverable.

## Hard constraints
- No token, key or auth code anywhere in the skill or the commit.
- Work on a feature branch, never on the default branch.
- Follow the existing conventions rather than starting a parallel one.
```

## When to use

Use right after you have manually proven a workflow that you expect to repeat, while the failures are
still fresh. The value of this prompt is the Gotchas section: it converts debugging time you already
spent into something the next session does not have to spend.

- You have at least one worked example and a list of things that went wrong.
- The workflow crosses tools or services, so the failure modes are not obvious from the code.
- You want the result discoverable by an agent, not just filed as a document.

## When NOT to use

Do not use it to write a skill for a workflow you have only read about. Without a real run there are
no gotchas, and a skill whose warnings are speculative is worse than none — it teaches the next agent
to trust invented failure modes.

Skip it for a one-line convenience (an alias, a single command). Packaging overhead exceeds the payoff
below roughly three steps.

Do not use it when the workflow depends on credentials you cannot cleanly externalize. If the honest
skill would have to embed a secret, fix that first.
