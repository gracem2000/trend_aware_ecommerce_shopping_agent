"""ORM 模型（SQLAlchemy 2.0，SQLite）。

从原 src/storage/database/model.py 迁移：
- 去掉 coze_coding_dev_sdk 依赖，自建 Base；
- JSONB → JSON（SQLite 原生支持，读回自动反序列化为 list）；
- 新增 SystemMeta 表，持久化流水线状态。
时区统一存 naive UTC。
"""
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, Float, ForeignKey, Index, Integer, String, Text, JSON, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    pass


def now_utc() -> datetime:
    """当前 naive UTC 时间（SQLite 存储统一用 naive UTC）。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =================== 场景库 ===================
class Scene(Base):
    """消费场景表 —— 感知 Agent 写入。"""
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, comment="场景标题")
    description: Mapped[str] = mapped_column(Text, nullable=False, comment="场景描述")
    target_user: Mapped[str] = mapped_column(String(200), nullable=False, comment="目标用户")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="置信度 0-1")
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="搜索关键词数组")
    source_hotspot: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, comment="来源热点标题")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="时效过期时间")

    __table_args__ = (
        Index("scenes_created_at_idx", "created_at"),
        Index("scenes_title_idx", "title"),
    )


# =================== 商品库 ===================
class Product(Base):
    """商品库 —— 静态/种子数据。"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="商品 SKU")
    title: Mapped[str] = mapped_column(String(300), nullable=False, comment="商品标题")
    price: Mapped[float] = mapped_column(Float, nullable=False, comment="现价")
    original_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="原价")
    shop_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="店铺名")
    good_rate: Mapped[str] = mapped_column(String(20), nullable=False, default="100%", comment="好评率")
    sales: Mapped[str] = mapped_column(String(50), nullable=False, default="0", comment="销量")
    category: Mapped[str] = mapped_column(String(100), nullable=False, comment="类目")
    icon_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, comment="emoji 图标")
    bg_color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="背景色 hex")
    sprite: Mapped[str] = mapped_column(String(50), nullable=False, default="juicer", comment="保留字段（像素图 key，当前 UI 用 emoji）")
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="商品标签")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("products_category_idx", "category"),
        Index("products_sku_idx", "sku_id"),
    )


# =================== 场景-商品关联 ===================
class SceneProduct(Base):
    """场景-商品关联表 —— 挂品 Agent 写入。"""
    __tablename__ = "scene_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene_id: Mapped[int] = mapped_column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="匹配分 0-1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("scene_products_scene_id_idx", "scene_id"),
        Index("scene_products_product_id_idx", "product_id"),
        Index("scene_products_score_idx", "match_score"),
    )


# =================== 推荐内容库 ===================
class Recommendation(Base):
    """推荐内容表 —— 导购生成 Agent 写入。"""
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scene_id: Mapped[int] = mapped_column(Integer, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False, comment="推荐理由")
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="推荐标签")
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, comment="综合评分")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("recommendations_scene_id_idx", "scene_id"),
        Index("recommendations_product_id_idx", "product_id"),
        Index("recommendations_score_idx", "score"),
        Index("recommendations_created_at_idx", "created_at"),
    )


# =================== Agent 日志 ===================
class AgentLog(Base):
    """Agent 日志表。"""
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="sense/match/copy/deliver/system")
    level: Mapped[str] = mapped_column(String(20), nullable=False, default="info", comment="info/warn/error/highlight")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="日志内容")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("agent_logs_agent_name_idx", "agent_name"),
        Index("agent_logs_created_at_idx", "created_at"),
    )


# =================== Agent 状态 ===================
class AgentStatus(Base):
    """Agent 状态表。"""
    __tablename__ = "agent_status"

    agent_name: Mapped[str] = mapped_column(String(50), primary_key=True, comment="Agent 名 (PK)")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="idle", comment="running/idle/done/failed")
    current_task: Mapped[str] = mapped_column(Text, nullable=False, default="等待任务...")
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


# =================== 系统元数据（流水线状态持久化）===================
class SystemMeta(Base):
    """key/value 元数据，存流水线 last_run_at / next_run_at / last_status。"""
    __tablename__ = "system_meta"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
