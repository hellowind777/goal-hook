#!/usr/bin/env python3
"""通用 goal Stop hook —— 纯文件状态检查，不依赖 transcript 检测。

三态逻辑：
  .goal_status.json 不存在   → pass（放行，非 goal 会话）
  status = "in_progress"      → block（GOAL_PROMPT 循环保护中）
  status = "terminated"       → pass（目标达成）+ 自动清理文件

超时保护：
  in_progress 文件超过 48 小时未更新 → 判定为崩溃残留，自动清理并放行
  防止 /goal 会话中途崩溃后，残留文件导致后续非 /goal 会话无法退出。

设计原则：
  - 零依赖：不读 transcript，不检测 /goal 标记，不依赖 CC 内置 hook
  - 持久化兜底：上下文压缩不影响磁盘上的状态文件
  - 非 /goal 会话：无文件 → pass，完全不影响正常使用
  - 崩溃恢复：48 小时超时自动过期，不留僵尸文件

用法：
  python ${CLAUDE_PLUGIN_ROOT}/scripts/_goal_check.py
"""
import json
import os
import sys
import time

STATUS_FILE = "scripts/data/.goal_status.json"
STALE_HOURS = 48  # in_progress 文件超过此时间未更新 → 判定为崩溃残留

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


def _file_age_hours() -> float:
    """返回状态文件距今的小时数。"""
    try:
        return (time.time() - os.path.getmtime(STATUS_FILE)) / 3600.0
    except OSError:
        return 0.0


def main() -> None:
    status_data = _read_status()

    # 无文件 → 放行
    if status_data is None:
        _emit("pass", "")

    status = status_data.get("status", "")

    if status == "in_progress":
        age = _file_age_hours()
        if age > STALE_HOURS:
            # 崩溃残留 → 自动清理
            try:
                os.remove(STATUS_FILE)
            except OSError:
                pass
            _emit("pass", "")
        reason = status_data.get("reason", "GOAL_PROMPT 循环执行中")
        _emit("block", f"[goal-hook] {reason}。" + HOW_TO_TERMINATE)

    if status == "terminated":
        try:
            os.remove(STATUS_FILE)
        except OSError:
            pass
        _emit("pass", "")

    # 未知状态 → 保守放行
    _emit("pass", "")


if __name__ == "__main__":
    main()
