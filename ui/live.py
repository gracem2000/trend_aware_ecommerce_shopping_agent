"""实时刷新片段（st.fragment）。

- right_panel_fragment: 每 3s 刷新 顶部状态条 + 跑流水线按钮 + Agent 面板
- product_grid_fragment: 每 5s 刷新 商品网格（读到 session_state.query 决定首页/搜索）

fragment 定时重跑只刷新自身，不打断整页、不丢搜索输入框焦点。
"""
from datetime import timedelta

import streamlit as st

from core import repository as r
from core.pipeline import get_pipeline_state, is_running, trigger_manual
from ui.components import (
    pipeline_meta_html, render_agent_panel, render_product_grid, status_pill_html,
)


@st.fragment(run_every=timedelta(seconds=3))
def right_panel_fragment() -> None:
    state = get_pipeline_state()
    st.markdown(status_pill_html(state), unsafe_allow_html=True)

    running = is_running()
    if st.button("立即跑流水线", disabled=running, use_container_width=True, type="primary"):
        trigger_manual()

    st.markdown(pipeline_meta_html(state), unsafe_allow_html=True)
    st.markdown('<hr style="margin:12px 0;border:none;border-top:1px solid var(--border-soft);"/>',
                unsafe_allow_html=True)
    st.markdown("**Agent 流水线**")
    render_agent_panel()


@st.fragment(run_every=timedelta(seconds=5))
def product_grid_fragment() -> None:
    q = (st.session_state.get("query") or "").strip()
    if q:
        items = r.search(q, limit=24)
        title = f'搜索：{q}'
    else:
        items = r.get_recommendations(limit=24)
        title = '热门推荐'
    st.markdown(f'#### {title} · 共 {len(items)} 条')
    render_product_grid(items)
