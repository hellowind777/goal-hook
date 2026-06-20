#!/usr/bin/env python3
"""会话启动清理 —— 自动终止上一会话残留的僵尸 Python 进程。

识别规则（满足任一即清理）：
1. 命令行包含 hello-ashare / aquant / backtest 项目路径 → 属于本项目残留
2. 运行 >10 分钟且 CPU <1% → 明显挂死

安全边界：
- 跳过当前进程及其父进程链
- 跳过运行 <2 分钟的新进程（可能是合法并发任务）
- 所有操作记录到 stderr
"""
import os
import sys
import time
import psutil


def _get_ancestor_pids() -> set:
    """获取当前进程及其所有祖先进程的 PID 集合。"""
    pids = set()
    try:
        proc = psutil.Process(os.getpid())
        while proc is not None:
            pids.add(proc.pid)
            proc = proc.parent()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return pids


def _is_our_project(proc) -> bool:
    """检查进程命令行是否属于我们的项目。"""
    try:
        cmdline = " ".join(proc.cmdline()).lower()
        for marker in ["hello-ashare", "aquant", "backtest", "strategy_backtest",
                       "goal_check", "goal_status", "pilot_round"]:
            if marker in cmdline:
                return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False


def _is_hung(proc) -> bool:
    """检查进程是否明显挂死（运行 >10 分钟且 CPU 接近零）。"""
    try:
        runtime = time.time() - proc.create_time()
        if runtime < 600:  # 运行不到 10 分钟，可能还在工作
            return False
        cpu = proc.cpu_percent(interval=0.1)
        return cpu < 1.0
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def main():
    protected = _get_ancestor_pids()
    killed = 0

    for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
        try:
            pname = proc.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        if not pname.startswith("python"):
            continue

        pid = proc.pid
        if pid in protected:
            continue

        # 运行 <2 分钟的新进程不碰
        try:
            runtime = time.time() - proc.create_time()
            if runtime < 120:
                continue
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

        should_kill = _is_our_project(proc) or _is_hung(proc)

        if should_kill:
            try:
                cmdline = " ".join(proc.cmdline() or [])[:150]
            except Exception:
                cmdline = "(unavailable)"
            try:
                proc.kill()
                killed += 1
                sys.stderr.write(f"[cleanup] Killed orphan PID={pid} runtime={runtime/60:.0f}min cmd={cmdline}\n")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    if killed > 0:
        sys.stderr.write(f"[cleanup] SessionStart: cleaned {killed} orphan process(es)\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
