#!/usr/bin/env python3
"""通用 goal Stop hook —— 三态逻辑，不干预自然语言 /goal。

三种状态：
  .goal_status.json 不存在   → 放行 (pass)，让 CC 内置 prompt hook 自行判定
  status = "in_progress"      → 阻止 (block)，GOAL_PROMPT 明确要求继续循环
  status = "terminated"       → 放行 (pass)，GOAL_PROMPT 声明目标达成

自然语言的 /goal（如"帮我优化策略"）不产生 .goal_status.json，
本 hook 不干预，CC 内置 prompt hook 正常工作。
结构化 GOAL_PROMPT 在启动时写入 in_progress，达成后写入 terminated，
由本 hook 接管循环控制，不受内置 hook JSON 校验错误影响。

用法：
  python ${CLAUDE_PLUGIN_ROOT}/scripts/_goal_check.py
"""
import json
import os
import sys

STATUS_FILE = "scripts/data/.goal_status.json"


def _emit(decision: str, reason: str) -> None:
    print(json.dumps({"decision": decision, "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def main() -> None:
    # 无文件 → 不干预，让 CC 内置 hook 决定
    if not os.path.exists(STATUS_FILE):
        _emit("pass", "非结构化 goal，由内置 hook 判定")
        return

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, IOError) as exc:
        _emit("block", f"GOAL_PROMPT 状态文件读取异常 ({exc})，保守阻止停止")
        return

    status = data.get("status", "")

    if status == "terminated":
        _emit("pass", f"目标达成: Round {data.get('round', '?')}")
    elif status == "in_progress":
        _emit("block", f"GOAL_PROMPT 进行中: {data.get('reason', '继续循环')}")
    else:
        # 未知状态 → 保守处理，不阻止（可能是旧格式文件）
        _emit("pass", f"未知状态 '{status}'，放行由内置 hook 判定")


if __name__ == "__main__":
    main()
