# 哲学（Philosophy）

> 这些规则为什么存在。"为什么"是规则能延续的原因——没有它，每个新项目都会重发明一遍，上一个项目的教训传不到下一个。

> **语言：** [English](PHILOSOPHY.md) | 中文

## Master TOC

- [起因](#起因)
- [三个核心张力](#三个核心张力)
- [采纳的约定](#采纳的约定)
- [拒绝的约定](#拒绝的约定)
- [活文档](#活文档)

## 起因

横跨几个项目（`liulian-python`、`swiss-river-network-benchmark`、`AI_Mur4Cast`、`jajupmochi.github.io` 等），同样的 Claude Code 规则一遍又一遍被重新发明：

- "实现前先计划"
- "Python 用 uv + ruff"
- "面向人类的内容做双语"
- "`PostToolUse:Write|Edit` 后自动格式化"
- 指向子文档的 "Authoritative references" 段
- Conventional Commits

每个项目的 CLAUDE.md 都从前一个项目复制粘贴，又略有偏移。新项目继承自最近的项目（最近的项目又继承自更早的）。Bug 在传，改进没传。

这个库就是这次合并。一次蒸馏的成本付一次，每个新项目都受益。

## 三个核心张力

### 1. 速度 vs 控制

Claude 完全自主时最快。但破坏性操作、中途重构、过度积极的 skill 调用都会消耗真实的人工 review 时间。

**解决：** 破坏性 / 不可逆 / 跨文件修改前必须 explicit "go"；常规任务匹配工具时自动触发；开放一条 `tool-proactivity` 规则给用户开放更高自主性。

### 2. 密度 vs 可发现性

5 页的 CLAUDE.md 涵盖一切，但 Claude 不会全部纳入工作记忆。1 页的 CLAUDE.md 全被加载，但漏掉了边角情况。

**解决：** CLAUDE.md 尽量精简——每一行都过"Claude 不写这条会不会出错"的测试。冗长内容放进链接的 rules / skills / `@imports`。`INVENTORY.md` 作为可导航的索引。

### 3. 项目专属 vs 通用

静态主页规则（i18n 一致性、双语文档、视觉验证）不适用于 ML 研究包。通用规则（实现前先计划、中文输出）所有项目都适用。

**解决：** 每条规则有 `scope:` 字段（如 `universal`、`python-research`、`static-site`、`ml-experiment`）。`setup/init-agent-harness` 技能在新项目启动时询问用户适用哪些 scope，只把对应规则写进去。

## 采纳的约定

这些在几乎所有项目里都出现，值得标准化：

- **Conventional Commits** —— `feat:`、`fix:`、`docs:`、`refactor:`、`chore:`。
- **Python 用 uv + ruff** —— 不用 `pip`，不用 `black`。即使 `pyproject.toml` 还留着 `[tool.black]` 段，ruff 也是权威。
- **`pyproject.toml` extras** 管理可选依赖，配 `ImportError` 捕获 + 安装提示。
- 每个 markdown 文件顶部 **Master TOC**。
- 面向人类的 doc 用 **`NAME.md` + `NAME.zh.md`**（每项目按需启用）。
- **`PostToolUse: Write|Edit`** 格式化钩子（Python：ruff；JSON：jq）。
- UI 工作用 **chrome-devtools MCP** 做视觉验证。
- 非平凡任务做 **阶段化规划**。
- **预编辑确认** + explicit "go"。
- CLAUDE.md 顶部放 **Authoritative references** 指向子文档（别重推已经写在别处的内容）。

## 拒绝的约定

这些只在部分项目里出现，太专或太重，不做通用化：

- **Hierarchy IDs（`H1.M2.G3.T4`）** —— 只有 `jajupmochi.github.io` 因为有真实长期 roadmap 才用。多数项目不需要；`git log` + 一个短的 PLAN.md 就够了。
- **`UPDATES.md` 每日日志** —— 短期项目过重。需要时可以从 static-site 模板里拉。
- **Black** —— 统一只用 `ruff format`。`pyproject.toml` 残留的 `[tool.black]` 段是技术债，不是要遵守的配置。
- **项目级 CLAUDE.local.md** —— 只有个人主页需要（求职背景、ML 研究员视角）。多数项目用全局 `~/.claude/CLAUDE.md` 就能覆盖个人偏好。

## 活文档

本文档的更新跟随对应规则的编辑。`RULE.md` 改了 rationale 时，这里同 batch 更新。"采纳"和"拒绝"的清单是经验性的——基于林林项目里实际管用的东西，不是先验的最佳实践。
