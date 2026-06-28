# Commit Message / 提交信息

fix(core): JSON 输出回退 print() 通道 + 硬编码原则 —— 修复 CC 原生评估器 JSON 校验冲突

- _write_json() 及三层 os.write(fd=1) 兜底移除，恢复直接 print(json.dumps(...))
- _setup_encoding() 恢复：sys.stdout/stderr 启动时配置 UTF-8
- 进程退出从 os._exit(0) 恢复为 sys.exit(0)
- 硬编码 JSON 原则：所有 stdout 输出由代码写死，LLM 语义分析仅影响内部分支
- hooks.json Stop timeout 60s→30s，HOOK_BUDGET_SEC 50→25
- 版本号 2.3.1→2.3.3：plugin.json / marketplace.json / _goal_guard.py
- README.md / README_CN.md / RELEASE_NOTES.md 全面更新

---

fix(core): revert JSON output to print() channel + hardcoded principle — fix CC native evaluator JSON validation conflict

- _write_json() and three-layer os.write(fd=1) fallback removed, reverted to direct print(json.dumps(...))
- _setup_encoding() restored: sys.stdout/stderr reconfigured to UTF-8 at startup
- Process exit reverted from os._exit(0) to sys.exit(0)
- Hardcoded JSON principle: all stdout output is code-written, LLM semantic analysis only affects internal branches
- hooks.json Stop timeout 60s→30s, HOOK_BUDGET_SEC 50→25
- Version 2.3.1→2.3.3: plugin.json / marketplace.json / _goal_guard.py
- README.md / README_CN.md / RELEASE_NOTES.md comprehensively updated
