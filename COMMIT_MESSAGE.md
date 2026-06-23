# Commit Message / 提交信息

feat(core): API 错误检测提升为全局 Phase 0 —— 无论是否 /goal 模式均自动恢复

- handle_stop() Phase 重排：API 错误检测从 /goal 专属 Phase 1.5 移至全局 Phase 0
- 非 /goal 会话的 socket 断开/429/502/503 等 API 错误现在自动 BLOCK 恢复
- /goal 模式下 API 错误恢复行为不变
- 版本号 2.1.2 → 2.2.0（plugin.json + marketplace.json + _goal_guard.py）

---

feat(core): promote API error detection to global Phase 0 — auto-recover regardless of /goal mode

- handle_stop() Phase reorder: API error detection moved from /goal-only Phase 1.5 to global Phase 0
- Non-/goal sessions now auto-BLOCK and recover on socket disconnect/429/502/503 API errors
- /goal mode API error recovery behavior unchanged
- Version 2.1.2 → 2.2.0 (plugin.json + marketplace.json + _goal_guard.py)
