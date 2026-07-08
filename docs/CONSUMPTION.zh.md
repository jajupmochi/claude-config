# 消费方式（Consumption）

> 在下游项目里使用本库的三种方式。在 `setup/init-agent-harness` 时选定，或混用。

> **语言：** [English](CONSUMPTION.md) | 中文

## Master TOC

- [方式 A：Raw URL 引用](#方式-araw-url-引用)
- [方式 B：本地 clone + @ imports](#方式-b本地-clone--imports)
- [方式 C：作为 Plugin 安装](#方式-c作为-plugin-安装)
- [对比](#对比)
- [混用](#混用)

## 方式 A：Raw URL 引用

项目的 `CLAUDE.md` 加入类似这样的行：

```markdown
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/pre-edit-confirmation/snippet.md
@https://raw.githubusercontent.com/jajupmochi/agent-harness/main/rules/phased-planning/snippet.md
```

**优点：** 永远是最新（规则更新立即生效）、不用 clone、容易被发现（Claude 直接跟链接走）、零本地配置。

**缺点：** session 启动需要联网；引用多了有 rate-limit 风险；本地覆盖不易（需 fork）。

## 方式 B：本地 clone + @ imports

一次性：

```bash
git clone https://github.com/jajupmochi/agent-harness.git ~/.claude/agent-harness
```

然后在项目 `CLAUDE.md`（或全局 `~/.claude/CLAUDE.md`）：

```markdown
@~/.claude/agent-harness/rules/pre-edit-confirmation/snippet.md
```

**优点：** session 启动更快（无网络）、离线可用、本地易覆盖（直接改 clone 出的文件）、可 pin 到具体 commit/tag。

**缺点：** 手动 `git pull` 才更新；本地改了又忘的话会和 upstream 不同步。

## 方式 C：作为 Plugin 安装

Phase 10 交付 `.claude-plugin/plugin.json` 后：

```bash
/plugin install jajupmochi/agent-harness
```

**优点：** 最原生——安装技能直接作为 `/init-agent-harness` 斜杠命令；自动注册选定的 rules / hooks / skills；marketplace 管更新。

**缺点：** 只有 Phase 10 之后才能用；多了一层间接，调试"这条规则从哪来"多一步。

## 对比

| 维度 | A：Raw URL | B：本地 clone | C：Plugin |
|---|---|---|---|
| Session 启动联网 | 需要 | 不需要 | 部分 |
| 更新机制 | 自动（live） | `git pull` | `/plugin update` |
| 本地覆盖 | 需 fork | 改 clone | 需 fork |
| 安装技能挂为 `/` 命令 | 不可 | 部分（手动调） | 可 |
| 当前可用（Phase 1） | 是 | 是 | 暂不可 |
| Pin 版本 | URL 里写死 | `git checkout <tag>` | plugin 版本号 |

## 混用

可以组合。常见模式：

- **全局** `~/.claude/CLAUDE.md` 用 **方式 B**（clone），稳定且离线可用。
- **项目级** `CLAUDE.md` 用 **方式 A**（raw URL）只引入项目相关子集（比如只要 static-site 那部分）。
- Phase C 上线后，把一个或两个换成 Plugin 形式获得斜杠命令体验。

`setup/init-agent-harness` 技能（Phase 8）会根据用户偏好把对应形式写进新项目的 `CLAUDE.md`。
