"""热点电商导购系统 —— Streamlit 入口。

运行：streamlit run app.py
"""
import streamlit as st

from core import repository as r
from core.database import init_db
from core.pipeline import start_scheduler
from ui.components import product_card_html  # noqa: F401  (确保模块加载/样式可用)
from ui.live import product_grid_fragment, right_panel_fragment
from ui.styles import inject_css

st.set_page_config(page_title="热点商城 · 智能导购", page_icon="🛍️", layout="wide")


@st.cache_resource(show_spinner=False)
def bootstrap() -> str:
    """进程级一次性初始化：建表+种子、启动后台调度线程。"""
    init_db()
    start_scheduler()
    return "ok"


# 初始化 session_state
if "query" not in st.session_state:
    st.session_state.query = ""

bootstrap()
inject_css()

# ============ 顶部 ============
hcol1, hcol2 = st.columns([1, 3])
with hcol1:
    st.markdown(
        '<div class="brand-logo"><span class="dot"></span>'
        '热点商城<span class="sub">智能导购</span></div>',
        unsafe_allow_html=True,
    )
with hcol2:
    st.text_input(
        "搜索",
        key="query",
        placeholder="搜索商品名、场景关键词、品牌…（回车搜索）",
        label_visibility="collapsed",
    )

st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid var(--border-soft);"/>',
            unsafe_allow_html=True)

# ============ 场景标签条 ============
def _set_query(title: str) -> None:
    """场景按钮回调：把场景标题填进搜索框。

    只能在 on_click 回调里改 widget 绑定的 session_state（在 widget 实例化后直接改会报错）。
    """
    st.session_state.query = title


_SCENES_SRC_ICON = {"seasonal": "📅", "hotspot": "🔥", "manual": "✍️", "seed": "🔥"}

scenes = r.get_scenes(6)
if scenes:
    cols = st.columns(len(scenes))
    for col, sc in zip(cols, scenes):
        icon = _SCENES_SRC_ICON.get(sc.get("source"), "🔥")
        col.button(f"{icon} {sc['title']}", key=f"scene_{sc['id']}",
                   use_container_width=True, type="secondary",
                   on_click=_set_query, args=(sc["title"],))

# ============ 主体两栏 ============
left, right = st.columns([7, 3], gap="medium")
with left:
    product_grid_fragment()
with right:
    right_panel_fragment()
