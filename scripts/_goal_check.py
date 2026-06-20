#!/usr/bin/env python3
"""通用 goal Stop hook —— 纯文件状态检查，不依赖 transcript 检测。

三态逻辑：
  .goal_status.json 不存在   → pass（放行，非 goal 会话 或 自然语言短 goal）
  status = "in_progress"      → block（GOAL_PROMPT 明确要求循环保护）
  status = "terminated"       → pass（目标达成）+ 自动清理文件

设计原则：
  - 零依赖：不读 transcript，不检测 /goal 标记，不依赖 CC 内置 hook
  - 持久化兜底：上下文压缩后 /goal 标记丢失，但 .goal_status.json 在磁盘上不受影响
  - 自然语言短 goal：由 CC 内置 prompt hook 判定，本 hook 不干预（无文件 = pass）
  - 长任务 goal：必须使用结构化 GOAL_PROMPT，由 GOAL_PROMPT 步骤 1.0 写入 in_progress

用法：
  python ${CLAUDE_PLUGIN_ROOT}/scripts/_goal_check.py
"""
import json
import os
import sys

STATUS_FILE = "scripts/data/.goal_status.json"

HOW_TO_TERMINATE = (
    "Goal 循环保护中。当你确认目标已达成，执行: "
    "python -c \"import json; json.dump({'status':'terminated','reason':'目标达成'},"
    " open('scripts/data/.goal_status.json','w',encoding='utf-8'))\""
)


def _emit(decision: str, reason: str) -> None:
    print(json.dumps({"decision": decision, "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def _read_status() -> dict | None:
    if not os.path.exists(STATUS_FILE):
        return None
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        return None


def main() -> None:
    status_data = _read_status()

    # 无文件 → 放行（非 goal 会话，或自然语言短 goal 由内置 hook 判定）
    if status_data is None:
        _emit("pass", "")

    status = status_data.get("status", "")

    if status == "terminated":
        # 清理文件，防止残留到下次非 goal 会话
        try:
            os.remove(STATUS_FILE)
        except OSError:
            pass
        _emit("pass", "")

    if status == "in_progress":
        reason = status_data.get("reason", "GOAL_PROMPT 循环执行中")
        _emit("block", f"[goal-hook] {reason}。" + HOW_TO_TERMINATE)

    # 未知状态 → 保守放行
    _emit("pass", "")


if __name__ == "__main__":
    main()
