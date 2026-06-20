"""注入全局 CSS（现代极简风，设计 token 搬自原 styles/main.css）。

Streamlit 原生组件不够自由，所以商品卡 / Agent 卡 / 状态条都用 st.markdown(unsafe_allow_html)
注入 HTML 块，再用这里的 CSS 统一外观。
"""
import streamlit as st

CSS = """
<style>
/* ============ 设计 token ============ */
:root {
  --bg-page: #f7f8fa;
  --bg-card: #ffffff;
  --bg-panel: #f9fafb;
  --border-soft: #e5e7eb;
  --border-card: #f0f0f0;
  --text-primary: #111827;
  --text-secondary: #6b7280;
  --text-muted: #9ca3af;
  --brand: #ff6b35;
  --brand-hover: #ea580c;
  --link: #2563eb;
  --success: #10b981;
  --warning: #f59e0b;
  --danger: #ef4444;
  --idle: #9ca3af;
  --shadow-md: 0 1px 3px rgba(0,0,0,.06), 0 1px 2px rgba(0,0,0,.04);
  --shadow-lg: 0 4px 12px rgba(0,0,0,.08), 0 2px 4px rgba(0,0,0,.04);
  --radius: 12px;
}

/* 页面底色 + 字体 */
.stApp, .main, section[data-testid="stMain"] {
  background: var(--bg-page);
  font-family: "Inter", "Noto Sans SC", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--text-primary);
}

/* 上边距必须够大，避开 Streamlit 固定顶栏（汉堡菜单/工具栏），否则首行内容会被它盖住 */
.block-container { padding-top: 5rem !important; padding-bottom: 3rem !important; max-width: 1400px; }

/* logo */
.brand-logo {
  display:flex; align-items:center; gap:10px;
  font-size: 20px; font-weight: 700; color: var(--text-primary);
}
.brand-logo .dot {
  width: 12px; height: 12px; background: var(--brand); border-radius: 3px;
}
.brand-logo .sub { font-size: 12px; font-weight: 400; color: var(--text-muted); margin-left: 4px; }

/* 顶部状态 pill */
.status-pill {
  display:inline-flex; align-items:center; gap:8px;
  background: var(--bg-card); border:1px solid var(--border-soft);
  padding: 6px 14px; border-radius: 999px; font-size: 13px; color: var(--text-secondary);
  box-shadow: var(--shadow-md);
}
.status-pill .dot { width:8px; height:8px; border-radius:50%; background: var(--idle); }
.status-pill.is-running .dot { background: var(--success); animation: breathe 1.5s ease-in-out infinite; }
.status-pill.is-error .dot { background: var(--danger); }
@keyframes breathe { 0%,100%{opacity:.4} 50%{opacity:1} }

/* ============ 商品网格 / 卡片 ============ */
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 14px;
}
.product-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-md);
  transition: transform .2s ease, box-shadow .2s ease;
  display: flex; flex-direction: column; gap: 8px;
}
.product-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-lg); }
.pc-thumb {
  width: 44px; height: 44px; border-radius: 10px;
  display:flex; align-items:center; justify-content:center;
  font-size: 24px; line-height: 1;
}
.pc-title { font-size: 14px; font-weight: 500; line-height: 1.4; color: var(--text-primary);
  display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; min-height: 39px; }
.pc-price { display:flex; align-items:baseline; gap:6px; }
.pc-price-now { font-size: 18px; font-weight: 600; color: var(--brand); }
.pc-price-now .sym { font-size: 12px; }
.pc-orig { font-size: 12px; color: var(--text-muted); text-decoration: line-through; }
.pc-meta { font-size: 12px; color: var(--text-secondary); }
.pc-tags { display:flex; flex-wrap:wrap; gap:4px; }
.pc-tag { font-size: 11px; color: var(--link); background: rgba(37,99,235,.08);
  padding: 2px 8px; border-radius: 999px; }
.pc-scene { font-size: 12px; color: var(--success); font-weight: 500; }
.pc-scene-extra { color: var(--text-muted); font-weight: 400; margin-left: 4px; font-size: 11px; }
.pc-reason { font-size: 12px; color: var(--text-secondary); line-height: 1.5;
  background: var(--bg-panel); padding: 6px 8px; border-radius: 8px; }

/* ============ Agent 面板 ============ */
.agent-card {
  background: var(--bg-card); border:1px solid var(--border-card);
  border-radius: var(--radius); padding: 12px 14px; margin-bottom: 10px;
  box-shadow: var(--shadow-md);
}
.agent-card.is-running { border-color: var(--success); }
.agent-head { display:flex; align-items:center; gap:8px; margin-bottom: 4px; }
.agent-avatar { font-size: 18px; }
.agent-name { font-size: 13px; font-weight: 600; color: var(--text-primary); flex: 1; }
.agent-state { font-size: 12px; color: var(--text-secondary); display:flex; align-items:center; gap:4px; }
.agent-state .dot { width:7px; height:7px; border-radius:50%; background: var(--idle); display:inline-block; }
.agent-state.is-running .dot { background: var(--success); animation: breathe 1.5s ease-in-out infinite; }
.agent-state.is-error .dot { background: var(--danger); }
.agent-task { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.agent-logs { font-family: "JetBrains Mono","Roboto Mono",ui-monospace,monospace; font-size: 11.5px; line-height: 1.6; }
.agent-log { color: var(--text-secondary); white-space: pre-wrap; word-break: break-word; }
.agent-log .t { color: var(--text-muted); }
.agent-log.is-error { color: var(--danger); }
.agent-log.is-highlight { color: var(--brand); }

/* 空态 */
.empty-note { color: var(--text-muted); font-size: 13px; padding: 20px 0; text-align: center; }

/* 按钮：只给 primary（跑流水线）上品牌橙；secondary（场景 chip）保持默认浅色 */
.stButton > button[kind="primary"] {
  background: var(--brand) !important; border-color: var(--brand) !important;
  color: #fff !important; border-radius: 10px !important; font-weight: 500 !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--brand-hover) !important; border-color: var(--brand-hover) !important;
}
.stButton > button[kind="primary"]:disabled { opacity: .5; }
/* 场景 chip（secondary） */
.stButton > button[kind="secondary"] {
  border-radius: 999px !important; font-size: 12px !important;
  border-color: var(--border-soft) !important; color: var(--text-secondary) !important;
  padding: 2px 12px !important; height: auto !important;
}
.stButton > button[kind="secondary"]:hover {
  border-color: var(--brand) !important; color: var(--brand) !important; background: rgba(255,107,53,.06) !important;
}
/* 搜索框圆角 */
.stApp input[type="text"] { border-radius: 10px !important; }

/* 隐藏 Streamlit 默认装饰 */
#MainMenu, footer { visibility: hidden; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
