# 内容总目（Inventory）

> 库中已收录条目的主索引。每次新增 / 删除 / 重命名都需更新。

> **语言：** [English](INVENTORY.md) | 中文

## Master TOC

- [当前状态](#当前状态)
- [Rules](#rules)
- [Skills](#skills)
- [Hooks](#hooks)
- [Recommendations](#recommendations)
- [Tooling](#tooling)
- [Templates](#templates)
- [Setup](#setup)
- [Codex 适配](#codex-适配)

## 当前状态

**当前 Phase：** 全部 10 个阶段完成（v0.1.0 发布于 2026-04-29）。发布后：外部发布渠道状态记在 [PUBLISHING.md](PUBLISHING.md)；git history 已通过 `git filter-repo` 清理早期的 setup-skill literal + 用户特定绝对路径（见 git log 的 rewrite 记录）。

- P1：基础骨架 ✓
- P1.5：Discovery（gitignore）✓
- P2：规则 ✓
- P3：钩子 ✓
- P4：技能 ✓
- P5：推荐清单 ✓
- P6：工具偏好 ✓
- P7：项目模板 ✓
- P8：安装技能 ✓
- P9：LICENSE + 元技能 + GitHub publish ✓（https://github.com/jajupmochi/agent-harness）
- P10：Plugin packaging（`.claude-plugin/plugin.json`）✓
- P11：Codex adapter（`.codex-plugin`、wrapper skills、`hooks.json`、安装/验证/更新脚本）✓

详见 [docs/PHILOSOPHY.zh.md](docs/PHILOSOPHY.zh.md) 与 README 的"构建历程"。

## Rules

✅ 14 条规则 + 索引 README。初始 9 条在 P2 填充（2026-04-29）；5 条新增于 2026-05-21（从全局 `~/.claude/CLAUDE.md` 演化提取：end-of-turn-marker、always-on-verification、autorun-mode、multi-round-redesign、latex-edit-policy）。

| 规则 | Scope | 一句话 |
|---|---|---|
| [`chinese-output`](rules/chinese-output/RULE.md) | personal | 最终面向用户的输出用中文；中间过程保持英文 |
| [`pre-edit-confirmation`](rules/pre-edit-confirmation/RULE.md) | universal | 任何 Edit / Write 前列出精确目标 + 一句话计划，等用户 explicit "go" |
| [`phased-planning`](rules/phased-planning/RULE.md) | universal | 中大任务（3+ 文件 / > ~5 次工具调用 / 多步骤）分阶段编号，每阶段后暂停 |
| [`plugin-preflight`](rules/plugin-preflight/RULE.md) | universal | 调用插件 / skill / 命令前先验证已安装且未弃用 |
| [`ui-iteration-loop`](rules/ui-iteration-loop/RULE.md) | ui-project | 自动 8 轮 UI 迭代循环，配 chrome-devtools 截图与四轴自评 |
| [`output-brevity`](rules/output-brevity/RULE.md) | personal | 不在末尾复述、不回显工具输出、优先 Edit 而非 Write |
| [`human-readable-output`](rules/human-readable-output/RULE.md) | personal | 所有输出（聊天和文档）写成完整的人类句子和表格，不要电报体 AI 缩写；结构化信息优先用表格 |
| [`writing-style`](rules/writing-style/RULE.md) | personal | 去 AI 味写作习惯。不用连字符拼合修饰词，不用冒号或分号在整句后接一段话，不用风格化填充词（important/crucial/genuinely 等）。改用户自己写的文字时最小化、外科式 |
| [`tool-proactivity`](rules/tool-proactivity/RULE.md) | personal | 已安装的插件 / skill / MCP 匹配场景时主动调用（含若干"必须先确认"的例外） |
| [`no-reread-files`](rules/no-reread-files/RULE.md) | personal | 信任本 session 内对文件内容的记忆；除非真的变了不再重读 |
| [`bilingual-docs`](rules/bilingual-docs/RULE.md) | optional | `NAME.md` + `NAME.zh.md` 双语文档约定（消费方 opt-in via `setup/init-agent-harness`） |
| [`end-of-turn-marker`](rules/end-of-turn-marker/RULE.md) | personal | 每轮以 `[END:FINAL]` / `[END:WAIT]` / `[END:NEEDS_USER]` 单行结束 |
| [`always-on-verification`](rules/always-on-verification/RULE.md) | research-pkg | 任何 code / test / 结果声明前，调用 `code-verifier`（artifact 真实性）+ `research-critic`（推理链可靠性） |
| [`autorun-mode`](rules/autorun-mode/RULE.md) | personal | 用户说 "autorun" / "全力跑" / "think a lot" + scope 时：高自主 cadence + 多轮 review + 分支卫生 |
| [`multi-round-redesign`](rules/multi-round-redesign/RULE.md) | ui-project | N 轮 UI 重设计协议——日期戳子目录里 `00-plan.md` + 每轮 `round-N.html`/`.png`/`.notes.md` + 最终 spec lock + production-lock 轮 |
| [`latex-edit-policy`](rules/latex-edit-policy/RULE.md) | research-pkg | 编辑 `.tex`/`.sty`/`.cls`/`.bib` 时：hard fix 直接改；soft（内容）改动注释保留原文不删，打 `% [orig YYYY-MM-DD]` 内联备份（LaTeX 内容编辑场景覆盖 output-brevity） |
| [`clickable-links`](rules/clickable-links/RULE.md) | personal | 每一处 commit / 文件 / 行 / PR / 文档 / 来源引用都是完整可点击链接——绝不用裸 hash、半截路径或残缺 URL |
| [`design-artifacts`](rules/design-artifacts/RULE.md) | personal | 设计了 API / UI？列出端点 + 可点击的本地测试链接（Swagger/Storybook）+ 给出实时预览链接 + 附截图——文档和小结里都要 |
| [`test-first`](rules/test-first/RULE.md) | personal | 任何代码改动前/同时写测试，覆盖每一个改动层级；跑完整套件看前后 delta，而非只跑目标测试 |
| [`design-modes`](rules/design-modes/RULE.md) | personal | 原型模式 vs 规模化模式——开工先问是哪种、切换时确认；决定一次改动要多少严谨度/验证 |
| [`regression-test-on-bugfix`](rules/regression-test-on-bugfix/RULE.md) | universal | 每个 bug 修复必须附回归测试：旧代码上失败、修复后通过（红→绿）；没有它的行为修复不算完成 |
| [`incremental-delivery`](rules/incremental-delivery/RULE.md) | universal | 完成的独立部分随做随交付（验证 → 推 staging → 远端+视觉验证 → 逐件汇报）；别干等整批。只有真正依赖/无法验证/需授权的才 hold |
| [`parity-restoration`](rules/parity-restoration/RULE.md) | universal | 对齐环境↔环境（staging↔prod、1:1 还原）？先枚举组件/页面 PLAN 确保不漏，逐项确定性对比，再按方向归类：reference→target 数据自动同步，target→reference 的新增列出交负责人。绝不改动 reference |
| [`commit-discipline`](rules/commit-discipline/RULE.md) | universal | 每个 commit 遵循 conventional-commit 格式（`type(scope): description`）；不允许空消息或单词消息。非原生模型下由 `scripts/codex_commit_msg.sh` 装的 commit-msg 钩子强制 |
| [`root-cause-before-fix`](rules/root-cause-before-fix/RULE.md) | personal | 修任何 bug 前：先复现+定位（`file:line`）、读失败行的历史（`git log -L`/blame）、和 baseline 分支对比以区分回归 vs 既有脆弱性并回答"为什么现在"，追踪坏值到源头，再在正确层级修复并记录。绝不 patch-first |
| [`fallback-discipline`](rules/fallback-discipline/RULE.md) | personal | fallback / `pass` / 吞异常按场景判定：生产环境允许但必须记录触发点+主路径为何失败；测试/开发默认有罪——当场修或大声抛出，绝不静默藏 bug。分界问题："这个 fallback 触发了，有人会发现吗？" |

详见 [`rules/README.md`](rules/README.md)（用法说明 + scope 标签定义）。

## Skills

✅ general 桶 8 个技能 + 索引 README。初始 5 个在 P4 填充（2026-04-29）；2 个新增于 2026-05-21（从用户级 always-on 验证 gates 蒸馏）；1 个新增于 2026-05-31（`system-cleanup`，从一次真实的磁盘清理 session 蒸馏）。

| 技能 | 桶 | 触发 | 用途 |
|---|---|---|---|
| [`verify-template`](skills/general/verify-template/SKILL.md) | general | `/verify` | 本地跑 CI 门禁；按项目定制内容 |
| [`preview-template`](skills/general/preview-template/SKILL.md) | general | `/preview` | 启动本地 dev server；按项目类型定制 |
| [`long-running-tasks`](skills/general/long-running-tasks/SKILL.md) | general | 自动 / `/long-running-tasks` | 决策树：后台 subagent vs Monitor vs 显式超时 |
| [`verify-visual`](skills/general/verify-visual/SKILL.md) | general | UI 改动时自动 | chrome-devtools MCP 截图 + 四轴对比参考 |
| [`privacy-redact`](skills/general/privacy-redact/SKILL.md) | general | `/privacy-redact <file>` | 扫描并 redact 用户名、绝对路径、密钥、代号 |
| [`code-verifier`](skills/general/code-verifier/SKILL.md) | general | 自动 / `/code-verifier` | "tests pass" / "code works" / "结果是 X" 前的三层门禁——检测 FAKE-RUN 模式（硬编码结果、`assert True`、纯 mock 测试等） |
| [`research-critic`](skills/general/research-critic/SKILL.md) | general | 自动 / `/research-critic` | 六问审计：可证伪性 · 设计与假设匹配 · 公平比较 · 泄漏 · 结论与证据匹配 · 替代解释排除 |
| [`system-cleanup`](skills/general/system-cleanup/SKILL.md) | general | 自动 / `/system-cleanup` | 诊断爆满的 Linux 磁盘（df/du/dpkg/snap/docker）→ 按优先级、带风险标签的清理；安全的用户级删除 + sudo 项交给用户跑；覆盖 VS Code WebStorage 膨胀、旧内核、NTFS 数据盘写入失败。附 `cleanup.sh`。 |
| [`linux-freeze-triage`](skills/general/linux-freeze-triage/SKILL.md) | general | 自动 / `/linux-freeze-triage` | 用证据定位 Linux 死机/黑屏的真正原因（排除休眠、自动升级导致的 NVIDIA 内核/用户态版本错配、OOM、PCIe 链路、DPMS 挂起）；附近零成本看门狗 + 只读诊断套件。附 `diagnose.sh` + `freeze-watch.sh`。 |
| [`figma-design-fetch`](skills/figma-design-fetch/SKILL.md) | general | figma.com URL 时自动 / `/figma-fetch <node-url>` | 完整 Figma→代码流水线（官方 MCP）：OAuth 连接、抓取前设计预检 lint、5 步（抽取真实值→映射设计系统 token→实现→视觉自检闸门→汇报）到 gitignore 的 `.design-imports/`；附 `scripts/visual-diff.mjs`（pixelmatch 客观闸门）+ 6 个实测坑。 |
| [`figma-authoring-constraints`](skills/figma-authoring-constraints/SKILL.md) | general | 设计师询问 / 变量为空 / 出像素快照时自动 | Figma 端 20 条设计规约（变量/token、auto layout、组件/变体、命名、Dev Mode/Code Connect、别用栅格占位），让设计在 Figma 端就干净可出码——figma-design-fetch 流水线的设计侧。 |

后续桶（将在 P7 模板里填充）：

- `research-pkg/` —— Python 研究包专用（`new-adapter`、`new-experiment` 等）
- `static-site/` —— 静态主页专用（`new-round`、`deploy-round`、`i18n-sync`）

详见 [`skills/README.md`](skills/README.md)。

## Hooks

✅ 已在 P3 填充（2026-04-29）。2 个钩子 + 索引 README。

| 钩子 | Event | Matcher | Context | 一句话 |
|---|---|---|---|---|
| [`ruff-format-on-edit`](hooks/ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | research-pkg / 任何 Python 项目 | Claude 编辑 `*.py` 后用 ruff 自动格式化 |
| [`jq-validate-json`](hooks/jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | static-site / JSON 配置项目 | Claude 写入指定路径下无效 JSON 时拦截下次工具调用 |
| [`typecheck-on-edit`](hooks/typecheck-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | 前端 / TypeScript | `.ts(x)` 编辑后跑 prettier + `tsc --noEmit`；**类型错误 exit 2 阻断本轮**（Figma→代码质量脊梁） |
| [`block-env-read`](hooks/block-env-read/README.md) | `PreToolUse` | `Read` | 任何含密钥的仓库 | 阻止读 `.env*`，密钥不进 transcript（exit 2） |

详见 [`hooks/README.md`](hooks/README.md)（安装方式）。

## Recommendations

✅ 15 个 active 文件 + 2 个 reference table + 索引 README。初始 12 个在 P5 填充（2026-04-29）；3 个新增于 2026-05-21（ai-coding-tools、cluster-hpc、reference-projects）。多个现存文件补充了条目（Chakra UI、anime.js、useanimations、itshover、HyperFrames、math-curve-loaders、React Native motion、yesicon.app、svgl.app、MLflow + W&B + ClearML）。

| 文件 | Context | 覆盖 |
|---|---|---|
| [cc-plugins.md](recommendations/cc-plugins.md) | always | 37 个 Claude Code 插件（workflow / 集成 / specialized） |
| [cc-marketplaces-and-skill-bundles.md](recommendations/cc-marketplaces-and-skill-bundles.md) | always | 4 个第三方 marketplace + 9 个 `npx skills add` 装的 skill bundle |
| [cli-tools.md](recommendations/cli-tools.md) | always（按需） | 系统 CLI（jq、gh、ripgrep、fd 等）+ Python 用户级 CLI（uv、ruff、mkdocs、hf 等） |
| [js-ui-and-design.md](recommendations/js-ui-and-design.md) | ui-project | Lucide、Radix 全套、**Chakra UI**、lenis、d3、visx、recharts、monaco、tanstack/table、shadcn；图标浏览器（**yesicon.app**、**svgl.app**） |
| [js-animation-and-3d.md](recommendations/js-animation-and-3d.md) | ui-project + 3d-or-animation | motion、gsap、**anime.js**、lottie-react、tailwindcss-animate、**math-curve-loaders**；three、R3F、drei、mediapipe；**动效图标库**（itshover、useanimations）；**HTML→视频**（HyperFrames、Remotion）；**React Native motion** |
| [js-build-test-style.md](recommendations/js-build-test-style.md) | ui-project | vite、next、electron、vitest、playwright、storybook、tailwindcss、prettier |
| [js-state-data.md](recommendations/js-state-data.md) | ui-project | pinia、zustand、swr、vueuse、vue-i18n、vue-router、next-themes |
| [web-auditing.md](recommendations/web-auditing.md) | static-site / web-perf | chrome-devtools MCP（默认）、lighthouse CLI、lhci、pa11y、axe-core |
| [image-video-pdf.md](recommendations/image-video-pdf.md) | image-or-video-work | sharp、svgo、imagemin、ffmpeg（apt）、puppeteer |
| [docs-tools.md](recommendations/docs-tools.md) | docs-site | mkdocs + material、ghp-import、latexmk（apt） |
| [ml-research.md](recommendations/ml-research.md) | ml-research | huggingface_hub[cli]、datasets、gpustat、kaleido、selenium；**实验跟踪平台**（MLflow、Weights & Biases、ClearML） |
| [orchestra-ml-skills.md](recommendations/orchestra-ml-skills.md) | ml-research | 21 类 ML 技能栈，含 `0-autoresearch-skill` 元编排器 |
| [ai-coding-tools.md](recommendations/ai-coding-tools.md) | optional | Spec-driven 脚手架（**OpenSpec**）+ 论文 review（**paperreview.ai**） |
| [cluster-hpc.md](recommendations/cluster-hpc.md) | optional | SLURM 模式、free-tier 规则、HPC 集群 rsync 约定 |
| [reference-projects.md](recommendations/reference-projects.md) | optional | 值得学习的 standalone demo / template 项目（例如 `mykonos-island-voxels` —— 零依赖 Canvas 2D 等距岛屿生成器，painterly 资产、分层缓存渲染、触屏 UI） |
| [reference/apt-packages.md](recommendations/reference/apt-packages.md) | always（查询） | apt 包知识表——绝不自动安装 |
| [reference/vscode-extensions.md](recommendations/reference/vscode-extensions.md) | always（查询） | VS Code 扩展知识表——绝不自动安装；CC-friendly 默认值已标注 |

详见 [`recommendations/README.md`](recommendations/README.md)（context 标签 + `setup/init-agent-harness` 如何按项目类型决定安装哪些）。

## Tooling

✅ 已在 P6 填充（2026-04-29）。3 个工具类目 + 索引 README。

| 目录 | Context | 给出什么 |
|---|---|---|
| [python-uv-ruff/](tooling/python-uv-ruff/README.md) | research-pkg | `uv` + `ruff` 安装步骤 + 标准 `pyproject.template.toml`（extras、ruff 配置、mypy、pytest） |
| [node-nvm/](tooling/node-nvm/README.md) | ui-project、electron-or-desktop | nvm 安装 + Node 22 LTS + 最小化全局包哲学 + scaffold 指引 |
| [permissions-allowlist/](tooling/permissions-allowlist/README.md) | always（按需） | `settings.local.snippet.json`：从真实项目里提炼的常见安全 Bash 白名单 |

详见 [`tooling/README.md`](tooling/README.md)。

## Templates

✅ 已在 P7 填充（2026-04-29）。2 个项目模板 + 索引 README。

| 模板 | 项目类型 | 包含 |
|---|---|---|
| [research-package-py/](templates/research-package-py/TEMPLATE_README.md) | Python 研究包（uv + ruff + pytest） | CLAUDE.template.md、pyproject.template.toml（含研究 extras：torch/data/logging）、.gitignore、.claude/settings.template.json（ruff 格式化钩子）、.claude/skills/verify/ |
| [personal-cite-static/](templates/personal-cite-static/TEMPLATE_README.md) | 静态个人学术主页（HTML/CSS/JS、i18n、双语） | CLAUDE.template.md（双语 + 视觉验证 + 迭代 round 文件约定）、index.template.html（i18n）、locales/{en,zh}.template.json、.gitignore、.claude/settings.template.json（jq JSON 校验钩子）、.claude/skills/{preview,verify-visual,i18n-sync}/ |

详见 [`templates/README.md`](templates/README.md)。`setup/init-agent-harness` 技能（P8）自动完成占位符替换与组合。

## Setup

✅ 已在 P8 填充（2026-04-29）。1 个安装技能 + 索引 README。

| 技能 | 用途 |
|---|---|
| [`init-agent-harness`](setup/init-agent-harness/SKILL.md) | 交互式 `/init-agent-harness` 斜杠命令。问 6 个问题（项目类型、双语策略、终端输出语言、context 标签、消费方式、个人偏好规则），然后从库中组合相应子集的 rules / hooks / skills / templates / tooling 到项目里。 |

详见 [`setup/README.md`](setup/README.md)。

## Codex 适配

已从 `codex-adapter` 分支融合（2026-07-08）。Claude Code 入口保持不变，Codex 使用独立 manifest 和 wrapper 层。

| 条目 | 用途 |
|---|---|
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) | Codex 插件 manifest；技能入口使用 `skills: "./skills/"` |
| [`hooks.json`](hooks.json) | 渲染为用户级或项目级绝对路径 hooks 的源模板；不声明为插件 hook |
| [`codex/`](codex) | 用户指导、4 个自定义 Agent 和只供审阅的模型/MCP 配置示例 |
| [`skills/init-codex-config`](skills/init-codex-config/SKILL.md) | 通过 `AGENTS.md`、`.codex/hooks.json` 和 `.agents/skills` 配置 Codex 项目 |
| [`scripts/install-codex-local.js`](scripts/install-codex-local.js) | 安装 20 个用户技能、策略安装插件条目、用户 AGENTS/hooks 和 4 个自定义 Agents；默认不覆盖不同文件 |
| [`scripts/verify-codex-adapter.js`](scripts/verify-codex-adapter.js) | 与隔离安装器、模型路由、ruff 和 review-gate 测试组合的结构验证 |
