"""UI 组件：把数据渲染成 HTML（商品卡 / Agent 卡 / 状态条）。

所有从数据库来的文本都经过 esc() 转义，防注入。
"""
from datetime import timedelta
from typing import Any, Dict, List, Optional

import streamlit as st

from core.repository import get_all_agent_status, get_recent_logs
from core.seed import AGENT_DEFS

# 存的是 naive UTC，展示用东八区
_LOCAL_OFFSET = timedelta(hours=8)


def esc(s: Any) -> str:
    if s is None:
        return ""
    return (str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def fmt_time(dt) -> str:
    if not dt:
        return "--:--:--"
    try:
        return (dt + _LOCAL_OFFSET).strftime("%H:%M:%S")
    except Exception:
        return "--:--:--"


# ============ 顶部状态 pill ============
def status_pill_html(state: Dict[str, Any]) -> str:
    running = state.get("running")
    last_status = state.get("last_status")
    if running:
        cls, text = "is-running", "流水线运行中"
    elif last_status == "error":
        cls, text = "is-error", "上次出错"
    else:
        cls, text = "", "系统就绪"
    return f'<div class="status-pill {cls}"><span class="dot"></span>{esc(text)}</div>'


def pipeline_meta_html(state: Dict[str, Any]) -> str:
    last = state.get("last_run_ago", "--")
    nxt = state.get("next_run_at")
    next_txt = ""
    if nxt:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(nxt)
            remain = int((dt - datetime.utcnow()).total_seconds())
            next_txt = f" / 下次 {max(0, remain // 60)} 分钟后"
        except Exception:
            next_txt = ""
    return f'<div style="font-size:12px;color:var(--text-muted);">流水线：上次运行 {esc(last)}{next_txt}</div>'


# ============ 商品卡 ============
def product_card_html(rec: Dict[str, Any]) -> str:
    p = rec.get("product") or {}
    scene = rec.get("scene") or {}
    tags = (p.get("tags") or [])[:3]
    price = p.get("price")
    orig = p.get("origPrice")

    orig_html = f'<span class="pc-orig">¥{esc(orig)}</span>' if (orig and orig > price) else ""
    tags_html = "".join(f'<span class="pc-tag">#{esc(t)}</span>' for t in tags)
    scene_title = scene.get("title", "")
    scene_extra = ""
    if scene_title:
        bits = []
        if scene.get("target_population"):
            bits.append(f"👤 {esc(scene['target_population'])}")
        if scene.get("trigger_event"):
            bits.append(f"🎯 {esc(str(scene['trigger_event'])[:20])}")
        extra = f'<span class="pc-scene-extra">{" · ".join(bits)}</span>' if bits else ""
        scene_html = f'<div class="pc-scene">#{esc(scene_title)}{extra}</div>'
    else:
        scene_html = ""
    reason_html = f'<div class="pc-reason">{esc(rec.get("reason", ""))}</div>' if rec.get("reason") else ""

    return f"""
    <div class="product-card">
      <div class="pc-thumb" style="background:{esc(p.get('bgColor') or '#5cd65c')}">{esc(p.get('icon') or '🛍️')}</div>
      <div class="pc-title">{esc(p.get('title', ''))}</div>
      <div class="pc-price">
        <span class="pc-price-now"><span class="sym">¥</span>{esc(price)}</span>
        {orig_html}
      </div>
      <div class="pc-meta">{esc(p.get('shop', ''))} · 好评 {esc(p.get('goodRate', ''))} · 销量 {esc(p.get('sales', ''))}</div>
      <div class="pc-tags">{tags_html}</div>
      {scene_html}
      {reason_html}
    </div>"""


def render_product_grid(items: List[Dict[str, Any]]) -> None:
    if not items:
        st.markdown('<div class="empty-note">暂无匹配的推荐，点右侧「立即跑流水线」生成。</div>',
                    unsafe_allow_html=True)
        return
    cards = "".join(product_card_html(r) for r in items)
    st.markdown(f'<div class="product-grid">{cards}</div>', unsafe_allow_html=True)


# ============ Agent 面板 ============
def agent_card_html(meta: Dict[str, str], status_row, logs: List[Dict[str, Any]]) -> str:
    running = bool(status_row) and status_row.status == "running"
    errored = bool(status_row) and status_row.status == "failed"

    state_cls = "is-running" if running else ("is-error" if errored else "")
    state_text = "运行中" if running else ("错误" if errored else "就绪")
    task = (status_row.current_task if status_row else meta["task"]) or meta["task"]

    log_html = ""
    if logs:
        lines = []
        for l in logs[-6:]:
            lvl = l.get("level", "info")
            line_cls = "is-error" if lvl == "error" else ("is-highlight" if lvl == "highlight" else "")
            lines.append(
                f'<div class="agent-log {line_cls}">'
                f'<span class="t">{esc(fmt_time(l.get("created_at")))}</span> '
                f'{esc(l.get("message", ""))}</div>'
            )
        log_html = f'<div class="agent-logs">{"".join(lines)}</div>'
    else:
        log_html = '<div class="agent-logs" style="color:var(--text-muted);">暂无日志</div>'

    return f"""
    <div class="agent-card {'is-running' if running else ''}">
      <div class="agent-head">
        <span class="agent-avatar">{esc(meta['icon'])}</span>
        <span class="agent-name">{esc(meta['name'])}</span>
        <span class="agent-state {state_cls}"><span class="dot"></span>{esc(state_text)}</span>
      </div>
      <div class="agent-task">{esc(task)}</div>
      {log_html}
    </div>"""


def render_agent_panel() -> None:
    status_map = get_all_agent_status()
    logs_map = get_recent_logs(6)
    order = [a["key"] for a in AGENT_DEFS]
    meta_map = {a["key"]: a for a in AGENT_DEFS}
    cards = "".join(
        agent_card_html(meta_map[k], status_map.get(k), logs_map.get(k, []))
        for k in order
    )
    st.markdown(cards, unsafe_allow_html=True)
