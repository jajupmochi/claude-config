# Drop-in onboarding prompt

Paste the block below verbatim into any Claude Code session. It installs (or updates) the agent-harness
plugin, de-duplicates, verifies, and then uses the bundled skills automatically for the rest of the session.
It is idempotent — safe to paste into a fresh session or one that already has an old copy loaded.

---

```
Set up and keep the "agent-harness" Claude Code plugin current in this session, then use its skills
automatically. Run these steps with the Bash tool and report the result of each:

1. UPDATE the install copy (clone it first if missing):
   if [ -d ~/.claude/agent-harness/.git ]; then git -C ~/.claude/agent-harness pull --ff-only; \
   else git clone https://github.com/jajupmochi/agent-harness ~/.claude/agent-harness; fi

2. CLEAR any stale delivery from an older version (safe if absent):
   rm -f ~/.claude/skills/claude-config ~/.claude/skills/init-claude-config
   claude plugin marketplace add ~/.claude/agent-harness 2>/dev/null || true

3. INSTALL or refresh the plugin (reinstall picks up updates):
   claude plugin uninstall agent-harness@agent-harness 2>/dev/null || true
   claude plugin install agent-harness@agent-harness

4. DE-DUPLICATE — drop per-skill symlinks that would load the same skills twice
   (leave any ~/.claude/skills/<name> that is a REAL directory — that is my own standalone skill):
   for s in ~/.claude/skills/*; do [ -L "$s" ] && readlink "$s" | grep -q agent-harness && rm "$s"; done

5. VERIFY: claude plugin details agent-harness    # expect: enabled, Skills (~20), ~2.0k always-on tok
   claude plugin list | grep agent-harness

Then tell me: whether it is now enabled, how many skills it exposes, and that it takes full effect in the
NEXT session (plugins load at session start). For the rest of THIS session and future ones, apply the bundled
skills automatically whenever a task matches — e.g. memory-flywheel to persist/recall cross-session memory,
code-verifier before claiming any test/script passes, research-critic before writing a research claim,
task-relationship-analysis before a 3+-step task, privacy-redact before publishing a file, system-cleanup when
a disk fills up. Do not ask permission to consult a skill; announce it in one line and proceed.
```

---

## 中文版(粘贴到任意 Claude Code 会话)

```
在本会话中安装并保持 "agent-harness" 这个 Claude Code 插件为最新,然后自动使用它的技能。
用 Bash 工具依次执行,并汇报每步结果:

1. 更新安装副本(不存在则克隆):
   if [ -d ~/.claude/agent-harness/.git ]; then git -C ~/.claude/agent-harness pull --ff-only; \
   else git clone https://github.com/jajupmochi/agent-harness ~/.claude/agent-harness; fi
2. 清理旧版本残留(不存在也安全):
   rm -f ~/.claude/skills/claude-config ~/.claude/skills/init-claude-config
   claude plugin marketplace add ~/.claude/agent-harness 2>/dev/null || true
3. 安装/刷新插件(重装即可拉取更新):
   claude plugin uninstall agent-harness@agent-harness 2>/dev/null || true
   claude plugin install agent-harness@agent-harness
4. 去重——删掉会导致技能重复加载的每技能软链(保留"真目录",那是我自己的独立技能):
   for s in ~/.claude/skills/*; do [ -L "$s" ] && readlink "$s" | grep -q agent-harness && rm "$s"; done
5. 验证:claude plugin details agent-harness   # 期望:enabled、Skills (~20)、~2.0k always-on
   claude plugin list | grep agent-harness

然后告诉我:是否已 enabled、暴露了多少个技能,并说明它在【下一个会话】才完全生效(插件在会话启动时加载)。
从本会话起,凡任务匹配就自动使用这些技能——例如 memory-flywheel(跨会话记忆)、code-verifier(声称测试通过前)、
research-critic(写研究结论前)、task-relationship-analysis(3+ 步任务前)、privacy-redact(发布文件前)、
system-cleanup(磁盘满时)。不必请求许可,用一句话说明后即执行。
```

---

## Notes

- **Codex / opencode** are separate and not touched by this prompt. For Codex: `codex plugin add
  agent-harness@personal` (re-run after each repo update — its cache is copy-based). For opencode: skills live
  in `~/.config/opencode/skills/` via `node ~/.claude/agent-harness/bin/deploy-skills.mjs --apply --agent opencode`.
- The plugin ships **skills only** by design. Hooks (review-gate) come from `~/.claude/settings.json`; rules
  come from `~/.claude/CLAUDE.md`. See `docs/PLUGIN_INSTALL.md`.
- To use the per-skill-symlink method instead of the plugin, see `docs/PLUGIN_INSTALL.md` section B.
