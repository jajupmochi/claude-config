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
- [仓库工具](#仓库工具)
- [Codex 适配](#codex-适配)

## 当前状态

**当前 Phase：** P1 到 P11 全部完成（v0.1.0 发布于 2026-04-29）。外部发布渠道状态记在 [PUBLISHING.md](PUBLISHING.md)。git history 已通过 `git filter-repo` 清理早期的 setup-skill literal 与用户特定绝对路径（见 git log 的 rewrite 记录）。

下面每一处数量都以 [`adapters/manifest.source.json`](adapters/manifest.source.json) 为准，它是唯一事实来源。各 agent 的 manifest 由 `node build.mjs` 从它生成，一旦漂移，`node build.mjs --check` 会失败。

1. P1：基础骨架 ✓
2. P1.5：Discovery（gitignore）✓
3. P2：规则 ✓
4. P3：钩子 ✓
5. P4：技能 ✓
6. P5：推荐清单 ✓
7. P6：工具偏好 ✓
8. P7：项目模板 ✓
9. P8：安装技能 ✓
10. P9：`LICENSE` + 元技能 + GitHub publish ✓（https://github.com/jajupmochi/agent-harness）
11. P10：Plugin packaging（`.claude-plugin/plugin.json`）✓
12. P11：Codex adapter（`.codex-plugin`、wrapper skills、`hooks.json`、安装/验证/更新脚本）✓

详见 [docs/PHILOSOPHY.zh.md](docs/PHILOSOPHY.zh.md) 与 README 的"构建历程"。

## Rules

✅ 28 条规则 + 索引 README。初始 9 条在 P2 填充（2026-04-29）；5 条新增于 2026-05-21（从全局 `~/.claude/CLAUDE.md` 演化提取：end-of-turn-marker、always-on-verification、autorun-mode、multi-round-redesign、latex-edit-policy）；其余从后续真实 session 里蒸馏。`native-capability-first` 排在最前，因为它决定其余 27 条是否适用。

| 规则 | Scope | 一句话 |
|---|---|---|
| [`native-capability-first`](rules/native-capability-first/RULE.md) | universal | 优先级最高。调用任何 harness 功能前，先判断它是否适合当前任务、照做是否会比你自己不借助它更差。有一份永不豁免清单——验证 gate、强制执行的 hook、隐私、破坏性操作确认，以及用户自己的指令 |
| [`chinese-output`](rules/chinese-output/RULE.md) | personal | 最终面向用户的输出用中文；中间过程保持英文 |
| [`pre-edit-confirmation`](rules/pre-edit-confirmation/RULE.md) | universal | 任何 Edit / Write 前列出精确目标 + 一句话计划，等用户 explicit "go" |
| [`no-ssh-username-probing`](rules/no-ssh-username-probing/RULE.md) | universal | SSH 前先确认准确用户名；只试一次，失败就问——绝不轮询候选用户名（会触发 fail2ban → 自己把 IP 封掉）。由 `ssh-guard` 钩子强制 |
| [`phased-planning`](rules/phased-planning/RULE.md) | universal | 中大任务（3+ 文件 / > ~5 次工具调用 / 多步骤）分阶段编号，每阶段后暂停 |
| [`plugin-preflight`](rules/plugin-preflight/RULE.md) | universal | 调用插件 / skill / 命令前先验证已安装且未弃用 |
| [`ui-iteration-loop`](rules/ui-iteration-loop/RULE.md) | ui-project | 自动 8 轮 UI 迭代循环，配 chrome-devtools 截图与四轴自评 |
| [`output-brevity`](rules/output-brevity/RULE.md) | personal | 不在末尾复述、不回显工具输出、优先 Edit 而非 Write |
| [`human-readable-output`](rules/human-readable-output/RULE.md) | personal | 所有输出（聊天和文档）写成完整的人类句子和表格，不要电报体 AI 缩写；结构化信息优先用表格 |
| [`writing-style`](rules/writing-style/RULE.md) | personal | 去 AI 味写作习惯。不用连字符拼合修饰词，不用冒号或分号在整句后接一段话，不用风格化填充词（important/crucial/genuinely 等）。改用户自己写的文字时最小化、外科式 |
| [`tool-proactivity`](rules/tool-proactivity/RULE.md) | personal | 已安装的插件 / skill / MCP 匹配场景时主动调用（含若干"必须先确认"的例外） |
| [`no-reread-files`](rules/no-reread-files/RULE.md) | personal | 信任本 session 内对文件内容的记忆；除非真的变了不再重读 |
| [`bilingual-docs`](rules/bilingual-docs/RULE.md) | optional | `NAME.md` + `NAME.zh.md` 双语文档约定（消费方 opt-in via `setup/init-agent-config`） |
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
| [`parity-restoration`](rules/parity-restoration/RULE.md) | universal | 对齐环境↔环境（staging↔prod、1:1 还原）？先枚举组件/页面清单（PLAN）确保不漏，逐项确定性对比，再按方向归类：reference→target 数据自动同步，target→reference 的新增列出交负责人。绝不改动 reference |
| [`commit-discipline`](rules/commit-discipline/RULE.md) | universal | 每个 commit 遵循 conventional-commit 格式（`type(scope): description`）；不允许空消息或单词消息。非原生模型下由 `scripts/codex_commit_msg.sh` 装的 commit-msg 钩子强制 |
| [`root-cause-before-fix`](rules/root-cause-before-fix/RULE.md) | personal | 修任何 bug 前：先复现+定位（`file:line`）、读失败行的历史（`git log -L`/blame）、和 baseline 分支对比以区分回归 vs 既有脆弱性并回答"为什么现在"，追踪坏值到源头，再在正确层级修复并记录。绝不 patch-first |
| [`fallback-discipline`](rules/fallback-discipline/RULE.md) | personal | fallback / `pass` / 吞异常按场景判定：生产环境允许但必须记录触发点+主路径为何失败；测试/开发默认有罪——当场修或大声抛出，绝不静默藏 bug。分界问题："这个 fallback 触发了，有人会发现吗？" |

详见 [`rules/README.md`](rules/README.md)（用法说明 + scope 标签定义）。

## Skills

✅ 已注册 24 个技能 + 索引 README——下表 23 个，再加上单列一节的 [`init-agent-config`](setup/init-agent-config/SKILL.md)（见 [Setup](#setup)）。初始 5 个在 P4 填充（2026-04-29）；2 个新增于 2026-05-21（从用户级 always-on 验证 gates 蒸馏）；其余从真实 session 里蒸馏。

"是否注册"不只是记账。[`bin/deploy-skills.mjs`](bin/deploy-skills.mjs) 读的正是 [`adapters/manifest.source.json`](adapters/manifest.source.json) 里这份列表，把每一项 symlink 进各 agent 的原生技能目录。所以一个没进 manifest 的技能，无论目录存在多久，都不会被送到 opencode。

| 技能 | 桶 | 触发 | 用途 |
|---|---|---|---|
| [`verify-template`](skills/general/verify-template/SKILL.md) | general | `/verify` | 本地跑 CI 门禁；按项目定制内容 |
| [`preview-template`](skills/general/preview-template/SKILL.md) | general | `/preview` | 启动本地 dev server；按项目类型定制 |
| [`long-running-tasks`](skills/general/long-running-tasks/SKILL.md) | general | 自动 / `/long-running-tasks` | 决策树：后台 subagent vs Monitor vs 显式超时 |
| [`verify-visual`](skills/general/verify-visual/SKILL.md) | general | UI 改动时自动 | chrome-devtools MCP 截图 + 四轴对比参考 |
| [`privacy-redact`](skills/general/privacy-redact/SKILL.md) | general | `/privacy-redact <file>` | 扫描并 redact 用户名、绝对路径、密钥、代号 |
| [`code-verifier`](skills/general/code-verifier/SKILL.md) | general | 自动 / `/code-verifier` | "tests pass" / "code works" / "结果是 X" 前的三层门禁——检测 FAKE-RUN（伪造运行）模式（硬编码结果、`assert True`、纯 mock 测试等） |
| [`research-critic`](skills/general/research-critic/SKILL.md) | general | 自动 / `/research-critic` | 六问审计：可证伪性 · 设计与假设匹配 · 公平比较 · 泄漏 · 结论与证据匹配 · 替代解释排除 |
| [`system-cleanup`](skills/general/system-cleanup/SKILL.md) | general | 自动 / `/system-cleanup` | 诊断爆满的 Linux 磁盘（df/du/dpkg/snap/docker）→ 按优先级、带风险标签的清理；安全的用户级删除 + sudo 项交给用户跑；覆盖 VS Code WebStorage 膨胀、旧内核、NTFS（Windows 文件系统）数据盘写入失败。附 `cleanup.sh`。 |
| [`linux-freeze-triage`](skills/general/linux-freeze-triage/SKILL.md) | general | 自动 / `/linux-freeze-triage` | 用证据定位 Linux 死机/黑屏的真正原因（排除休眠、自动升级导致的 NVIDIA 内核/用户态版本错配、OOM、PCIe 链路、DPMS 挂起）；附近零成本看门狗 + 只读诊断套件。附 `diagnose.sh` + `freeze-watch.sh`。 |
| [`figma-design-fetch`](skills/figma-design-fetch/SKILL.md) | general | figma.com URL 时自动 / `/figma-fetch <node-url>` | 完整 Figma→代码流水线（官方 MCP）：OAuth 连接、抓取前设计预检 lint、5 步（抽取真实值→映射设计系统 token→实现→视觉自检闸门→汇报）到 gitignore 的 `.design-imports/`；附 `scripts/visual-diff.mjs`（pixelmatch 客观闸门）+ 6 个实测坑。 |
| [`figma-authoring-constraints`](skills/figma-authoring-constraints/SKILL.md) | general | 设计师询问 / 变量为空 / 出像素快照时自动 | Figma 端 20 条设计规约（变量/token、auto layout、组件/变体、命名、Dev Mode/Code Connect、别用栅格占位），让设计在 Figma 端就干净可出码——figma-design-fetch 流水线的设计侧。 |
| [`autoresearch-toolfinder`](skills/general/autoresearch-toolfinder/SKILL.md) | general | 自动 / `/autoresearch-toolfinder` | 从两份 awesome-autoresearch 清单（alvinreal + yibie，550+ 条）的本地缓存索引里找到合适的 autoresearch / research-agent 工具。`query.py` 只返回命中的少数几条，不把整个目录读进上下文；每周刷新，用内容哈希跟踪上游变化。 |
| [`autopilot`](skills/general/autopilot/SKILL.md) | general | `/autopilot` | 配置或管理每日自主项目驱动器——一个系统级定时器，每天起一次全新的 autorun session 推进项目，过 review-gate、重新规划、正式估算工时、卡住时自愈。 |
| [`doc-writing`](skills/doc-writing/SKILL.md) | general | 写任何给人读的文档时自动 / `/doc-writing` | 从两次真实项目 session 里蒸馏出的文档要求（每个术语就地定义、每条结论都给出证据并说明测试者如何复验、完整可点击链接、该画图的地方画图）。附 [`scripts/doccheck.py`](skills/doc-writing/scripts/doccheck.py)，对其中可机器检查的部分做 lint。 |
| [`task-orchestrator`](skills/task-orchestrator/SKILL.md) | general | 自动 / `/task-orchestrator` | 对每个原子任务强制 Research → Design → Plan → Execute → Verify 流水线。按探测到的模型能力调整计划模板的严格度，并把更好的做法回写进模板。 |
| [`task-relationship-analysis`](skills/task-relationship-analysis/SKILL.md) | general | 3 个以上任务的请求前自动 | 执行前先梳理这些任务彼此的关系（协同、冲突、共享底座、先后顺序），避免三个共用同一块东西的任务被分别造三遍。给出两两矩阵 + 综合检查表。 |
| [`memory-flywheel`](skills/memory-flywheel/SKILL.md) | general | 自动 / `/memory-flywheel` | 按项目维护跨 session 的工作记忆，避免长 session 因上下文压缩丢细节。每轮进展写进项目记忆目录，先读粗粒度索引，再按关键词召回打开具体条目。 |
| [`prompt-library`](skills/prompt-library/SKILL.md) | general | `/prompt-library` | 跨项目、跨 agent 保存和复用好的 prompt，并从本地 Claude Code / Codex / Copilot / opencode 历史里挖出过去写过的，整理成可浏览、可 grep 的 Markdown。 |
| [`agent-update-watcher`](skills/agent-update-watcher/SKILL.md) | general | 自动 / `/agent-update-watcher` | 跟进 agent 生态（新增或更新的 CLI、插件、技能）而不必频繁轮询。只在超过最小间隔后检查声明的来源列表，且只报告相对已记录版本真正变化的部分。 |
| [`tui-installer`](skills/tui-installer/SKILL.md) | general | `/tui-installer` | 在 Ubuntu 上安装（或只是规划）驱动多个编码 agent 的终端栈（zellij + claude-squad + lazygit + delta）。默认 dry-run，`--apply` 时逐个工具询问。 |
| [`agent-config-adapter`](skills/agent-config-adapter/SKILL.md) | general | 自动 / `/agent-config-adapter` | 把一套 agent 配置或插件适配到另一个 agent 或模型路由——Claude Code、Codex、Gemini、Cursor、本地模型，或 DeepSeek 这类非原生后端。 |
| [`init-codex-config`](skills/init-codex-config/SKILL.md) | general | `/init-codex-config` | 通过 `AGENTS.md`、`.codex/hooks.json` 和 `.agents/skills` 把项目接到 Codex 上使用 agent-harness，不改动原有的 Claude 配置。 |
| [`end-of-turn-marker`](skills/end-of-turn-marker/SKILL.md) | general | 每轮结束时自动 | 每轮以可见分隔标题 + 编号小结项收尾，其中带 `[END:FINAL]` / `[END:WAIT]` / `[END:NEEDS_USER]`。是同名规则的技能侧。 |

后续桶（将在 P7 模板里填充）：

- `research-pkg/` —— Python 研究包专用（`new-adapter`、`new-experiment` 等）
- `static-site/` —— 静态主页专用（`new-round`、`deploy-round`、`i18n-sync`）

详见 [`skills/README.md`](skills/README.md)。

## Hooks

✅ 7 个钩子 + 索引 README。前两个在 P3 填充（2026-04-29）；`typecheck-on-edit`、`block-env-read`、`ssh-guard`、`review-gate`、`task-ledger` 是后来从真实 session 里补的。

| 钩子 | Event | Matcher | Context | 一句话 |
|---|---|---|---|---|
| [`ruff-format-on-edit`](hooks/ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | research-pkg / 任何 Python 项目 | Claude 编辑 `*.py` 后用 ruff 自动格式化 |
| [`jq-validate-json`](hooks/jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | static-site / JSON 配置项目 | Claude 写入指定路径下无效 JSON 时拦截下次工具调用 |
| [`typecheck-on-edit`](hooks/typecheck-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | 前端 / TypeScript | `.ts(x)` 编辑后跑 prettier + `tsc --noEmit`；**类型错误 exit 2 阻断本轮**（Figma→代码质量脊梁） |
| [`block-env-read`](hooks/block-env-read/README.md) | `PreToolUse` | `Read` | 任何含密钥的仓库 | 阻止读 `.env*`，密钥不进 transcript（exit 2） |
| [`ssh-guard`](hooks/ssh-guard/README.md) | `PreToolUse` | `Bash` | 任何需要 SSH 访问主机的项目 | 拦截 SSH 用户名试探（一次连击里出现第 2 个不同的 `user@host`）——正是会触发 fail2ban 把你 IP 封掉的模式；强制执行 `no-ssh-username-probing`（exit 2） |
| [`review-gate`](hooks/review-gate/README.md) | `PostToolUse` + `Stop` + `PreToolUse` | `Write\|Edit`、`Bash` | 任何由 agent 写代码的仓库 | 对每个改动代码的回合做无法跳过的审阅。T0 记录每个被改的文件，T1 在 linter 干净且完成一轮产出 Markdown 报告的审阅前一直阻断 `Stop`，T2 放行 `git commit` 但拦截远端发布，除非项目在 `push-whitelist.txt` 上 |
| [`task-ledger`](hooks/task-ledger/README.md) | `Stop` + `UserPromptSubmit` | —— | 子任务超过十个左右的回合 | 每轮一份任务文档。`Stop` gate 在还有任务未完成、有任务被标记完成却没有证据、或有中途新增需求未分诊时拒绝结束本轮；`UserPromptSubmit` 捕获会在中途需求被遗忘前先记下来 |

详见 [`hooks/README.md`](hooks/README.md)（安装方式）。

## Recommendations

✅ 21 个推荐文件 + 索引 README——19 个 active 清单 + 2 个 reference table。初始 12 个在 P5 填充（2026-04-29）；3 个新增于 2026-05-21（ai-coding-tools、cluster-hpc、reference-projects）；4 个后续新增（tui-for-agents、github-actions-frugality、codex-marketplaces、codex-plugins）。多个现存文件持续补充条目（Chakra UI、`anime.js`、useanimations、itshover、HyperFrames、math-curve-loaders、React Native motion、yesicon.app、svgl.app、MLflow + W&B + ClearML）。

| 文件 | Context | 覆盖 |
|---|---|---|
| [cc-plugins.md](recommendations/cc-plugins.md) | always | 37 个 Claude Code 插件（workflow / 集成 / specialized） |
| [cc-marketplaces-and-skill-bundles.md](recommendations/cc-marketplaces-and-skill-bundles.md) | always | 4 个第三方 marketplace + 9 个 `npx skills add` 装的 skill bundle |
| [cli-tools.md](recommendations/cli-tools.md) | always（按需） | 系统 CLI（jq、gh、ripgrep、fd 等）+ Python 用户级 CLI（uv、ruff、mkdocs、hf 等） |
| [js-ui-and-design.md](recommendations/js-ui-and-design.md) | ui-project | Lucide、Radix 全套、**Chakra UI**、lenis、d3、visx、recharts、monaco、tanstack/table、shadcn；图标浏览器（**yesicon.app**、**svgl.app**） |
| [js-animation-and-3d.md](recommendations/js-animation-and-3d.md) | ui-project + 3d-or-animation | motion、gsap、**`anime.js`**、lottie-react、tailwindcss-animate、**math-curve-loaders**；three、R3F（react-three-fiber）、drei、mediapipe；**动效图标库**（itshover、useanimations）；**HTML→视频**（HyperFrames、Remotion）；**React Native motion** |
| [js-build-test-style.md](recommendations/js-build-test-style.md) | ui-project | vite、next、electron、vitest、playwright、storybook、tailwindcss、prettier |
| [js-state-data.md](recommendations/js-state-data.md) | ui-project | pinia、zustand、swr、vueuse、vue-i18n、vue-router、next-themes |
| [web-auditing.md](recommendations/web-auditing.md) | static-site / web-perf | chrome-devtools MCP（默认）、lighthouse CLI、lhci、pa11y、axe-core |
| [image-video-pdf.md](recommendations/image-video-pdf.md) | image-or-video-work | sharp、svgo、imagemin、ffmpeg（apt）、puppeteer |
| [docs-tools.md](recommendations/docs-tools.md) | docs-site | mkdocs + material、ghp-import、latexmk（apt） |
| [ml-research.md](recommendations/ml-research.md) | ml-research | huggingface_hub[cli]、datasets、gpustat、kaleido、selenium；**实验跟踪平台**（MLflow、Weights & Biases、ClearML） |
| [orchestra-ml-skills.md](recommendations/orchestra-ml-skills.md) | ml-research | 21 类 ML 技能栈，含 `0-autoresearch-skill` 元编排器 |
| [ai-coding-tools.md](recommendations/ai-coding-tools.md) | optional | Spec-driven 脚手架（**OpenSpec**）+ 论文 review（**paperreview.ai**） |
| [cluster-hpc.md](recommendations/cluster-hpc.md) | optional | SLURM（集群作业调度器）模式、free-tier 规则、HPC（高性能计算）集群的 rsync 约定 |
| [reference-projects.md](recommendations/reference-projects.md) | optional | 值得学习的 standalone demo / template 项目（例如 `mykonos-island-voxels` —— 零依赖 Canvas 2D 等距岛屿生成器，painterly 资产、分层缓存渲染、触屏 UI） |
| [github-actions-frugality.md](recommendations/github-actions-frugality.md) | always（任何带 workflow 的仓库） | 压低远端 Actions 分钟数——核实过的 2026 计费事实与费率、按效果排序的手段、四层"本地到远端"方案与 profile、自建 runner 的盈亏平衡点与安全性、`act` 的局限、push 前的门禁。附 [`templates/actions-frugal-ci/`](templates/actions-frugal-ci/TEMPLATE_README.md) + [`scripts/actions-budget.mjs`](scripts/actions-budget.mjs) |
| [tui-for-agents.md](recommendations/tui-for-agents.md) | agent-workflow / terminal-first | 同时驱动多个编码 agent 的终端栈（claude-squad + Zellij/tmux + lazygit + delta），覆盖多 session、子 agent、diff 审阅和人在环，并如实写出 agent 之间互动的缺口 |
| [codex-marketplaces.md](recommendations/codex-marketplaces.md) | codex | Codex 的第三方 marketplace、skill bundle 与精选集合 |
| [codex-plugins.md](recommendations/codex-plugins.md) | codex | 已认可可配合 Codex 使用的插件、MCP server 与外部工具；已安装的按 `tool-proactivity` 规则自动触发 |
| [reference/apt-packages.md](recommendations/reference/apt-packages.md) | always（查询） | apt 包知识表——绝不自动安装 |
| [reference/vscode-extensions.md](recommendations/reference/vscode-extensions.md) | always（查询） | VS Code 扩展知识表——绝不自动安装；CC-friendly 默认值已标注 |

详见 [`recommendations/README.md`](recommendations/README.md)（context 标签 + `setup/init-agent-config` 如何按项目类型决定安装哪些）。

## Tooling

✅ 已在 P6 填充（2026-04-29）。3 个工具类目 + 索引 README。

| 目录 | Context | 给出什么 |
|---|---|---|
| [python-uv-ruff/](tooling/python-uv-ruff/README.md) | research-pkg | `uv` + `ruff` 安装步骤 + 标准 `pyproject.template.toml`（extras、ruff 配置、mypy、pytest） |
| [node-nvm/](tooling/node-nvm/README.md) | ui-project、electron-or-desktop | nvm 安装 + Node 22 LTS（长期支持版）+ 最小化全局包哲学 + scaffold 指引 |
| [permissions-allowlist/](tooling/permissions-allowlist/README.md) | always（按需） | `settings.local.snippet.json`：从真实项目里提炼的常见安全 Bash 白名单 |

详见 [`tooling/README.md`](tooling/README.md)。

## Templates

✅ 3 个模板 + 索引 README。前两个在 P7 填充（2026-04-29）；`actions-frugal-ci` 是后来加的，定位是给已有仓库的附加件，而不是项目起手模板。

| 模板 | 项目类型 | 包含 |
|---|---|---|
| [research-package-py/](templates/research-package-py/TEMPLATE_README.md) | Python 研究包（uv + ruff + pytest） | `CLAUDE.template.md`、`pyproject.template.toml`（含研究 extras：torch/data/logging）、`.gitignore`、`.claude/settings.template.json`（ruff 格式化钩子）、`.claude/skills/verify/` |
| [personal-cite-static/](templates/personal-cite-static/TEMPLATE_README.md) | 静态个人学术主页（HTML/CSS/JS、i18n、双语） | `CLAUDE.template.md`（双语 + 视觉验证 + 迭代 round 文件约定）、`index.template.html`（i18n）、`locales/{en,zh}.template.json`、`.gitignore`、`.claude/settings.template.json`（jq JSON 校验钩子）、`.claude/skills/{preview,verify-visual,i18n-sync}/` |
| [actions-frugal-ci/](templates/actions-frugal-ci/TEMPLATE_README.md) | 任何用 GitHub Actions 的仓库（附加件，不是起手模板） | 压低 Actions 分钟数的四层 CI：`git-hooks/{pre-commit,pre-push}.template.sh`（占位符没替换完就拒绝运行）、`lefthook.template.yml`、`.github/workflows/{ci,heavy,_checks.reusable}.template.yml`。原理与数据见 [github-actions-frugality.md](recommendations/github-actions-frugality.md) |

详见 [`templates/README.md`](templates/README.md)。`setup/init-agent-config` 技能（P8）自动完成占位符替换与组合。

## Setup

✅ 已在 P8 填充（2026-04-29）。1 个安装技能 + 索引 README。

| 技能 | 用途 |
|---|---|
| [`init-agent-config`](setup/init-agent-config/SKILL.md) | 交互式 `/init-agent-config` 斜杠命令。问 6 个问题（项目类型、双语策略、终端输出语言、context 标签、消费方式、个人偏好规则），然后从库中组合相应子集的 rules / hooks / skills / templates / tooling 到项目里。它是 manifest 技能列表里的第 24 项。 |

详见 [`setup/README.md`](setup/README.md)。

## 仓库工具

维护 harness 自身、而非下游项目的脚本。它们不属于 manifest 的六个类目，因此没有别处索引它们。

| 脚本 | 作用 |
|---|---|
| [`build.mjs`](build.mjs) | 从 [`adapters/manifest.source.json`](adapters/manifest.source.json) 生成各 agent 的 manifest。`--check` 在生成结果与源漂移时以非零码退出 |
| [`bin/deploy-skills.mjs`](bin/deploy-skills.mjs) | 把 manifest 里每个技能 symlink 进各 agent 的原生技能目录（`~/.claude/skills/`、`~/.config/opencode/skills/`）——这正是未注册技能永远到不了 opencode 的原因 |
| [`bin/rule-activation.mjs`](bin/rule-activation.mjs) | 报告"已注册但不生效"的规则。规则只有在其正文位于 agent 真正会读的文件里才会进模型，`--apply` 把缺失的补进一个可重新生成的托管块 |
| [`bin/harness-feedback.mjs`](bin/harness-feedback.mjs) | `native-capability-first` 反馈闭环的写入端。某个功能不合用时向 `docs/harness-feedback/QUEUE.md` 追加一条结构化记录，让"这次跳过"变成"以后修好"；`/harness-sync` 负责消费队列 |
| [`bin/capability-receipt.mjs`](bin/capability-receipt.mjs) | 读取 session transcript，逐个能力报告是否有证据表明它真的触发过。识别特征放在 `adapters/capabilities.json`，新增覆盖只需改配置 |
| [`scripts/actions-budget.mjs`](scripts/actions-budget.mjs) | 对仓库的 GitHub Actions workflow 做离线预算检查——PR 更新、合并、定时各会触发什么，计费分钟数下限，以及缺少 paths 过滤、用了非 Linux runner 之类的发现 |
| [`hooks/review-gate/scripts/statsbar.sh`](hooks/review-gate/scripts/statsbar.sh) | 把计数拆解渲染成对齐柱状图的共享渲染器，让 review-gate 和 task-ledger 在终端和 Markdown 里给出同一种形状 |

## Codex 适配

已从 `codex-adapter` 分支融合（2026-07-08）。Claude Code 入口保持不变，Codex 使用独立 manifest 和 wrapper 层。

| 条目 | 用途 |
|---|---|
| [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) | Codex 插件 manifest；技能入口使用 `skills: "./skills/"` |
| [`hooks.json`](hooks.json) | 渲染为用户级或项目级绝对路径 hooks 的源模板；不声明为插件 hook |
| [`codex/`](codex) | 用户指导、4 个自定义 Agent 和只供审阅的模型/MCP 配置示例 |
| [`skills/init-codex-config`](skills/init-codex-config/SKILL.md) | 通过 `AGENTS.md`、`.codex/hooks.json` 和 `.agents/skills` 配置 Codex 项目 |
| [`skills/agent-config-adapter`](skills/agent-config-adapter/SKILL.md) | 把一套 agent 配置适配到另一个 agent / 模型路由的通用流程 |
| [`scripts/install-codex-local.js`](scripts/install-codex-local.js) | 安装 20 个用户技能、策略安装插件条目、用户 `AGENTS.md` 与 hooks 文件和 4 个自定义 Agents；默认不覆盖不同文件 |
| [`scripts/verify-codex-adapter.js`](scripts/verify-codex-adapter.js) | 与隔离安装器、模型路由、ruff 和 review-gate 测试组合的结构验证 |
| [`scripts/codex-update-safe.js`](scripts/codex-update-safe.js) | 面向 release 资产灰度窗口的 Codex CLI 安全更新器 |
| [`docs/CODEX_ADAPTATION_PLAN.md`](docs/CODEX_ADAPTATION_PLAN.md) | 完整的功能清单、调研笔记、架构选项与执行计划 |
