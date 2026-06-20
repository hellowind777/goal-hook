#!/usr/bin/env python3
"""通用 goal Stop hook —— 状态文件 + transcript 存活双重检查。

三态逻辑：
  .goal_status.json 不存在   → pass（放行，非 goal 会话）
  status = "in_progress"      → transcript 存活检测 → block or 自动清理
  status = "terminated"       → pass（目标达成）+ 自动清理文件

Transcript 存活检测（核心）：
  CC 的 Stop hook 通过 stdin 传入 transcript_path（会话完整 JSONL）。
  活跃 /goal 时 GOAL_PROMPT 驱动每一轮回复，assistant 消息必然包含
  周期标志词（Cycle / GOAL_PROMPT / 即将开始 等）。
  如果最后一条 assistant 消息不含任何标志词，说明会话已离开 /goal 模式
  而状态文件残留 → 自动清理并放行。

  这解决了"/goal 结束仅几分钟后就被误拦截"的根本问题——
  不需要等超时，立刻就能从 transcript 判断 /goal 是否还活着。

超时保护（兜底）：
  in_progress 文件超过 8 小时未更新 → 判定为残留，自动清理并放行。
  transcript 可读时不会触发此分支；仅在 transcript 不可读时作为最后安全网。

用法：
  python ${CLAUDE_PLUGIN_ROOT}/scripts/_goal_check.py
"""
import json
import os
import re
import sys
import time

STATUS_FILE = "scripts/data/.goal_status.json"
STALE_HOURS = 8

HOW_TO_TERMINATE = (
    "Goal 循环保护中。当你确认目标已达成，执行: "
    "python -c \"import json; json.dump({'status':'terminated','reason':'目标达成'},"
    " open('scripts/data/.goal_status.json','w',encoding='utf-8'))\""
)

# /goal 活跃周期标志词 —— 活跃 /goal 回复中必然出现其中一个
_GOAL_CYCLE_RE = re.compile(
    r"Cycle\s*\d|GOAL_PROMPT|TERMINATION_GUARD|循环执行中|即将开始"
    r"|不可终止|未达标|需≥|TERMINATED\S*三条件|达标判定"
    r"|P\d+方向|P\d+持续性|P\d+\s*Top|本轮目标|当前进度"
)


def _block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    sys.exit(0)


def _pass() -> None:
    print("{}")
    sys.exit(0)


def _cleanup() -> None:
    try:
        os.remove(STATUS_FILE)
    except OSError:
        pass


def _read_status() -> dict | None:
    if not os.path.exists(STATUS_FILE):
        return None
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, IOError):
        return None


def _file_age_hours() -> float:
    try:
        return (time.time() - os.path.getmtime(STATUS_FILE)) / 3600.0
    except OSError:
        return 0.0


def _read_last_assistant_content(transcript_path: str) -> str:
    """读取 transcript 末尾最后一条 assistant 消息的文本内容。

    只读文件末尾 ~64KB，覆盖最近几条消息，大文件也不会慢。
    返回空字符串表示无法读取或未找到。
    """
    if not transcript_path or not os.path.exists(transcript_path):
        return ""
    try:
        file_size = os.path.getsize(transcript_path)
        read_size = min(file_size, 64 * 1024)
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as fh:
            if file_size > read_size:
                fh.seek(file_size - read_size)
            lines = fh.readlines()

        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        parts.append(str(block.get("text", "")))
                    elif isinstance(block, str):
                        parts.append(block)
                content = " ".join(parts)
            return str(content)
        return ""
    except Exception:
        return ""


def _has_goal_markers(text: str, status_reason: str) -> bool:
    """检查文本中是否包含 /goal 活跃标志。"""
    if not text:
        return False
    # 特异性标志：从 status reason 中提取 "Cycle N" 精确匹配
    if status_reason:
        m = re.search(r"Cycle\s*\d+", status_reason)
        if m and m.group() in text:
            return True
    # 通用标志：正则匹配
    return bool(_GOAL_CYCLE_RE.search(text))


def _is_goal_active(transcript_path: str, status_data: dict) -> bool:
    """通过 transcript 判断 /goal 是否仍在活跃运行。

    活跃 /goal → 最后一条 assistant 消息必然包含周期标志词。
    无标志词 → 会话已离开 /goal → 返回 False，触发清理。
    transcript 不可读 → 保守返回 True，依赖超时兜底。
    """
    reason = status_data.get("reason", "")
    content = _read_last_assistant_content(transcript_path)
    if not content:
        return True  # 无法读取 transcript → 保守假设活跃
    return _has_goal_markers(content, reason)


def main() -> None:
    # Windows GBK → UTF-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # 读取 CC hook 上下文（stdin JSON）
    try:
        hook_ctx = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        hook_ctx = {}
    transcript_path = hook_ctx.get("transcript_path", "")

    status_data = _read_status()

    # 无文件 → 放行
    if status_data is None:
        _pass()

    status = status_data.get("status", "")

    if status == "in_progress":
        age = _file_age_hours()
        if age > STALE_HOURS:
            _cleanup()
            _pass()

        if not _is_goal_active(transcript_path, status_data):
            _cleanup()
            _pass()

        reason = status_data.get("reason", "GOAL_PROMPT 循环执行中")
        _block(f"[goal-hook] {reason}。" + HOW_TO_TERMINATE)

    if status == "terminated":
        _cleanup()
        _pass()

    _pass()


if __name__ == "__main__":
    main()
