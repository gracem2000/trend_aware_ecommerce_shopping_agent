# 热点电商导购系统 · 智能导购

一个演示「**热点 → 消费场景 → 爆款商品**」AI 导购流水线的 Web 应用：左侧商品推荐网格，右侧 4 个 Agent 实时工作日志。

- **后端**：4 Agent 流水线（感知 → 挂品 → 导购生成 → 分发）+ SQLite
- **前端**：Streamlit（纯 Python，零前端代码）
- **调度**：后台线程每 5 分钟自动跑一次流水线 + 可手动触发
- **Agent**：当前为 mock（`sleep` + 模板文案），已留好 LLM 接口，后续接真模型只改一处

> 本版本已**脱离扣子（Coze）平台**，是标准的 Streamlit + SQLite + Python 项目，`git push` 即可部署到公网。

---

## 目录结构

```
.
├── app.py                # Streamlit 入口（streamlit run app.py）
├── core/                 # 纯 Python 后端（不依赖 Streamlit，可独立测试）
│   ├── config.py         # 配置（环境变量）
│   ├── database.py       # SQLite 引擎 / Session / 建表 / WAL
│   ├── models.py         # ORM 模型（7 张表）
│   ├── repository.py     # 数据访问层（所有 DB 读写）
│   ├── seed.py           # 种子商品 / 场景 / Agent 定义
│   ├── llm.py            # LLM 抽象 + Mock 实现（可替换接口）
│   ├── pipeline.py       # 流水线编排 + 后台调度
│   └── agents/           # 4 个 Agent（sense/match/copy/deliver）
├── ui/                   # Streamlit 界面层
│   ├── styles.py         # 全局 CSS（现代极简风）
│   ├── components.py     # 商品卡 / Agent 卡 / 状态条
│   └── live.py           # st.fragment 定时刷新（实时日志）
├── data/                 # SQLite 文件目录（不提交；PaaS 挂持久卷到这里）
├── .streamlit/config.toml
├── Dockerfile            # 容器镜像
├── railway.toml          # Railway 部署
├── render.yaml           # Render 部署
├── requirements.txt
└── .env.example
```

---

## 本地运行

需要 Python 3.9+（推荐 3.12）。

```bash
# 1. 建虚拟环境 + 装依赖
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. 启动（首次会自动建库 + 种子数据）
streamlit run app.py
# 打开 http://localhost:8501
```

首次启动后约 5 秒，后台调度器会自动跑一次流水线，右侧 Agent 面板开始滚动日志。

> 想重置数据库：删掉 `data/app.db`（或设环境变量 `DATABASE_PATH` 指到别处），重启即可重新建库 + 种子。

---

## 部署到公网

> **关键：SQLite 的持久化**。如果只是把数据库文件放在容器内，**每次重新部署数据都会被重置**（演示数据会自动 re-seed，但你之后手动加的数据会丢）。要持久化，必须给数据库目录挂一个**持久卷（persistent volume）**。

项目默认 `DATABASE_PATH=/data/app.db`，所以把持久卷挂到 `/data` 即可。下面三条路径任选其一。

### 方案一：Railway（推荐，数据持久、配置最简单）

1. 把项目推到 GitHub（见下方「初始化 git」）。
2. Railway → New Project → Deploy from GitHub repo → 选本仓库。
3. Railway 自动识别 `Dockerfile` / `railway.toml` 构建。
4. **加持久卷**：服务设置 → Volumes → Add Volume，Mount path 填 `/data`。
5. 确认环境变量 `DATABASE_PATH=/data/app.db`（Dockerfile 已默认）。
6. 部署完成，拿到 `xxx.up.railway.app` 公网地址。

### 方案二：Render

1. Render → New → Blueprint → 选本仓库（读取 `render.yaml`）。
2. `render.yaml` 已配置 disk 挂到 `/data`（**持久磁盘需付费方案**；免费方案每次重新部署 SQLite 会重置）。
3. 部署完成，拿到 `xxx.onrender.com` 地址。

### 方案三：Streamlit Community Cloud（零配置免费，但不持久）

1. 推到 GitHub。
2. streamlit.io/cloud → Deploy app → 选仓库，主文件填 `app.py`。
3. ⚠️ Community Cloud 的文件系统是 **ephemeral**：每次应用重新部署 / 休眠唤醒，SQLite 会被重置（自动 re-seed 演示数据）。**只适合纯演示**，不要指望它保存数据。需要持久数据请用方案一/二。

### 本地 Docker

```bash
docker build -t trend-shop .
# 用本地 ./data 目录做持久化
docker run --rm -p 8501:8501 -v "$PWD/data:/data" -e DATABASE_PATH=/data/app.db trend-shop
# 打开 http://localhost:8501
```

---

## 维护指南

### 加 / 改商品

编辑 `core/seed.py` 的 `INITIAL_PRODUCTS`。字段：`sku_id / title / price / original_price / shop_name / good_rate / sales / category / icon_emoji / bg_color / tags`。改完删 `data/app.db` 重启即可重新种子。

> 想在不重置的情况下加商品：可以用 `sqlite3 data/app.db` 直接往 `products` 表插，或临时写个小脚本走 `core.database.SessionLocal`。

### 加 / 改场景

编辑 `core/seed.py` 的 `INITIAL_SCENES`，`keywords` 用于和商品 `tags`/`category` 做匹配。

### 接真实大模型（把 mock 换成真 LLM）

1. 新建 `core/llm_deepseek.py`（或 openai/glm），写一个继承 `LLMClient` 的类，实现 `complete(prompt)`：
   ```python
   from core.llm import LLMClient
   class DeepSeekLLMClient(LLMClient):
       def complete(self, prompt: str) -> str:
           # 调用对应 SDK，返回模型文本
           ...
   ```
2. 在 `core/llm.py` 的 `get_llm()` 里加一个分支：
   ```python
   elif provider == "deepseek":
       from core.llm_deepseek import DeepSeekLLMClient
       _LLM_SINGLETON = DeepSeekLLMClient()
   ```
3. 设置环境变量 `LLM_PROVIDER=deepseek`（以及模型 API key 等）。

挂品 Agent 的匹配逻辑、其余 Agent 不用改 —— 这就是预留的「可替换接口」。

### 改流水线调度频率

设环境变量 `PIPELINE_INTERVAL_SECONDS=600`（10 分钟）等。

### 调度器说明

后台调度是进程内线程：**只在应用进程活着时跑**。Railway / 付费 Render 常驻不睡；免费层会休眠，休眠期间调度暂停，唤醒后继续。这对演示完全够用。需要更严格的定时，可后续接外部 cron。

---

## 技术备忘

- **SQLite 并发**：启用了 WAL 模式（读不阻塞写），写操作在 `repository`/`agent` 层用可重入锁串行化。Streamlit 多会话并发读 + 后台流水线写安全。
- **单进程模型**：不要把 Streamlit 跑成多进程/多副本，否则调度器会跑多份、SQLite 写竞争。PaaS 默认单实例即可。
- **时区**：数据库统一存 naive UTC，界面展示转成东八区。
- **4 Agent 当前是 mock**：`sleep` + 随机评分 + 模板文案，行为可预测、不联网。
