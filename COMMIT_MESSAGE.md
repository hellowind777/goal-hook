# Commit Message / 提交信息

feat(core): 架构全面重构 —— Hybrid Guardian v2.0.1

- 零提示词侵入：从 transcript 自动检测 /goal 状态，不再依赖 .goal_status.json
- 行为结构分析：语言无关的四信号加权体系（零工具调用/趋势塌缩/停滞循环/只读停滞）
- LLM 语义兜底：仅模糊区间触发（~10% 轮次），API 不可用回退保守 BLOCK
- 三钩子架构：Stop + SessionStart + PostCompact 完整生命周期覆盖
- 中断恢复：stop_reason 异常直接 BLOCK
- 会话感知状态管理：CLAUDE_PLUGIN_DATA 持久化
- 文件变更：新增 _goal_guard.py（~300 行），删除 _goal_check.py，更新 hooks.json/plugin.json/README

---

feat(core): complete architecture rewrite —— Hybrid Guardian v2.0.1

- Zero prompt intrusion: auto-detect /goal from transcript, no .goal_status.json dependency
- Behavioral structure analysis: language-agnostic 4-signal weighted scoring
- LLM semantic fallback: ambiguous zone only (~10% turns), conservative BLOCK on API failure
- Three-hook architecture: Stop + SessionStart + PostCompact
- Interruption recovery: abnormal stop_reason triggers immediate BLOCK
- Session-aware state: CLAUDE_PLUGIN_DATA persistence
- Files: added _goal_guard.py (~300 lines), removed _goal_check.py, updated configs
