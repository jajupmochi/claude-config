# USAGE —— 操作指南

> `agent-harness` 常见使用场景的分步走查。

> **语言：** [English](USAGE.md) | 中文

## Master TOC

- [0. 安装 agent-harness（每台机器一次）](#0-安装-agent-harness每台机器一次)
- [1. 启动新的 Python 研究项目](#1-启动新的-python-研究项目)
- [2. 启动新的静态个人主页](#2-启动新的静态个人主页)
- [3. 把 agent-harness 加到现有项目](#3-把-agent-harness-加到现有项目)
- [4. 为单个项目定制规则](#4-为单个项目定制规则)
- [5. 给库新增 rule / skill / hook](#5-给库新增-rule--skill--hook)
- [6. 更新到最新版](#6-更新到最新版)
- [7. 发布新版本（维护者）](#7-发布新版本维护者)
- [疑难排解](#疑难排解)

## 0. 安装 agent-harness（每台机器一次）

**6 种 Claude Code 方式**选一；Codex 使用下面单独的安装路径。快速对比：

| 方式 | 最适合 | session 启动联网 | 更新机制 |
|---|---|---|---|
| **A) npx** ⭐ 推荐 | 终端一行命令最快 | 不需要 | 再跑一次 `npx ...` |
| **B) `/plugin` 交互** | 在 Claude Code 里浏览安装 | 部分 | `/plugin update` |
| **C) `/plugin install` 直接** | 已知插件名 | 部分 | `/plugin update` |
| **D) 本地 `git clone`** | 完全手动控制 / 离线友好 | 不需要 | `git pull` |
| **E) Raw URL `@imports`** | 完全不装——CLAUDE.md 里直接放 URL | 需要 | 自动（live） |
| **F) 复制粘贴提示词** | 最省心——让 CC 帮你装 | 不需要 | 再跑一次提示词 |

### A) `npx`（推荐）

最快路径，零配置：

```bash
npx github:jajupmochi/agent-harness
```

这会跑 [`bin/install.js`](https://github.com/jajupmochi/agent-harness/blob/main/bin/install.js)：
1. 把库 clone 到 `~/.claude/agent-harness/`
2. 把 `init-agent-harness` 技能软链到 `~/.claude/skills/`，让 `/init-agent-harness` 在任何项目都可用
3. 打印下一步

后续更新：再跑一次 `npx github:jajupmochi/agent-harness`（它会检测已有安装并打印 `git pull` 提示）。

### B) `/plugin` 交互（在 Claude Code 里）

浏览插件 marketplace 并选择 agent-harness：

```
/plugin marketplace add jajupmochi/agent-harness
/plugin
# 浏览并安装 agent-harness
```

安装后 `/init-agent-harness` 在任何项目里可用。

### C) `/plugin install` 直接（在 Claude Code 里）

如果已知插件名：

```
/plugin install jajupmochi/agent-harness
```

（plugin 规范稳定后能用——manifest 已就绪在 [`.claude-plugin/plugin.json`](https://github.com/jajupmochi/agent-harness/blob/main/.claude-plugin/plugin.json)。）

### D) 本地 `git clone`（标准方式）

完全手动控制：

```bash
git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness

# 软链 init 技能让 /init-agent-harness 全局可用：
ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness
```

更新：`cd ~/.claude/agent-harness && git pull`。

### E) Raw URL `@imports`（不装）

什么都不装。项目 `CLAUDE.md` 用 `@import` 直接指向 GitHub raw URL：

```markdown
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/pre-edit-confirmation/snippet.md
```

永远是最新的，但 session 启动需要联网。`/init-agent-harness` 斜杠命令也不会全局可用——需要手动组合 `CLAUDE.md`，不能用 scaffold 技能。

### F) 复制粘贴提示词给 Claude Code

在任何目录打开 Claude Code（不用先装任何东西）。把这段提示词原样粘贴进去，Claude 会帮你执行安装：

> 请帮我从 https://github.com/jajupmochi/agent-harness 安装 agent-harness：
>
> 1. 跑：`git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness`
> 2. 跑：`mkdir -p ~/.claude/skills && ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness`
> 3. 确认完成后告诉我在项目里跑 `/init-agent-harness`。

或英文：

> Please install agent-harness from https://github.com/jajupmochi/agent-harness:
>
> 1. Run: `git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness`
> 2. Run: `mkdir -p ~/.claude/skills && ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness`
> 3. Confirm done and tell me to run `/init-agent-harness` in my project.

这种方式可行，因为 Claude Code 能执行 shell 命令、能读取提示词里的 GitHub URL。

---

### Codex 本地激活

Codex 使用的发现位置和 Claude Code 不同。这个路径不会改动 `~/.claude` 或 Claude 插件安装。

```bash
cd ~/.claude/agent-harness
npm run verify:codex
npm run activate:codex
```

安装脚本会：

1. 把 Codex wrapper skills 软链到 `~/.agents/skills/`。
2. 把本仓库软链到 `~/plugins/agent-harness`。
3. 创建或更新 `~/.agents/plugins/marketplace.json`。

重启 Codex 或开启新 session 后，用 `/skills` 调用 `init-codex-config` 或 `agent-config-adapter`；用 `/plugins` 查看本地插件条目。

如果 Codex CLI 更新报 `Could not find Codex package or platform npm release assets`，运行 `npm run update:codex`。这个 wrapper 会在 latest release 元数据和实际资产短暂不同步时，改用显式 `CODEX_RELEASE` 重试官方安装器。

---

## 1. 启动新的 Python 研究项目

### 场景

新的 ML / 科学计算项目，想沿用 `liulian-python` / `swiss-river-network-benchmark` 的所有约定：uv + ruff + pytest，可选 torch / data / logging extras，mkdocs 文档，ruff 编辑后自动格式化。

### 步骤

```bash
# 1. 建空目录并进入
mkdir my-research-pkg
cd my-research-pkg

# 2. 打开 Claude Code
claude

# 3. 跑安装技能
/init-agent-harness
```

提示时回答：

| 问题 | 选 |
|---|---|
| 项目类型 | Python 研究包 |
| 双语 | 仅英文（如果还会做中文文档则 EN+zh） |
| 终端输出语言 | 中文（或英文） |
| Context 标签 | `always`、`research-pkg`、`docs-site`（不做 UI 就跳过 ui-project；ML 工作才选 ml-research） |
| 消费方式 | 本地 clone（推荐） |
| 个人偏好 | output-brevity、tool-proactivity、no-reread-files |

### 结果

```
my-research-pkg/
├── CLAUDE.md                       ← 模板 + 选定规则组合而成
├── README.md                       ← 模板
├── pyproject.toml                  ← 模板，含 research extras
├── .gitignore                      ← Python + 研究产物忽略
├── .claude/
│   ├── settings.json               ← ruff 编辑后自动格式化钩子
│   ├── settings.local.json         ← 权限白名单（gitignore）
│   ├── skills/
│   │   ├── verify/SKILL.md         ← 项目专属 verify
│   │   ├── long-running-tasks/     ← 来自 agent-harness（symlink）
│   │   ├── privacy-redact/         ← 来自 agent-harness（symlink）
│   │   └── verify-visual/          ← 来自 agent-harness（symlink）
└── （你的代码）
```

### 安装后命令

替换占位符、装依赖、验证：

```bash
# 替换占位符
find . -type f \( -name "*.md" -o -name "*.toml" \) -exec sed -i \
  -e "s/<PROJECT_NAME>/my-research-pkg/g" \
  -e "s/<PACKAGE_NAME>/my_research_pkg/g" \
  -e "s/<DESCRIPTION>/我的 ML 研究项目/g" \
  -e "s/<AUTHOR_NAME>/你的名字/g" \
  -e "s/<AUTHOR_EMAIL>/you@example.com/g" \
  {} +

# uv 启动
uv sync --python 3.12
uv pip install -e ".[dev]"

# 初始化 git
git init -b main
git add .
git commit -m "chore: initialize from agent-harness research-package-py template"

# 验证
/verify
```

---

## 2. 启动新的静态个人主页

### 场景

做个人学术主页 / 作品集（HTML / CSS / JS，不带构建步骤），想要双语文档、JSON i18n、GitHub Pages 部署、chrome-devtools MCP 视觉验证。

### 步骤

```bash
# 1. 建项目（典型用 <你的handle>.github.io 名字给 GitHub Pages）
mkdir myhandle.github.io
cd myhandle.github.io

# 2. 打开 Claude Code 跑 scaffold
claude
/init-agent-harness
```

回答：

| 问题 | 选 |
|---|---|
| 项目类型 | 静态个人/作品集主页（HTML/CSS/JS） |
| 双语 | EN+zh（推荐，给国际访问者） |
| 终端输出语言 | 中文（你的偏好） |
| Context 标签 | `always`、`static-site`、`web-perf`、`ui-project`（如果用动画库） |
| 消费方式 | 本地 clone |
| 个人偏好 | 三个全选（output-brevity、tool-proactivity、no-reread-files） |

### 结果

```
myhandle.github.io/
├── CLAUDE.md / CLAUDE.zh.md（如果双语）
├── README.md / README.zh.md
├── index.html                        ← 模板，i18n 支持
├── locales/
│   ├── en.json                       ← 模板
│   └── zh.json                       ← 模板（与 en 键对齐）
├── .gitignore
└── .claude/
    ├── settings.json                 ← jq-validate-json 钩子
    ├── skills/
    │   ├── preview/SKILL.md          ← python3 -m http.server
    │   ├── verify-visual/SKILL.md    ← chrome-devtools MCP
    │   ├── i18n-sync/SKILL.md        ← locale 一致性检查
    │   ├── long-running-tasks/       ← 来自 agent-harness
    │   └── privacy-redact/           ← 来自 agent-harness
```

### 安装后命令

```bash
# 替换占位符
find . -type f \( -name "*.html" -o -name "*.json" -o -name "*.md" \) -exec sed -i \
  -e "s/<SITE_NAME>/我的主页/g" \
  -e "s/<DESCRIPTION>/我的描述/g" \
  -e "s/<AUTHOR_NAME>/你的名字/g" \
  -e "s/<AUTHOR_GITHUB>/myhandle/g" \
  -e "s|<DEPLOY_URL>|https://myhandle.github.io|g" \
  {} +

# 跑 dev server
/preview
# 自动打开 http://localhost:8000/index.html

# 编辑后视觉验证
/verify-visual

# 初始化 git + 推到 GitHub
git init -b main
git add .
git commit -m "chore: initialize from agent-harness personal-cite-static template"
gh repo create myhandle/myhandle.github.io --public --source=. --push
```

---

## 3. 把 agent-harness 加到现有项目

### 场景

已有项目，想给它加上 `agent-harness` 约定但不覆盖现有代码。

### 步骤

```bash
cd my-existing-project
claude
/init-agent-harness
```

技能检测到现有项目（有 manifest / 有 CLAUDE.md / 有 .git）：

- **没有 CLAUDE.md**：技能新建一个，含 `@import` 行。
- **有 CLAUDE.md**：技能问：merge / 先备份 / 跳过 CLAUDE.md 只做 `.claude/`。默认 **merge**（增量——加新规则，不动现有规则）。

Context 标签按现有项目性质选。技能不会复制模板脚手架（项目已有源码）。

### 加进什么

- `CLAUDE.md`（新建或追加）：所选规则的 `@import` 行
- `.claude/settings.json`：所选 context 的钩子
- `.claude/settings.local.json`：权限白名单
- `.claude/skills/`：相关通用技能（long-running-tasks、privacy-redact、verify-visual）

### 不动什么

- 你的源码
- 现有 `pyproject.toml` / `package.json`
- 现有 `.gitignore`（仅追加 agent-harness 相关条目）
- 现有 `README.md`

---

## 4. 为单个项目定制规则

### 场景

你普遍喜欢 `output-brevity`，但**这个项目**希望 Claude 详细一点（比如新人 onboarding 需要更多上下文）。

### 方案 A：在这个项目里禁用此规则

编辑项目 `CLAUDE.md`，把对应 `@import` 注释掉：

```markdown
<!-- @~/.claude/agent-harness/rules/output-brevity/snippet.md -->
```

完成。其他规则仍生效。

### 方案 B：用项目级备注覆盖

`CLAUDE.md` 的 imports 之下：

```markdown
## 项目特定覆盖

覆盖 `output-brevity`：本项目**需要**末尾汇总，因为新人正在熟悉代码。两段话以内。
```

项目级文本写在 imported snippet 之后，会胜出。

### 方案 C：全局修正（影响所有消费方）

如果规则本身错了（不只是项目特殊），向 `agent-harness` 提 PR 修正。见 5。

---

## 5. 给库新增 rule / skill / hook

### 场景

你发现一个值得标准化的新行为（比如"提交 JS 前总是 `prettier --check`"）。

### 步骤

```bash
cd ~/.claude/agent-harness
claude

# 加规则：
/new-rule prettier-check-before-commit

# 加技能：
/new-skill general/format-staged

# 加钩子：
/new-hook prettier-format-on-edit
```

每个元技能 scaffold 出对应文件（含 frontmatter + 内容模板），提醒同 batch 更新 `INVENTORY.md`，提交前要你确认。

> **技能放置位置（关系 Claude Code 能否发现）：** 想让 Claude 自动发现的技能要放在**顶层** `skills/<kebab-name>/`
> —— Claude Code 插件加载器只扫 `skills/*/SKILL.md` **一级**,不扫 `skills/<bucket>/*`。（Codex 和 opencode 两级都看得到。）
> 详见 `/new-skill` 里的说明。

提交后 push：

```bash
git push origin main
```

要发版本看第 7 节。

---

## 6. 更新到最新版

### 本地 clone（方案 B 安装）

```bash
cd ~/.claude/agent-harness
git pull origin main
```

如果项目里用 raw URL `@imports`，下次 session 启动自动更新（无需操作）。

### Plugin 安装（方案 A）

```bash
/plugin update
```

### Pin 到某个版本

下游项目锁定到具体版本：

```markdown
<!-- 锁定到 v0.1.0 而不是 main -->
@https://raw.githubusercontent.com/jajupmochi/agent-harness/v0.1.0/rules/<rule>/snippet.md
```

本地 clone：`cd ~/.claude/agent-harness && git checkout v0.1.0`。

---

## 7. 发布新版本（维护者）

```bash
cd ~/.claude/agent-harness
claude
/publish minor
```

`/publish` 技能（在 `.claude/skills/publish/SKILL.md`）：

1. 验证：工作树干净 + 在 `main` + `gh` 已认证
2. 从 `git tag --list 'v*'` 读出当前版本
3. 计算新版本（patch / minor / major bump）
4. 从 git log 生成 release notes（按 Conventional Commit 类型分组）
5. 运行 pre-release 校验（`jq empty` JSON、privacy-redact 扫描）
6. 打 tag、push 分支 + tag
7. 用 notes 创建 GitHub release

---

## 疑难排解

### `/init-agent-harness` 找不到

技能还没在你的 CC 环境里：

- **Plugin 安装**：重跑 `/plugin install jajupmochi/agent-harness`
- **本地 clone**：把技能 symlink 进 `~/.claude/skills/`：

  ```bash
  ln -s ~/.claude/agent-harness/setup/init-agent-harness ~/.claude/skills/init-agent-harness
  ```

- **Raw URL**（高级）：手动，因为 SKILL.md 不会自动加载。建议改用 clone 或 plugin。

### 规则没生效

检查：

1. 项目 `CLAUDE.md` 里确实有 `@import` 行（或 snippet 已嵌入）
2. 路径解析正确（本地 clone 用 `@~/.claude/agent-harness/rules/...`——注意 tilde）
3. CLAUDE.md 改完后 CC 重启了一次（`@import` 解析有时需要重启）

### 钩子没触发

```bash
# 检查 settings.json 里钩子在不在：
cat .claude/settings.json | jq '.hooks'

# 手动触发一次匹配的工具调用（比如 Edit *.py）
# 然后看 Claude Code 日志——失败的钩子会打印错误
```

钩子运行时报错（比如 `uv run` 找不到），确认 CC 启动时 `uv` 在 `PATH` 里。nvm 管的 Node 也需要正确的 shell 初始化才能被 CC 看到。

### 需要帮助

- Issue 跟踪：https://github.com/jajupmochi/agent-harness/issues
- 已有讨论：看 closed issues 找常见问题
