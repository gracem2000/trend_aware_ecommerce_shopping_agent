"""配置：从环境变量读取（支持 .env）。

所有可调参数集中在这里，方便单人维护。
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# 项目根目录（core/ 的上一级）
ROOT = Path(__file__).resolve().parent.parent

# SQLite 数据库文件路径。部署到 PaaS 时通过环境变量指向持久卷，例如 /data/app.db
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(ROOT / "data" / "app.db"))

# 流水线自动调度间隔（秒）。演示用 5 分钟。
PIPELINE_INTERVAL_SECONDS = int(os.environ.get("PIPELINE_INTERVAL_SECONDS", "300"))

# 每个 Agent 面板最多保留多少条最近日志（前端展示）
LOG_RETENTION_PER_AGENT = int(os.environ.get("LOG_RETENTION_PER_AGENT", "15"))

# 一次首页推荐/搜索最多返回多少条
RECOMMEND_LIMIT = int(os.environ.get("RECOMMEND_LIMIT", "20"))
