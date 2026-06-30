#!/usr/bin/env python3
"""hello-goal v2.3.8 StopFailure 守护 —— CC turn 因 API 错误终止时自动恢复继续。

CC v2.1.78+ 在 API 错误（socket 断开/429/503/认证失败等）时触发 StopFailure 事件，
传入 error_type + error_message。本 handler 无条件返回 BLOCK 让任务继续。
"""
import json
import sys


def main():
    try:
        ctx = json.load(sys.stdin)
    except Exception:
        ctx = {}

    _ = ctx.get("error_type", "")
    _ = ctx.get("error_message", "")

    print(json.dumps({"decision": "block", "reason": "继续"}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
