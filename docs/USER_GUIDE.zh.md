# agent-harness 用户指南

> 这套 harness 提供的每一项能力：它做什么、你怎么调用它、用哪条命令能证明它真的有效，以及它在这台机器上是不是活的。

> **语言：** [English](USER_GUIDE.md) | 中文

## Master TOC

1. [先读这一节：注册、部署、真正触发](#先读这一节注册部署真正触发)
2. [每项能力靠什么运行](#每项能力靠什么运行)
3. [你问到的七项能力](#你问到的七项能力)
4. [本轮新增](#本轮新增)
5. [Rules](#rules)
6. [Skills](#skills)
7. [Hooks](#hooks)
8. [斜杠命令](#斜杠命令)
9. [仓库工具](#仓库工具)
10. [模板、工具链、推荐清单、scaffold](#模板工具链推荐清单scaffold)
11. [这台机器上的部署是怎么回事](#这台机器上的部署是怎么回事)
12. [验证记录](#验证记录)
13. [已知过期文档](#已知过期文档)

除非另有说明，本指南中的每条命令都在仓库根目录下运行。文中引用的每个结果，都是 2026-07-18 在分支 `feat/harness-meta-optimization-2026-07-18` 上真实跑出来的。

## 先读这一节：注册、部署、真正触发

一项能力要经过三个彼此独立的状态。把它们当成一回事，正是这份指南要终结的困惑。

| 状态 | 含义 | 在哪里查 |
|---|---|---|
| 已注册 | 它的路径出现在那份生成所有 agent manifest 的规范清单里。仅凭这一点，运行时什么都不会发生。 | [`adapters/manifest.source.json`](../adapters/manifest.source.json) |
| 已部署 | 文件已经躺在 agent 真正会去读的目录里。 | `~/.claude/skills/`、`~/.claude/hooks/`、`~/.claude/settings.json` |
| 真正触发 | 有东西让它在真实的一轮对话中跑起来。 | 一个 hook 事件、你输入的斜杠命令，或者模型自己决定用它 |

**Skills 和 rules 抵达模型的路径完全不同，而这正是把我们坑了的地方。** Claude Code 会自动发现 `~/.claude/skills/` 下的任何 `SKILL.md`，所以对 skill 来说，已部署确实等于可被发现。rules 没有任何等价机制。[`adapters/claude.mjs`](../adapters/claude.mjs) 这个 Claude 投影器根本不产出 rule 加载器，它自己的注释也这么写着，说 rules 留在 `CLAUDE.md` 里。[`.claude-plugin/plugin.json`](../.claude-plugin/plugin.json) 里的 `rules` 数组是清单元数据，不是运行时导入。一条 rule 只有当它的文本躺在 agent 每轮都会读的文件里才算抵达模型，在这台机器上那个文件是 `~/.claude/CLAUDE.md`。

实际后果是，`design-modes`、`test-first`、`regression-test-on-bugfix`、`incremental-delivery`、`parity-restoration` 和 `commit-discipline` 已注册、已发布、已写进文档好几个月，却一次都没进过 prompt。本轮由 [`bin/rule-activation.mjs`](../bin/rule-activation.mjs) 补上了这个缺口，它把这些 rule 的文本写进 `~/.claude/CLAUDE.md` 中一个可重新生成的托管块。那个块现在已经存在，六条全在里面。

**已部署仍然不保证它会触发。** 一个躺在 `~/.claude/skills/` 里的 skill 是提供给模型的，不是强加给模型的。`code-verifier` 部署了好几个月，而且在 review-gate 的第 4 项审查表里被点名，未经验证的结论照样溜过去了，因为没有任何东西强迫模型去打开它。这就是下面两个状态值的区别，也是这份文档里最值钱的一句话。

## 每项能力靠什么运行

状态这一列只回答一个问题：靠什么让它跑起来。是否活着那一列回答的是另一个问题：这套机制此刻在这台机器上有没有接好。

| 状态 | 含义 |
|---|---|
| `enforced` | 由 hook 事件驱动，模型无法拒绝。如果是阻断式 hook，检查不通过这一轮就结束不了。 |
| `advisory` | 模型读到的文本，或它可以调用的工具。它跑不跑取决于模型自己的选择，或者你亲手输入命令。 |
| `incomplete` | 东西发出来了，但完成它所描述的工作还缺一块，所以它自己做不完那件事。 |

总览如下，细节在后面各节。

| 领域 | 数量 | 状态 | 在这台机器上 |
|---|---|---|---|
| [Rules](#rules) | 27 个目录，其中 26 个已注册 | `advisory` | 26/26 在 `~/.claude/CLAUDE.md` 中可达，已验证。第 27 个 `native-capability-first` 是死的。 |
| [Skills](#skills) | 顶层 23 个，general 桶里另有 11 个，19 个已注册 | `advisory` | 17 个可用裸名字够到，另有 4 个只能用 `agent-harness:<name>`。`doc-writing` 两条路都够不着。 |
| [Hooks](#hooks) | 6 个 | `enforced` | 3 个接进了 `~/.claude/settings.json`。`task-ledger`、`block-env-read`、`typecheck-on-edit` 没有。 |
| [斜杠命令](#斜杠命令) | 2 个 | `advisory` | 两个都通过已启用的 plugin 生效。 |
| [仓库工具](#仓库工具) | `bin/` 与 `scripts/` 下 9 个 | `advisory` | 全部可运行。 |
| [模板与工具链](#模板工具链推荐清单scaffold) | 3 个模板、3 套工具链、20 个推荐清单文件 | `advisory` | 按需阅读。 |

今天唯一能稳定触发的强制路径是 [review-gate](#review-gate)。harness 里其余的一切都是模型可以拒绝的建议，这就是整套系统最诚实的总结。

## 你问到的七项能力

### 1. 两种设计模式

**它做什么。** 给出两种默认取向相反的模式，让一次实质性的构建在开工前先定下自己属于哪一种。prototyping 用高自主度和推迟测试广度换速度；scaling 用受限自主度、小步可审查、完整覆盖换正确性。这条 rule 还覆盖了按子任务混用、中途切换需要的确认，以及一条能力下限规则：能力弱的模型一律走 scaling 模式。

**怎么调用。** 你不调用它。它是 `~/.claude/CLAUDE.md` 里的 rule 文本，每一轮都在模型的上下文里。rule 内部的触发条件是：模型在实质性构建前询问属于哪种模式，或者当你的话已经暗示了其中一种时，直接说出自己的判断。

**怎么测。** 确认文本可达。

```bash
node bin/rule-activation.mjs --check --verbose --agent claude | grep design-modes
```

这台机器上的结果：`ok     design-modes                 matched: managed block`。

**是否活着。** 是，通过本轮写入的托管块生效。正文见 [`rules/design-modes/RULE.md`](../rules/design-modes/RULE.md)，浓缩版见 [`rules/design-modes/snippet.md`](../rules/design-modes/snippet.md)。状态 `advisory`。

### 2. 上下文优化

**它做什么。** 根本没有一个叫上下文优化的工具。这个行为分散在三个互不相干的地方，把这一点直说，比暗示存在一个子系统有用得多。

1. [`rules/output-brevity`](../rules/output-brevity/RULE.md) 削减进入 transcript 的内容。禁止把工具输出复述回去、禁止批次末尾的总结段落，并且优先用 `Edit` 而不是 `Write`，这样穿过上下文的只有一个 diff 而不是整个文件。
2. [`rules/no-reread-files`](../rules/no-reread-files/RULE.md) 阻止同一个文件被读进来两次。只有文件真的变了才重读。
3. [`skills/memory-flywheel`](../skills/memory-flywheel/SKILL.md) 把细节从上下文窗口挪到磁盘上，长 session 可以先丢掉，之后再召回。

overhaul 的第 2 项任务，也就是按需加载与 token 占用度量，只做了设计从未实现。仓库里没有任何东西在度量 token 占用。

**怎么调用。** 两条 rule 作为 rule 文本加载。skill 按名字调用，见下一条。

**怎么测。** 检查两条 rule 是否可达。

```bash
node bin/rule-activation.mjs --check --verbose --agent claude | grep -E "output-brevity|no-reread"
```

结果：`ok     output-brevity` 和 `ok     no-reread-files`，两条都由它们在 `~/.claude/CLAUDE.md` 里自己的标题命中。

**是否活着。** 两条 rule 是活的。度量工具本身不存在，也就无所谓活不活。整体状态 `incomplete`，因为那块能告诉你上下文究竟有没有变小的东西并不存在。

### 3. 跨 session 信息

**它做什么。** [`skills/memory-flywheel/scripts/mem.py`](../skills/memory-flywheel/scripts/mem.py) 把每一轮工作写成一个按项目分目录的纯 Markdown 文件，带 frontmatter，之后按关键词打分召回。它是确定性代码，回路里没有模型，所以召回既便宜又可复现。召回用 IDF（逆文档频率）加权，这样一个在每一轮里都出现的查询词不会淹没排序。

**怎么调用。** `Skill(memory-flywheel)`，或者直接调脚本。四个子命令：`record`、`index`、`recall`、`link`。

**怎么测。** 下面这段只往你传入的临时根目录里写东西。

```bash
mkdir -p /tmp/memdemo
echo "decided to use grep-native files" | python3 skills/memory-flywheel/scripts/mem.py \
  record --root /tmp/memdemo --project demo --kind design \
  --title "Memory layout" --keywords memory,layout
python3 skills/memory-flywheel/scripts/mem.py index  --root /tmp/memdemo --project demo
python3 skills/memory-flywheel/scripts/mem.py recall --root /tmp/memdemo --project demo --query "grep-native"
```

预期输出。`record` 打印它写出的那个 round 文件的路径。`index` 不打印任何东西，只重写 `INDEX.md`。`recall` 打印一行带分数的结果，这次跑出来是 `0.001` 后面跟着 `0001-design.md` 的路径。完整测试是 `python3 skills/memory-flywheel/scripts/test_mem.py`，报告 `mem.py: all 11 tests PASS`。

**是否活着。** 是，作为 skill 可被发现。有一个注意点写在[部署那一节](#这台机器上的部署是怎么回事)：已部署的那份是指向另一个 clone 的符号链接，不是这个 checkout。状态 `advisory`。

### 4. 多粒度文档记忆

**它做什么。** 还是同一个 skill，只是分两层来读。粗粒度层是 `INDEX.md`，每一轮一行表格，含 id、kind、title 和关键词。细粒度层是 `rounds/NNNN-<kind>.md`，每一轮一个文件，装着逐字正文。阅读协议是先打开索引，再只打开召回指向的那几个 round 文件，这样一段很长的历史只花一张小表的代价，而不是每个文件都读。

**怎么调用。** 同一个 skill。`index` 重建粗粒度层，`recall` 挑出该打开哪些细粒度文件。

**怎么测。** 接着上一条的测试，把两层读出来。

```bash
cat /tmp/memdemo/demo/INDEX.md
cat /tmp/memdemo/demo/rounds/0001-design.md
```

预期输出。`INDEX.md` 里有标题 `# Memory index — demo`、一行 `1 round(s). Read this coarse layer first; open only the round files recall points at.`，以及一张四列表格，唯一一行是 `| 0001 | design | Memory layout | memory, layout |`。round 文件里是含 `id`、`kind`、`title`、`ts`、`keywords` 的 frontmatter，然后是逐字正文。这两层都是上面那次运行产生的。

**是否活着。** 是，同上一条。状态 `advisory`。

### 5. 自适应工具

**它做什么。** [`skills/agent-update-watcher`](../skills/agent-update-watcher/SKILL.md) 把一份被监视源的列表和你上次记录的版本做对比，只打印真正变了的那些，并用一个最小间隔做保护，所以重复运行几乎不花钱。

**它无法自驱，这是你依赖它之前必须先搞清楚的局限。** 这个 skill 有 diff 引擎，没有抓取器。它不联网。每个源的最新版本必须以 `--snapshot` 文件的形式喂给它，而那段把每个被监视 URL 变成 snapshot 的代码被有意留给调用方，且从未写出来。仓库里没有任何东西去抓它，也没有定时器去跑它。所以它是一个你手动驱动的比较器，不是一个会自己盯着的 watcher。

**怎么调用。** `Skill(agent-update-watcher)`，或者直接用配置、状态文件和 snapshot 调脚本。

**怎么测。** 下面这段同时验证 diff 和间隔保护。

```bash
cp skills/agent-update-watcher/scripts/sources.example.json /tmp/sources.json
printf '{"claude-code":"99.99.99","codex":"99.99.99","opencode":"99.99.99"}' > /tmp/latest.json
python3 skills/agent-update-watcher/scripts/check_updates.py \
  --config /tmp/sources.json --state /tmp/state.json --snapshot /tmp/latest.json --min-interval-days 7
python3 skills/agent-update-watcher/scripts/check_updates.py \
  --config /tmp/sources.json --state /tmp/state.json --snapshot /tmp/latest.json --min-interval-days 7
```

预期输出。第一次运行打印 `[agent-update-watcher] 3 update(s) of 3 source(s).`，后面跟三行以 `UPDATE` 开头的制表符分隔行。第二次运行打印 `[agent-update-watcher] skipped: checked 0d ago (< 7d). Use --force to override.`。两者都实际观察到了。单元测试 `python3 skills/agent-update-watcher/scripts/test_check_updates.py` 报告 `check_updates.py: all 6 tests PASS`。

**是否活着。** skill 可被发现，比较器能跑。作为一项完整能力，状态是 `incomplete`，因为让它变得自适应的那个抓取器并不存在。

### 6. 自动 plugin 策展

**这个东西不存在。** 没有任何工具、脚本、hook 或 skill 在做 plugin 策展。

这个说法来自 [`docs/OVERHAUL_DELIVERY.md`](OVERHAUL_DELIVERY.md) 的第 7 行，写着 `Plugin hygiene | rename leftovers, dead-knob templates, malformed-YAML fixes`。那是 overhaul 期间的三次一次性手工修改，不是一项还会再跑的能力。在这一点上，[`docs/strategy/agent-harness-overhaul-2026-07-09/STATUS.md`](strategy/agent-harness-overhaul-2026-07-09/STATUS.md) 反而更准确，它把第 7 项标为部分完成，并明确写出周期性清理工具尚未落地。

最接近的现存物是 [`recommendations/cc-plugins.md`](../recommendations/cc-plugins.md)，一份手工维护、没有任何自动化的 plugin 清单，以及 `rules/plugin-preflight`，它要求模型在调用某个 plugin 前先确认它已安装且未废弃。两者都不做策展。

**怎么测。** 诚实的测试是两次搜索都什么也搜不到。第一条找的是有没有发布任何名字与 plugin 或策展相关的东西，第二条在已注册清单里找同样的东西。

```bash
ls bin scripts hooks skills commands | grep -i "plugin\|curat"
grep -io "plugin[a-z-]*curation\|curate-plugins\|plugin-hygiene" \
  adapters/manifest.source.json .claude-plugin/plugin.json
```

这台机器上的结果：两条都无输出、退出码 1。单纯搜 `curate` 这个词不是有效的测试，因为它会命中 prompt library 的文档字符串，那里策展的是 prompt 而不是 plugin。状态 `incomplete`，意思是这个功能被描述过，但从未被构建。

### 7. TUI（terminal user interface，终端用户界面）工具推荐

**它做什么。** 这是七项里唯一一项端到端做完的。[`recommendations/tui-for-agents.md`](../recommendations/tui-for-agents.md) 是那份调研，面向完整编辑器会崩溃的机器，覆盖并发 session、子 agent 切换、diff 审查和批准或拒绝流程，并对每条论断标注了已核实或未核实。[`skills/tui-installer`](../skills/tui-installer/SKILL.md) 把这份调研变成一个针对四个工具的安装器：`zellij`、`claude-squad`、`lazygit`、`delta`。默认是 dry run，`--apply` 会逐个工具问你 yes 或 no，没有干净安装包的工具会被标为 manual 并给出上游 URL，而不是编一条命令出来。

**怎么调用。** `Skill(tui-installer)`，或者直接调脚本。调研文件用任何阅读器打开即可。

**怎么测。** 只读，不安装任何东西。

```bash
bash skills/tui-installer/scripts/install-tui.sh --check
```

在四个工具都没装的机器上的预期输出：四行各以 `MISSING` 开头，然后是 `4 of 4 recommended tools missing.`。这台机器打印的正是这个，也就是说这套栈被推荐了但还没装。单元测试 `bash skills/tui-installer/scripts/test_install_tui.sh` 报告 `install-tui.sh: all 11 checks PASS`。

**是否活着。** 是，作为 skill 可被发现，推荐文件也可读。状态 `advisory`，功能完整。

## 本轮新增

### rules/native-capability-first

**它做什么。** 在其他每一项 harness 功能之前放一道三问适配检查：对这种任务形态它是必要的吗、照做会不会比不用它更糟、以及到底哪边更强。它列出了永不豁免的情形：验证闸门、阻断式 hook、隐私处理、破坏性确认，以及你自己的指令。当模型跳过某项功能时，它要提交一条反馈记录，而不是默默跳过。

**怎么调用。** rule 文本，和其他 rule 一样。

**怎么测。**

```bash
node bin/rule-activation.mjs --check --verbose --agent claude | grep -c native-capability
```

这台机器上的结果：`0`。**这条 rule 是死的。** 它不在已注册清单里，所以 `rule-activation.mjs` 从不考虑它，也就没有任何东西把它写进 `~/.claude/CLAUDE.md`。注册工作由本指南之外的人负责。文件是 [`rules/native-capability-first/RULE.md`](../rules/native-capability-first/RULE.md) 和 [`rules/native-capability-first/snippet.md`](../rules/native-capability-first/snippet.md)。在它被注册、并且有一次 `--apply` 把它收进去之前，状态是 `incomplete`。

### hooks/task-ledger

**它做什么。** 每一轮工作对应一个 Markdown 文档，只要里面还有没做完的事，就拒绝让这一轮结束。`UserPromptSubmit` 上的 `capture.sh` 把每一条轮次中途的 prompt 追加进 inbox，赶在模型忘掉它之前。`Stop` 上的 `gate.sh` 会在还有任务未关闭、有任务被标记完成却没有证据、或有 inbox 条目未分诊时阻断。`ledger.py` 读写这个文档，还负责生成子 agent 的 brief，这样一次交接是生成出来的而不是回忆出来的。把任务标记完成必须给 `--evidence`，阻塞或丢弃必须给 `--reason`。

**怎么调用。** 装好之后，两个 hook 在上述事件上触发。命令行是 `python3 hooks/task-ledger/scripts/ledger.py <subcommand>`，子命令有 `open`、`add`、`inbox`、`triage`、`start`、`done`、`block`、`drop`、`status`、`check`、`approvals`、`brief`、`view`、`close`。

**怎么测。**

```bash
python3 hooks/task-ledger/scripts/ledger.py status
npm run test:task-ledger
```

预期输出。`status` 为当前活动轮次打印一行。这台机器打印的是 `Harness meta optimization — 8/16 settled · 8 todo`，后面跟着未关闭任务列表，读的是 [`.agent/ledger/`](../.agent/ledger) 里的实时账本。测试脚本在 16 个 Python 测试之后报告 `task-ledger hooks: all 11 tests PASS`。

**是否活着。** 文档和命令行是好用的。**但两个 hook 没有安装**，所以没有任何东西因为账本而阻断。`~/.claude/hooks/` 里只有 `review-gate`、它的一份备份，以及 ssh-guard 的状态目录。安装的方式是把三个脚本拷过去，再把 [`hooks/task-ledger/settings.snippet.json`](../hooks/task-ledger/settings.snippet.json) 合并进 `~/.claude/settings.json`，步骤见 [`hooks/task-ledger/README.md`](../hooks/task-ledger/README.md)。状态：设计上是 `enforced`，但没活。

### `bin/rule-activation.mjs`

**它做什么。** 报告哪些已注册的 rule 实际能抵达每个 agent，并把抵达不了的那些写进一个由起止注释标记界定的托管块。检测刻意做得宽松，用 rule 名字或它 snippet 的标题去匹配文件，因为 `~/.claude/CLAUDE.md` 是你手工维护的，重复一条你已经写过的 rule 会在每一轮都花掉 token。那些你已经用自己的话覆盖过的 rule 放进一个 ignore 文件，这样检测器漏掉它是预期行为，而不是永远重复报错。

**怎么调用。**

```bash
node bin/rule-activation.mjs --check                  # 报告，有 rule 是死的就退出码 1
node bin/rule-activation.mjs --check --verbose        # 逐条给出命中证据
node bin/rule-activation.mjs --apply --dry-run        # 只显示块内容，不写
node bin/rule-activation.mjs --apply --agent claude   # 真的写进去
```

**怎么测。**

```bash
node bin/rule-activation.mjs --check
npm run test:rule-activation
```

预期输出。检查会为每个 agent 打印一段。这台机器上 claude 对 `~/.claude/CLAUDE.md` 打印 `26/26 rules reachable`，codex 对 `~/.codex/AGENTS.md` 相同，opencode 则是 `loads every rule via instructions glob; nothing to write`，最后 `all registered rules are reachable`，退出码 0。opencode 那一行是真实情况而不是特例，因为它的配置声明了一个覆盖所有 rule 文件的 instructions glob。测试脚本报告 `rule-activation.mjs: all 26 checks PASS`。

**是否活着。** 是。托管块已在 `~/.claude/CLAUDE.md` 里，装着 `test-first`、`design-modes`、`regression-test-on-bugfix`、`incremental-delivery`、`parity-restoration` 和 `commit-discipline`。状态 `advisory`，因为要你去跑它，但它的产出才是 rules 能被加载的原因。

### `bin/harness-feedback.mjs`

**它做什么。** 这是 `native-capability-first` 打开的那个回路的写入端。当某项 harness 功能不合用时，它往队列文件里追加一条结构化记录，让这次不匹配被记下来而不是被无声吸收。三种判定：`native-better` 意思是收窄触发条件或退役它，`needs-update` 意思是原则对细节过时，`missing-capability` 意思是 harness 应该收进来某样它还没有的东西。`/harness-sync` 是读取端，负责把队列排干成真正的修改。

**怎么调用。**

```bash
node bin/harness-feedback.mjs --feature rules/phased-planning --verdict native-better \
  --why "forced a 3-phase plan onto a one-line fix" \
  --proposal "narrow the trigger to 3+ files AND 5+ tool calls"
node bin/harness-feedback.mjs --list
node bin/harness-feedback.mjs --list --all
```

**怎么测。** 读取路径直接对着仓库跑是安全的。

```bash
node bin/harness-feedback.mjs --list
npm run test:harness-feedback
```

预期输出。`--list` 打印了 `no open entries`，这是对的，因为 `docs/harness-feedback/QUEUE.md` 还没被创建。测试脚本报告 `harness-feedback.mjs: all 9 tests PASS`。写入路径另外用脚本的一份临时副本验证过，它写出了带头部、判定表和一条记录的队列文件，随后列出为 `open     native-better       rules/phased-planning`。非法判定会被拒绝，提示 `--verdict must be one of: native-better, needs-update, missing-capability`。

**是否活着。** 作为脚本是活的。没有任何东西自动调用它，而本该提示模型去调用它的那条 rule 正是上面那条死的。状态 `advisory`。

### skills/doc-writing

**它做什么。** 把从两个真实项目 session 里挖出来的文档偏好编码下来，262 条 prompt 归纳成 102 条逐字偏好和 48 条合并规则，按文档类型组织。它附带 [`scripts/doccheck.py`](../skills/doc-writing/scripts/doccheck.py)，一个针对机器可检查子集的 linter：泄漏的密钥、本该是链接的裸引用、未定义的术语、缺失的图、缺失的必需章节、渲染不出来的表格和列表、过期标记，以及超过三项还在用短横线的平铺列表。按类型的必需章节和缩写白名单放在 [`doccheck.config.json`](../skills/doc-writing/doccheck.config.json) 里，改它不用碰脚本。

**怎么调用。** 部署之后用 `Skill(doc-writing)`。linter 今天已经可以独立运行。

**怎么测。**

```bash
python3 skills/doc-writing/scripts/doccheck.py docs/USER_GUIDE.md --type readme
python3 skills/doc-writing/scripts/test_doccheck.py
```

预期输出。linter 每条发现打印一行，含级别、检查名、规则 id 和行号，最后是汇总；干净时退出码 0，有警告 1，有错误 2。测试脚本报告 `doccheck.py: 20/20 tests PASS`。

**是否活着。** **这个 skill 走哪条路都发现不了。** 它不在已注册清单里，所以部署器不会把它放进 `~/.claude/skills/`；它在 plugin 提供的那个 clone 里也不存在，所以 `agent-harness:doc-writing` 这种写法同样解析不出来。它不会出现在 session 的 skill 目录中。按路径调用 linter 是好用的。状态 `advisory`，没活。

### skills/prompt-library 及其挖掘出的语料

**它做什么。** 把可复用的 prompt 策展成可 grep 的 Markdown，每条都带原文、优化改写，以及一段何时不要用它的说明，判断力就住在那一段里。一道隐私闸门会拒绝存入任何还带着路径、邮箱、token、用户名或代号的内容，好让这个库保持可公开。`plib_mine.py` 是本轮新增的，负责从本地 session 历史里抽取 prompt。挖掘出的语料落在 [`recommendations/prompt-library/`](../recommendations/prompt-library/)，18 条记录加一份索引，覆盖功能规格、skill 编写、文档、部署、数据平台工作、研究设计、bug 分诊、报告和提案写作。

**怎么调用。** `Skill(prompt-library)`，或者用脚本的 `scan`、`add`、`index`、`find`、`mine`。

**怎么测。**

```bash
python3 skills/prompt-library/scripts/plib.py find --query "documentation audit"
python3 skills/prompt-library/scripts/test_plib.py
```

预期输出。`find` 按分数从高到低打印路径。这台机器返回四条命中，最高的是分数 `9` 的 `documentation-completeness-audit-and-backlog-consolidation.md`。测试脚本报告 `plib.py + plib_mine.py: all 24 tests PASS`。

**是否活着。** skill 可被发现，但有一个缺口。`--root` 默认是相对工作目录解析的 `recommendations/prompt-library`，而已部署 skill 指向的那个 clone 里没有这个目录，所以只有在这个 checkout 下运行时默认值才解析得出来。从别处运行时要显式传 `--root`。状态 `advisory`。

### `hooks/review-gate/scripts/statsbar.sh`

**它做什么。** 把一份计数拆解渲染成对齐的彩色条，这样一条报告 12 个文件、10 个干净、1 个已修、1 个待修的审查是一眼看懂的，而不是当句子去解析。两种输出格式，因为这些数字会在两个地方被读。终端上默认 `ansi`，给 Markdown 阅读器的是 `md`，一个等宽围栏块，颜色由 emoji 承担，因为转义码在阅读器里会变成一堆乱字符。`NO_COLOR` 强制无转义输出。它是共享渲染器，所以 review-gate、task-ledger 以及别的任何东西报出来的形状是一致的。

**怎么调用。**

```bash
bash hooks/review-gate/scripts/statsbar.sh --title "review-gate" --unit files --total 12 \
  --stat "OK:10:green" --stat "fixed:1:yellow" --stat "open:1:red"
```

颜色可选 `green`、`yellow`、`red`、`blue`、`grey`，省略颜色即为 grey。省略 `--total` 则取各项之和。

**怎么测。**

```bash
bash hooks/review-gate/scripts/statsbar.sh --help
bash hooks/review-gate/scripts/test_statsbar.sh
```

预期输出。`--help` 打印文件头部注释块，包含两个格式名和用法示例。测试脚本报告 `statsbar.sh: all 20 checks PASS`。

**是否活着。** 是。它已部署在 `~/.claude/hooks/review-gate/statsbar.sh`，与分支上的副本逐字节一致。状态 `advisory`；它被引用在 review-gate 的 brief 里，从而推动模型去生成这个条形图而不是手画一个。

### review-gate 的 brief 文件

**它做什么。** Claude Code 会把 Stop hook 的 reason 字符串原样渲染到你的终端。那份审查 brief 大约三 KB，是给模型的指令而不是给你的消息，而它此前在每一个改动代码的轮次都被倒进你的终端。现在 `core.sh` 把 brief 写进文件、只返回一个简短指针，显示出来的就是那个指针。文件路径由 `gate.sh` 以 `RG_BRIEF_FILE` 传入，落在 `~/.claude/review-state/` 下，按 session id 命名。

同一次修改里还有另外三处变化。改动文件清单改成一行一个路径而不是空格拼接，因为路径里一旦含空格，空格拼接的清单就再也切不开了，而这个 checkout 正好住在一个名字带空格的目录下。审查正文现在是 Markdown 表格而不是散装 bullet，任何超过一个短句的内容都被推到表格下面的编号注释里。brief 现在还要求把计数做成一个由 `statsbar.sh` 生成的条形图。

**怎么测。**

```bash
npm run test:review-gate-core
grep -n "RG_BRIEF_FILE" hooks/review-gate/scripts/gate.sh
```

预期输出。测试脚本报告 `core.sh: all 22 checks PASS`。grep 返回 `gate.sh` 里说明并设置这个变量的两行。

**是否活着。** 是。`~/.claude/hooks/review-gate/` 下的 `core.sh`、`gate.sh`、`track.sh`、`statsbar.sh` 与分支副本逐字节一致。`precommit.sh` 不一致，且已部署的那份更新，带着本分支切出之后才落到 `main` 上的 ssh-guard 工作。状态 `enforced`。

## Rules

27 个 rule 目录，其中 26 个已注册。所有 rule 本质上都是 `advisory`，因为一条 rule 是靠说服的文本，不是靠强制的机制。有差别的是这段文本到底有没有抵达模型。

完整描述在 [`rules/README.md`](../rules/README.md) 和 [`INVENTORY.md`](../INVENTORY.md) 的逐条表格里。这一节只讲一条 rule 如何抵达模型、以及你怎么检查，因为这一部分没有别的文档写过。

存在三条路径，每个 agent 恰好走其中一条。

1. **Claude Code** 读 `~/.claude/CLAUDE.md`。一条 rule 出现在那里，要么是你自己写的，要么是 `rule-activation.mjs --apply` 放进托管块的，要么是被列在 ignore 文件里、表示你已用自己的话覆盖过。
2. **Codex** 以同样机制读 `~/.codex/AGENTS.md`。
3. **opencode** 在 [`opencode.json`](../opencode.json) 里声明了一个覆盖所有 rule 文件的 instructions glob，所以它全部加载，不需要托管块。

三者共用一条测试命令。

```bash
node bin/rule-activation.mjs --check --verbose
```

预期输出：每个 agent 一段，最后是 `all registered rules are reachable`，退出码 0。失败时会逐条列出不可达的 rule 并以 1 退出。这台机器上的当前状态，已验证。

| Agent | 目标文件 | 可达 | 说明 |
|---|---|---|---|
| claude | `~/.claude/CLAUDE.md` | 26/26 | 19 条由你自己的标题命中，6 条由托管块命中，1 条由 ignore 文件命中 |
| codex | `~/.codex/AGENTS.md` | 26/26 | 机制相同 |
| opencode | [`opencode.json`](../opencode.json) | 26/26 | instructions glob，无需写入 |

唯一在这幅图之外的是 `native-capability-first`，它没有注册，因此在任何地方都不可达。见[上面那一条](#rulesnative-capability-first)。

ignore 文件位于 `~/.claude/agent-harness-rule-activation.ignore`，目前只有一条 `root-cause-before-fix`，因为你自己的代码变更工程原则已经用另一套措辞承载了完整的七步流程。

## Skills

顶层 23 个 skill 目录，general 桶里另有 11 个，19 个已注册。每个 skill 都是 `advisory`。Claude Code 把发现到的 skill 提供给模型，用不用由模型决定。

**两层布局。** 一个同时出现在 `skills/<name>/` 和 `skills/general/<name>/` 的名字并不是重复。general 桶里是规范版本，顶层那个文件是一层很薄的 Codex 包装，它告诉 Codex 去读规范版本，然后按 Codex 的约定做适配。对比 [`skills/verify-template/SKILL.md`](../skills/verify-template/SKILL.md) 的 991 字节和 [`skills/general/verify-template/SKILL.md`](../skills/general/verify-template/SKILL.md) 的 2168 字节就能看出这个模式。

**怎么调用任意 skill。** 用 `Skill` 工具，部署在 `~/.claude/skills/` 下的用裸名字，由已启用 plugin 提供的用 `agent-harness:<name>` 形式。有几个 skill 两条路都通。

**怎么测一个 skill 是不是活的。**

```bash
ls ~/.claude/skills/ | grep -x doc-writing || echo "not deployed"
node bin/deploy-skills.mjs                     # dry run，显示每个 skill 的计划
node bin/deploy-skills.mjs --apply             # 真的写符号链接
```

当前部署状态，由 dry run 验证。它报告 `plan: link=4 relink=30 ok=0 kept=4 nosrc=0`，意思是 4 个目标不存在，30 个存在但指向仓库的另一份副本，4 个是真实目录、部署器不会去动，因为那是你自己的独立版本。

下面是有可运行行为的那些 skill 的逐项状态。每条测试命令都真跑过，每个结果都是真实结果。

| Skill | 测试命令 | 结果 | 是否活着 |
|---|---|---|---|
| [`memory-flywheel`](../skills/memory-flywheel/SKILL.md) | `python3 skills/memory-flywheel/scripts/test_mem.py` | `all 11 tests PASS` | 是 |
| [`memory-flywheel`](../skills/memory-flywheel/SKILL.md) 评测器 | `python3 skills/memory-flywheel/scripts/test_mem_eval.py` | `all 3 tests PASS` | 是 |
| [`memory-flywheel`](../skills/memory-flywheel/SKILL.md) 自动记录 hook | `python3 skills/memory-flywheel/scripts/test_supervise.py` | `all 7 checks PASS` | 只有脚本，hook 未安装且默认关闭 |
| [`prompt-library`](../skills/prompt-library/SKILL.md) | `python3 skills/prompt-library/scripts/test_plib.py` | `all 24 tests PASS` | 是，注意 `--root` 那个缺口 |
| [`agent-update-watcher`](../skills/agent-update-watcher/SKILL.md) | `python3 skills/agent-update-watcher/scripts/test_check_updates.py` | `all 6 tests PASS` | 是，但没有抓取器 |
| [`tui-installer`](../skills/tui-installer/SKILL.md) | `bash skills/tui-installer/scripts/test_install_tui.sh` | `all 11 checks PASS` | 是 |
| [`task-relationship-analysis`](../skills/task-relationship-analysis/SKILL.md) | `python3 skills/task-relationship-analysis/scripts/test_scaffold.py` | `all 6 tests PASS` | 是 |
| [`doc-writing`](../skills/doc-writing/SKILL.md) | `python3 skills/doc-writing/scripts/test_doccheck.py` | `20/20 tests PASS` | 否，未部署也未注册 |
| [`figma-design-fetch`](../skills/figma-design-fetch/SKILL.md) | `node skills/figma-design-fetch/scripts/test_visual_diff.mjs` | 未运行，需要 pixelmatch 依赖 | 作为 skill 是活的 |

其余 skill 只有文字，没有可执行脚本，包括 `code-verifier`、`research-critic`、`verify-template`、`preview-template`、`verify-visual`、`privacy-redact`、`long-running-tasks`、`figma-authoring-constraints`、`task-orchestrator`、`end-of-turn-marker`、`agent-config-adapter` 和 `init-codex-config`。对它们来说，测试就是模型能不能找到它们，方法是列一下 `~/.claude/skills/`，或者在 session 里按名字点它。

顶层有五个 skill 没有注册，所以 `deploy-skills.mjs` 从不把它们放进 `~/.claude/skills/`，它们都不能用裸名字够到。其中四个仍然走另一条路抵达，因为已启用的 plugin 提供的是那个 clone 的整个 skill 目录，所以 `task-orchestrator`、`end-of-turn-marker`、`agent-config-adapter` 和 `init-codex-config` 都可以用 `agent-harness:<name>` 调用。`doc-writing` 是例外，它在那个 clone 里也不存在，所以两条路都够不着它。

**`code-verifier` 处在什么位置，因为它是 advisory 最尖锐的例子。** 它已部署，而且是真实目录而不是符号链接，因为那是你自己的独立副本，并且它在 review-gate 的第 4 项审查表里被点名。这些都不能让它跑起来。harness 里没有任何东西会因为你没打开它而阻断一句完成声明。把一个已部署的验证 skill 当成保证，正是这份指南要避免的错误。

## Hooks

6 个 hook 目录。hooks 是 harness 里唯一的 `enforced` 机制，而这台机器上六个里只有三个接进了 `~/.claude/settings.json`。

**怎么查到底接了哪些。**

```bash
python3 -c "import json,os;d=json.load(open(os.path.expanduser('~/.claude/settings.json')));print(json.dumps(d['hooks'],indent=1))"
```

那个文件此刻已验证的状态如下。

| Hook | 事件 | Matcher | 这里接了吗 | 状态 |
|---|---|---|---|---|
| [`review-gate`](../hooks/review-gate/README.md) 追踪器 | `PostToolUse` | `Write\|Edit` | 是，调用 `track.sh` | `enforced` |
| [`review-gate`](../hooks/review-gate/README.md) 提交守卫 | `PreToolUse` | `Bash` | 是，调用 `precommit.sh` | `enforced` |
| [`review-gate`](../hooks/review-gate/README.md) 停止闸门 | `Stop` | 全部 | 是，调用 `gate.sh` | `enforced` |
| [`ruff-format-on-edit`](../hooks/ruff-format-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | 是，内联命令而非脚本文件 | `enforced` |
| [`jq-validate-json`](../hooks/jq-validate-json/README.md) | `PostToolUse` | `Write\|Edit` | 是，内联命令 | `enforced` |
| [`block-env-read`](../hooks/block-env-read/README.md) | `PreToolUse` | `Read` | 否 | 设计上 `enforced`，没活 |
| [`typecheck-on-edit`](../hooks/typecheck-on-edit/README.md) | `PostToolUse` | `Write\|Edit` | 否 | 设计上 `enforced`，没活 |
| [`task-ledger`](../hooks/task-ledger/README.md) 捕获 | `UserPromptSubmit` | 全部 | 否 | 设计上 `enforced`，没活 |
| [`task-ledger`](../hooks/task-ledger/README.md) 轮次闸门 | `Stop` | 全部 | 否 | 设计上 `enforced`，没活 |

那个文件里还有两条来自本分支之外。`PreToolUse` 上的 `ssh-guard` 是本分支切出之后加到 `main` 上的，它是活的。`SessionStart` 上的 autopilot 会话检查来自 autopilot skill。

### review-gate

**它做什么。** 追踪一轮改了哪些文件，然后在 `Stop` 时返回一份审查 brief，并阻断本轮结束直到完成一轮审查。brief 列出编号的审查表，覆盖正确性、最小改动、模块化、假运行检测、提交与文档卫生、对抗性输入，以及当这一轮修了 bug 时的红转绿回归测试。有小模块变更时会追加逐函数审查。它还通过 `Bash` 上的 `PreToolUse` matcher 守卫 `git commit` 和 `git push`。

**怎么调用。** 你不调用。任何改动代码的轮次在 `Stop` 时它都会触发。

**怎么测。**

```bash
npm run test:review-gate-core
bash hooks/review-gate/scripts/test_precommit.sh
cat ~/.claude/hooks/review-gate/review-gate.conf
```

预期输出。`core.sh: all 22 checks PASS` 和 `precommit.sh: all 22 tests PASS`。这台机器上的配置文件内容是 `block_commit=0` 和 `stop_mode=block`。

**两个值得知道的设置。** `stop_mode=block` 是默认值，也正是它让审查无法回避，代价是较新版本的 Claude Code 会把这一轮标成 stop hook 错误。这个标签只是外观问题，审查照样跑。`stop_mode=feedback` 能拿到干净的标签，但审查会变成可跳过的，也就是变成 advisory。不存在既阻断又避开这个标签的输出方式。`block_commit=0` 让 `git commit` 自由通过，而 `git push` 仍受守卫。

**跨 agent。** 审查逻辑集中在一份共享的 `core.sh` 里，外面套薄薄的按 agent 的 shim，所以 Claude Code、Codex 和 opencode 跑的是同一套审查。Codex 的 shim 是 [`scripts/codex_review_gate.sh`](../scripts/codex_review_gate.sh)，opencode 的在 [`.opencode/plugin/`](../.opencode/plugin) 下。测试用 `bash scripts/test_codex_review_gate.sh` 和 `npm run test:opencode-review`，后者报告 `opencode review helper: all 6 checks PASS`。

### 另外五个 hook

每个都自带 README，里面有安装片段，并且每个都有测试。

| Hook | 它做什么 | 测试命令 | 结果 |
|---|---|---|---|
| [`ruff-format-on-edit`](../hooks/ruff-format-on-edit/README.md) | 模型写完 Python 文件后跑 ruff format 和 ruff check | `bash scripts/test_codex_ruff_format_on_edit.sh` | 通过，作为 `npm run verify:codex` 的一部分 |
| [`jq-validate-json`](../hooks/jq-validate-json/README.md) | 如果往配置的路径写入了非法 JSON，阻断下一次工具调用 | 由 `~/.claude/settings.json` 里的内联命令承载 | 已接入且活着 |
| [`block-env-read`](../hooks/block-env-read/README.md) | 拒绝读取任何 `.env` 文件，让密钥进不了 transcript | `bash hooks/block-env-read/test_block_env.sh` | `block-env.sh: all 12 checks PASS` |
| [`typecheck-on-edit`](../hooks/typecheck-on-edit/README.md) | TypeScript 编辑后跑 prettier 再跑不产出的类型检查，类型错误会阻断本轮 | `bash hooks/typecheck-on-edit/test_typecheck.sh` | 未运行，需要 TypeScript 工具链 |
| [`task-ledger`](../hooks/task-ledger/README.md) | 拒绝在还有未完成任务时结束一轮 | `npm run test:task-ledger` | 16 个 Python 测试之后 `all 11 tests PASS` |

## 斜杠命令

两个命令，都是 `advisory`，因为要你输入，并且都通过已启用的 plugin 生效。

| 命令 | 它做什么 | 测试 |
|---|---|---|
| `/harness-sync` | 更新 agent-harness、展示改了什么、推荐与当前任务相关的部分、应用前先问你，并在不重启的情况下让最新 rules 在当前 session 生效。它同时是 harness 反馈队列的读取端。 | 在 session 里输入 `/harness-sync`，或读 [`commands/harness-sync.md`](../commands/harness-sync.md) |
| `/figma-fetch` | 通过 Figma MCP 把一个 Figma 设计节点，也就是它的代码、素材和截图，取进一个被 gitignore 的导入目录。 | 输入 `/figma-fetch <node-url>`，或读 [`commands/figma-fetch.md`](../commands/figma-fetch.md) |

要确认两个命令都随 plugin 注册了，检查 `~/.claude/settings.json` 的 `enabledPlugins` 里 `agent-harness` 是启用状态。它是启用的，来源是一个指向下面所说那个 clone 的本地目录 marketplace。

## 仓库工具

[`bin/`](../bin) 和 [`scripts/`](../scripts) 下共 9 个工具。全部是 `advisory`，意思是要你或模型去跑，尽管其中两个正是让别的东西能工作的前提。

| 工具 | 它做什么 | 调用 | 测试 | 结果 |
|---|---|---|---|---|
| [`bin/rule-activation.mjs`](../bin/rule-activation.mjs) | 报告并修复已注册但失效的 rule | `node bin/rule-activation.mjs --check` | `npm run test:rule-activation` | `all 26 checks PASS` |
| [`bin/harness-feedback.mjs`](../bin/harness-feedback.mjs) | 记录一项不合用的 harness 功能 | `node bin/harness-feedback.mjs --list` | `npm run test:harness-feedback` | `all 9 tests PASS` |
| [`bin/deploy-skills.mjs`](../bin/deploy-skills.mjs) | 把每个已注册 skill 符号链接进各 agent 的全局 skill 目录，只增不覆盖，默认 dry run | `node bin/deploy-skills.mjs --apply` | `npm run test:deploy-skills` | `all 9 checks PASS` |
| [`build.mjs`](../build.mjs) | 从唯一的规范源重新生成三个 agent 的 manifest | `node build.mjs` | `npm run check:manifests` | `check OK: all manifests match source` |
| [`adapters/test-projection.mjs`](../adapters/test-projection.mjs) | 源清单与各生成 manifest 之间的逐字节一致性闸门 | `npm run test:projection` | 同左 | `all 3 parity test(s) PASS` |
| [`scripts/resolve_model.mjs`](../scripts/resolve_model.mjs) | 按 agent 与任务档位解析模型 id | `node scripts/resolve_model.mjs claude research` | `npm run test:models` | `all 31 checks PASS`，上述调用返回 `claude-opus-4-8` |
| [`scripts/install-codex-local.js`](../scripts/install-codex-local.js) | 往 Codex 安装 20 个用户 skill、plugin 条目、用户指令、hooks 和四个自定义 agent 档案 | `npm run install:codex` | `npm run test:codex-install` | `isolated 20-skill/user-surface install PASS` |
| [`scripts/verify-codex-adapter.js`](../scripts/verify-codex-adapter.js) | 对整个 Codex adapter 做结构性检查 | `npm run verify:codex` | 同左 | 一并跑安装器、模型、ruff 和 review-gate 测试 |
| [`scripts/codex-update-safe.js`](../scripts/codex-update-safe.js) | 面向发布资产灰度窗口的 Codex 安全更新器 | `npm run update:codex` | 无专门测试 | 未验证 |

还有两个脚本，[`scripts/actions-budget.mjs`](../scripts/actions-budget.mjs) 和 [`templates/actions-frugal-ci/`](../templates/actions-frugal-ci) 下的工作流模板，与本轮同期落地，但归属另一条工作线，本文不做记录。`node scripts/actions-budget.mjs --help` 描述的是一个对磁盘上 `.github/workflows` 的离线预算检查，报告哪些工作流会在 pull request、合并和定时上触发、各自扇出多大，以及计费分钟数下限。

**一条把所有测试跑完的命令。**

```bash
for t in check:manifests test:projection test:opencode-review test:deploy-skills \
         test:rule-activation test:models test:codex-install test:harness-feedback \
         test:task-ledger test:review-gate-core; do npm run --silent $t >/dev/null 2>&1 \
  && echo "PASS $t" || echo "FAIL $t"; done
```

2026-07-18 在这台机器上十条全部打印 pass。

## 模板、工具链、推荐清单、scaffold

全部 `advisory`。这些东西是被读或被拷贝的，从不对你强制执行。

| 领域 | 内容 | 位置 |
|---|---|---|
| 模板 | 一个用 uv、ruff、pytest 的 Python 研究包；一个带国际化的静态学术个人站；一套节俭的持续集成工作流 | [`templates/README.md`](../templates/README.md) |
| 工具链 | uv 加 ruff 的 Python、nvm 的 Node，以及一份权限白名单片段 | [`tooling/README.md`](../tooling/README.md) |
| 推荐清单 | 20 个文件，覆盖 plugin、marketplace、命令行工具、UI 与动画库、审计、文档、机器学习研究、集群模式、参考项目和终端栈 | [`recommendations/README.md`](../recommendations/README.md) |
| scaffold | 把上面这些的正确子集组合进一个项目的交互式脚手架 | [`setup/init-agent-config/SKILL.md`](../setup/init-agent-config/SKILL.md) |

脚手架用 `/init-agent-config` 或 `Skill(init-agent-config)` 调用。它会问项目类型、语言偏好和上下文标签，然后写出项目专属的 `CLAUDE.md`、一份 settings 文件和起步文件。新建 Python 研究包、新建静态站、以及接入已有项目的分步走查已经在 [`USAGE.md`](../USAGE.md) 里，本指南不重复。

## 这台机器上的部署是怎么回事

写这一节，是因为一个改动到底活没活，取决于一个别的文档都没写过的细节。

这台机器上有两份这个仓库的副本，而 agent 读的是另外那一份。

1. **这个 checkout**，在分支 `feat/harness-meta-optimization-2026-07-18` 上，是干活的地方。
2. **位于 `~/.claude/agent-harness` 的另一个 clone**，停在 `main` 上，是 plugin marketplace 指向的对象，也是每一个已部署 skill 符号链接最终解析到的地方。

所以在这个分支上新增的 skill，在那个 clone 被更新、或者从这个 checkout 跑一次 `node bin/deploy-skills.mjs --apply` 把符号链接重新指过来之前，都不是活的。dry run 报出来的正是这件事：38 个目标里有 30 个被标记为需要重新链接，因为它们此刻指向那个 clone。

**尽管如此，本分支上仍然是活的部分**，因为它们在这一轮里被手工拷贝或应用过。

1. review-gate 的 `core.sh`、`gate.sh`、`track.sh`、`statsbar.sh`，与分支副本逐字节一致。
2. `~/.claude/CLAUDE.md` 里的托管 rules 块，由 `rule-activation.mjs --apply` 写入。

**本分支上没活的部分。** 本轮其余的新东西全都没活，包括 `rules/native-capability-first`、`hooks/task-ledger`、`bin/rule-activation.mjs`、`bin/harness-feedback.mjs`、`skills/doc-writing` 和 `recommendations/prompt-library/`。它们在那个 clone 里都不存在。从这个 checkout 按路径调用它们都能跑。

**还有一处反方向的偏离。** 已部署的 `precommit.sh` 比分支副本新。它带着本分支切出之后才落到 `main` 上的 ssh-guard 工作，而本分支根本没有 `hooks/ssh-guard` 这个目录。rebase 到 `main` 由另一条工作线跟踪。

**Codex 的行为和另外两个不同。** Claude Code 和 opencode 用符号链接，clone 更新后自动跟上。Codex 的 plugin 缓存是拷贝式的，所以每次 clone 更新后都需要 `codex plugin remove` 再 `codex plugin add`。

**这些你都可以自己查。**

```bash
readlink -f ~/.claude/skills/memory-flywheel        # agent 实际读的是哪一份副本
node bin/deploy-skills.mjs                          # 完整计划，不写任何东西
node bin/rule-activation.mjs --check                # rules 是否抵达各 agent
grep -c "agent-harness:rules:begin" ~/.claude/CLAUDE.md   # 托管块存在则为 1
```

## 验证记录

以下全部于 2026-07-18 在这个 checkout 下运行。本指南里没有任何一句话是没跑过就写下的。

| 命令 | 结果 |
|---|---|
| `npm run check:manifests` | `check OK: all manifests match source` |
| `npm run test:projection` | `projection: all 3 parity test(s) PASS` |
| `npm run test:opencode-review` | `opencode review helper: all 6 checks PASS` |
| `npm run test:deploy-skills` | `deploy-skills.mjs: all 9 checks PASS` |
| `npm run test:rule-activation` | `rule-activation.mjs: all 26 checks PASS` |
| `npm run test:models` | `resolve_model: all 31 checks PASS` |
| `npm run test:codex-install` | `install-codex-local: isolated 20-skill/user-surface install PASS` |
| `npm run test:harness-feedback` | `harness-feedback.mjs: all 9 tests PASS` |
| `npm run test:task-ledger` | `task-ledger hooks: all 11 tests PASS` |
| `npm run test:review-gate-core` | `core.sh: all 22 checks PASS` |
| `bash hooks/review-gate/scripts/test_statsbar.sh` | `statsbar.sh: all 20 checks PASS` |
| `bash hooks/review-gate/scripts/test_precommit.sh` | `precommit.sh: all 22 tests PASS` |
| `bash hooks/block-env-read/test_block_env.sh` | `block-env.sh: all 12 checks PASS` |
| `python3 skills/doc-writing/scripts/test_doccheck.py` | `doccheck.py: 20/20 tests PASS` |
| `python3 skills/memory-flywheel/scripts/test_mem.py` | `mem.py: all 11 tests PASS` |
| `python3 skills/memory-flywheel/scripts/test_mem_eval.py` | `mem_eval.py: all 3 tests PASS` |
| `python3 skills/memory-flywheel/scripts/test_supervise.py` | `supervise.py: all 7 checks PASS` |
| `python3 skills/prompt-library/scripts/test_plib.py` | `plib.py + plib_mine.py: all 24 tests PASS` |
| `python3 skills/agent-update-watcher/scripts/test_check_updates.py` | `check_updates.py: all 6 tests PASS` |
| `python3 skills/task-relationship-analysis/scripts/test_scaffold.py` | `scaffold.py: all 6 tests PASS` |
| `bash skills/tui-installer/scripts/test_install_tui.sh` | `install-tui.sh: all 11 checks PASS` |
| `node bin/rule-activation.mjs --check` | `all registered rules are reachable`，三个 agent 全部 26/26 |
| `node bin/harness-feedback.mjs --list` | `no open entries` |
| `python3 hooks/task-ledger/scripts/ledger.py status` | `Harness meta optimization — 8/16 settled · 8 todo` |
| `bash skills/tui-installer/scripts/install-tui.sh --check` | `4 of 4 recommended tools missing.` |
| `node scripts/resolve_model.mjs claude research` | `claude-opus-4-8` |
| `node bin/deploy-skills.mjs` | `plan: link=4 relink=30 ok=0 kept=4 nosrc=0` |

有两项测试没有运行，两者的结果都不作声明。[`hooks/typecheck-on-edit/test_typecheck.sh`](../hooks/typecheck-on-edit/test_typecheck.sh) 需要 TypeScript 工具链，[`skills/figma-design-fetch/scripts/test_visual_diff.mjs`](../skills/figma-design-fetch/scripts/test_visual_diff.mjs) 需要 pixelmatch 依赖。

## 已知过期文档

写这份指南时发现的问题，只记录不修改，因为这些文件属于别的工作线。

1. **[`docs/strategy/agent-harness-overhaul-2026-07-09/STATUS.md`](strategy/agent-harness-overhaul-2026-07-09/STATUS.md) 与 [`docs/OVERHAUL_DELIVERY.md`](OVERHAUL_DELIVERY.md) 互相矛盾，而两者日期相同。** 状态看板把终端栈的第 8 项和 prompt library 的第 9 项标为未开始、把记忆相关的第 3 和第 4 项标为缺失、把第 5 项标为只做了设计。交付摘要说这五项都已发布，而代码站在交付摘要这一边。状态看板自报的统计是 1 完成、8 部分、2 已研究、4 缺失，这已经不再描述任何东西。
2. **同一份状态看板自相矛盾。** 它的头部写着 review-gate 的解耦已在三个 agent 上全部完成，而它自己推荐的下一步序列第一条就是把同一件解耦当成下一步来做。
3. **[`docs/OVERHAUL_DELIVERY.md`](OVERHAUL_DELIVERY.md) 数少了。** 它写 16 个已发布 skill 和 20 条 rule。仓库现在有 23 个顶层 skill 目录和 27 个 rule 目录。它的第 7 行读起来也像 plugin 卫生是一项已发布能力，而背后那三件事只是一次性手工修改。
4. **[`INVENTORY.md`](../INVENTORY.md) 的标题数字落后于它自己的表格。** rules 一节写 14 条，随后列了 26 行。skills 一节写 general 桶 8 个，随后列了 11 行，同时完全漏掉了 `memory-flywheel`、`prompt-library`、`agent-update-watcher`、`tui-installer`、`task-relationship-analysis`、`doc-writing` 和 `task-orchestrator`。hooks 一节写 2 个，列了 4 行，漏掉 `review-gate` 和 `task-ledger`。注册归属另一条工作线，所以本指南只记录这份漂移，不去修它。
5. **[`README.md`](../README.md) 的章节标题是约数。** 上面写 15 条以上的工作流 rule 和 8 个 hook，而实际是 27 个 rule 目录和 6 个 hook 目录。

## 遗留缺口

集中列在一起，每条都附上它今天让你付出的代价。

1. **`rules/native-capability-first` 是死的。** 它没有注册，所以从不进入任何 agent 的上下文。它所治理的一切，包括通往 `harness-feedback.mjs` 的反馈回路，在它被注册并被一次 `--apply` 收进去之前都是停摆的。
2. **`skills/doc-writing` 无法被发现。** 既未注册也未部署，所以模型按名字找不到它，还会继续在没有它的情况下写文档。linter 按路径仍然可用。
3. **`hooks/task-ledger` 没有安装。** 轮次文档和它的命令行是好用的，但没有任何东西因为未完成的工作而阻断，而那正是这个 hook 的全部意义。
4. **`agent-update-watcher` 没有抓取器。** 它比较的是你提供的版本。没有任何东西去获取它们，也没有定时器去跑它。
5. **自动 plugin 策展不存在。** 从来没有为它构建过工具。
6. **没有上下文占用度量。** overhaul 的第 2 项只做了设计没有实现，所以没有任何数字能告诉你上下文优化到底有没有起作用。
7. **本分支落后于 `main`。** 已部署的 `precommit.sh` 和整个 `hooks/ssh-guard` 目录存在于 `main` 而不在这里。
8. **已部署的 skill 指向另一个 clone。** 在从这个 checkout 跑一次 `deploy-skills.mjs --apply`、或者那个 clone 被更新之前，本分支的新东西没有一样能按 skill 名字够到。
