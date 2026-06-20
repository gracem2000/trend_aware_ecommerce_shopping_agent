"""流水线编排 + 后台调度（同步）。

- run_pipeline(trigger): 串行跑 4 个 Agent；用 in-process _running 标志互斥；
  last_run_at / next_run_at / last_status 持久化到 system_meta（重启不丢）。
- start_scheduler(): 启动一个守护线程，按 PIPELINE_INTERVAL_SECONDS 自动跑。
- trigger_manual(): 手动触发（在后台线程跑，不阻塞 UI）。
"""
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from core.agents import CopyAgent, DeliverAgent, MatchAgent, SenseAgent
from core.config import PIPELINE_INTERVAL_SECONDS
from core.models import now_utc
from core.repository import set_agent_status, set_system_meta, get_system_meta, time_since, write_log
from core.seed import AGENT_DEFS

# SystemMeta 键
META_LAST_RUN = "pipeline_last_run_at"
META_NEXT_RUN = "pipeline_next_run_at"
META_LAST_STATUS = "pipeline_last_status"

_lock = threading.Lock()
_running = False

_scheduler_started = False
_scheduler_lock = threading.Lock()


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _parse(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def is_running() -> bool:
    with _lock:
        return _running


def run_pipeline(trigger: str = "auto") -> Dict[str, Any]:
    """跑一次完整流水线。已在跑则直接返回。"""
    global _running
    with _lock:
        if _running:
            return {"ok": False, "message": "流水线正在运行"}
        _running = True

    set_system_meta(META_LAST_RUN, _iso(now_utc()))
    set_system_meta(META_NEXT_RUN, _iso(now_utc() + timedelta(seconds=PIPELINE_INTERVAL_SECONDS)))
    write_log("system", "info", f"[PIPELINE] 启动 (trigger={trigger})")

    summary: Dict[str, Any] = {"trigger": trigger, "scenes_added": 0, "pairs": 0, "recommendations": 0}
    ok = True
    try:
        summary["scenes_added"] = SenseAgent().run()
        summary["pairs"] = MatchAgent().run()
        summary["recommendations"] = CopyAgent().run()
        DeliverAgent().run()
        write_log("system", "info",
                  f"[PIPELINE] 完成: 新增场景 {summary['scenes_added']} / "
                  f"关联 {summary['pairs']} / 推荐 {summary['recommendations']}")
        set_system_meta(META_LAST_STATUS, "ok")
    except Exception as e:
        ok = False
        write_log("system", "error", f"[PIPELINE] 异常: {e}")
        set_system_meta(META_LAST_STATUS, "error")
        summary["error"] = str(e)
    finally:
        # 所有 Agent 回到 idle
        for a in AGENT_DEFS:
            set_agent_status(a["key"], "idle", a["task"])
        with _lock:
            _running = False
    return {"ok": ok, "summary": summary}


def trigger_manual() -> Dict[str, Any]:
    """手动触发流水线（后台线程跑，立即返回，不阻塞 UI）。"""
    if is_running():
        return {"ok": False, "message": "流水线正在运行"}
    t = threading.Thread(target=run_pipeline, args=("manual",), daemon=True, name="pipeline-manual")
    t.start()
    return {"ok": True, "message": "已触发"}


def get_pipeline_state() -> Dict[str, Any]:
    """当前流水线状态（供 UI 渲染）。"""
    running = is_running()
    last_run = _parse(get_system_meta(META_LAST_RUN))
    next_run = _parse(get_system_meta(META_NEXT_RUN))
    last_status = get_system_meta(META_LAST_STATUS) or "idle"
    return {
        "running": running,
        "last_run_at": _iso(last_run),
        "last_run_ago": time_since(last_run),
        "next_run_at": _iso(next_run),
        "last_status": "running" if running else last_status,
    }


def start_scheduler() -> None:
    """启动后台自动调度线程（幂等，整个进程只启一次）。"""
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True
    t = threading.Thread(target=_scheduler_loop, daemon=True, name="pipeline-scheduler")
    t.start()


def _scheduler_loop() -> None:
    # 启动后 5s 跑一次，之后按间隔自动跑
    time.sleep(5)
    while True:
        try:
            run_pipeline("auto")
        except Exception as e:  # noqa: BLE001
            print(f"[scheduler] 异常: {e}")
        time.sleep(PIPELINE_INTERVAL_SECONDS)
