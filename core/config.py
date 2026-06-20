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

# 流水线自动调度间隔（秒）。真实 LLM 模式建议调大（如 1800=30 分钟）以省额度；mock 可 300。
PIPELINE_INTERVAL_SECONDS = int(os.environ.get("PIPELINE_INTERVAL_SECONDS", "300"))

# 每个 Agent 面板最多保留多少条最近日志（前端展示）
LOG_RETENTION_PER_AGENT = int(os.environ.get("LOG_RETENTION_PER_AGENT", "15"))

# 一次首页推荐/搜索最多返回多少条
RECOMMEND_LIMIT = int(os.environ.get("RECOMMEND_LIMIT", "20"))

# ==================== LLM 配置 ====================
# 提供方：mock（默认，无 key 演示）/ glm（智谱 GLM，需配 ZHIPU_API_KEY）
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock").lower()
ZHIPU_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = os.environ.get("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/anthropic")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "glm-4.6")  # 智谱主力模型（JD 原项目用 glm-5.1；可用 DEFAULT_MODEL 覆盖）
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.7"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "2000"))

# ==================== 感知层配置 ====================
HOT_FETCH_LIMIT = int(os.environ.get("HOT_FETCH_LIMIT", "10"))       # 每次抓百度热搜前 N 条
SCENE_LIMIT_PER_RUN = int(os.environ.get("SCENE_LIMIT_PER_RUN", "3"))  # 每次流水线最多挖掘几条热点场景（控成本）
MIN_CONFIDENCE = float(os.environ.get("MIN_CONFIDENCE", "0.3"))      # 商品匹配置信度下限
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "10"))       # 热搜抓取超时（秒）
SEASONAL_DAYS_BEFORE = int(os.environ.get("SEASONAL_DAYS_BEFORE", "3"))
SEASONAL_DAYS_AFTER = int(os.environ.get("SEASONAL_DAYS_AFTER", "21"))
