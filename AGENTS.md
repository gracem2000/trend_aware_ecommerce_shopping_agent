# AGENTS.md — 热点电商导购系统

## 项目概览
**类型**：Streamlit 单体应用（纯 Python，无前端框架/无构建步骤）
**入口**：`app.py` → `streamlit run app.py`
**栈**：Streamlit + SQLAlchemy + SQLite
**部署**：Railway / Render / Streamlit Cloud（详见 README.md）

演示「热点 → 消费场景 → 爆款商品」的 4 Agent 导购流水线，右侧实时展示 Agent 工作日志。

## 目录结构
```
app.py                # Streamlit 入口（页面编排）
core/                 # 后端（不依赖 Streamlit，可单测）
  config.py           # 配置（环境变量）
  database.py         # SQLite engine + Session + WAL + init_db
  models.py           # ORM（7 张表）
  repository.py       # 数据访问层（所有 DB 读写，写用锁串行）
  seed.py             # 种子商品/场景 + Agent 定义
  llm.py              # LLMClient 抽象 + MockLLMClient（可替换接口）
  pipeline.py         # run_pipeline + 后台调度线程 + 状态持久化
  agents/             # sense/match/copy/deliver（各一个同步 run()）
ui/                   # Streamlit 界面
  styles.py           # 全局 CSS（现代极简风）
  components.py       # 商品卡/Agent卡/状态条 HTML 渲染
  live.py             # st.fragment 定时刷新（实时日志）
data/                 # SQLite 文件（不提交，PaaS 挂持久卷）
```

## 本地运行
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py      # http://localhost:8501
```
首次启动自动建库 + 种子；约 5s 后后台调度器跑第一次流水线。

## 关键约定
- **数据访问统一走 `core/repository.py`**；agent 的批量写可直接用 `SessionLocal` + `_write_lock`（见 `core/agents/*`）。写操作短事务、提交后再 log（避免持锁调 log）。
- **JSON 列**（tags/keywords）由 SQLAlchemy 自动 (de)序列化，读回即 `list`，无需 `isinstance(str)` 处理。
- **时区**：DB 存 naive UTC（`now_utc()`），UI 展示转东八区（`ui/components.py:fmt_time`）。
- **流水线状态**：`running` 是进程内标志；`last_run_at`/`next_run_at`/`last_status` 持久化在 `system_meta` 表（重启不丢）。
- **单进程**：不要多副本运行（调度器会重复、SQLite 写竞争）。

## 常见改动
- **加商品/场景**：改 `core/seed.py` 的 `INITIAL_PRODUCTS`/`INITIAL_SCENES`，删 `data/app.db` 重启重新种子。
- **接真 LLM**：见 `core/llm.py:get_llm()` 注释 + README「接真实大模型」。
- **改调度频率**：环境变量 `PIPELINE_INTERVAL_SECONDS`。
- **改 UI 配色**：`ui/styles.py` 的 CSS 变量 + `.streamlit/config.toml` 的 `[theme]`。

## 常见问题
1. **数据丢失**：SQLite 没挂持久卷 → 重新部署会重置（自动 re-seed）。PaaS 挂 `/data` 卷。
2. **日志不刷新**：`st.fragment` 每 3s 刷一次；浏览器需保持连接。
3. **数据库锁**：已开 WAL；若仍报 `database is locked`，检查是否多进程/多副本运行。
