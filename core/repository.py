"""数据访问层：所有 DB 读写集中在这里。

每个函数自己开短生命周期 Session，调用方无需管 session。
写操作用 _write_lock 串行化（SQLite 写并发安全）；读不持锁。
JSON 列（tags/keywords）由 SQLAlchemy 自动 (de)序列化，读回即 list，无需手动处理字符串。
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from core.config import LOG_RETENTION_PER_AGENT
from core.database import SessionLocal, _write_lock
from core.models import (
    AgentLog, AgentStatus, Product, Recommendation, Scene, SceneProduct,
    SystemMeta, now_utc,
)


# ============== 工具 ==============
def time_since(dt: Optional[datetime]) -> str:
    """距现在的中文相对时间。"""
    if not dt:
        return "--"
    delta = now_utc() - dt
    sec = int(delta.total_seconds())
    if sec < 0:
        return "刚刚"
    if sec < 60:
        return f"{sec} 秒前"
    if sec < 3600:
        return f"{sec // 60} 分钟前"
    return f"{sec // 3600} 小时前"


# ============== 日志 ==============
def write_log(agent_name: str, level: str, message: str) -> None:
    """写一条 Agent 日志（立即提交，保证 UI 能实时读到）。"""
    with _write_lock, SessionLocal() as db:
        db.add(AgentLog(agent_name=agent_name, level=level, message=message))
        db.commit()


def get_recent_logs(limit_per_agent: int = LOG_RETENTION_PER_AGENT) -> Dict[str, List[Dict[str, Any]]]:
    """每个 Agent 最近 N 条日志，按 agent_name 分组。返回 {agent_name: [{id, created_at, level, message}]}。"""
    result: Dict[str, List[Dict[str, Any]]] = {}
    with SessionLocal() as db:
        rows = (
            db.query(AgentLog)
            .order_by(AgentLog.id.desc())
            .limit(200)
            .all()
        )
        for row in rows:
            lst = result.setdefault(row.agent_name, [])
            if len(lst) < limit_per_agent:
                lst.append({
                    "id": row.id,
                    "created_at": row.created_at,
                    "level": row.level,
                    "message": row.message,
                })
    # 反转成时间正序
    for k in result:
        result[k].reverse()
    return result


# ============== Agent 状态 ==============
def set_agent_status(agent_name: str, status: str, task: Optional[str] = None) -> None:
    """更新（或插入）Agent 状态。"""
    with _write_lock, SessionLocal() as db:
        row = db.query(AgentStatus).filter_by(agent_name=agent_name).first()
        if row is None:
            db.add(AgentStatus(
                agent_name=agent_name,
                status=status,
                current_task=task or "等待任务...",
            ))
        else:
            row.status = status
            if task is not None:
                row.current_task = task
            if status in ("done", "failed"):
                row.last_run_at = now_utc()
        db.commit()


def get_all_agent_status() -> Dict[str, AgentStatus]:
    with SessionLocal() as db:
        rows = db.query(AgentStatus).all()
        return {r.agent_name: r for r in rows}


# ============== 系统元数据（流水线状态持久化） ==============
def set_system_meta(key: str, value: Optional[str]) -> None:
    with _write_lock, SessionLocal() as db:
        row = db.query(SystemMeta).filter_by(key=key).first()
        if row is None:
            db.add(SystemMeta(key=key, value=value))
        else:
            row.value = value
        db.commit()


def get_system_meta(key: str) -> Optional[str]:
    with SessionLocal() as db:
        row = db.query(SystemMeta).filter_by(key=key).first()
        return row.value if row else None


# ============== 商品 ==============
def get_products(limit: int = 200) -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        rows = db.query(Product).order_by(Product.id).limit(limit).all()
        return [_serialize_product(p) for p in rows]


# ============== 场景 ==============
def get_scenes(limit: int = 50) -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        rows = db.query(Scene).order_by(Scene.confidence.desc()).limit(limit).all()
        return [{
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "target_user": s.target_user,
            "confidence": s.confidence,
            "keywords": s.keywords or [],
            "source_hotspot": s.source_hotspot or "",
            "created_at": s.created_at,
        } for s in rows]


# ============== 推荐（首页 / 搜索） ==============
def get_recommendations(limit: int = 20) -> List[Dict[str, Any]]:
    with SessionLocal() as db:
        rows = (
            db.query(Recommendation)
            .order_by(Recommendation.score.desc())
            .limit(limit)
            .all()
        )
        return _hydrate(db, rows)


def search(q: str, limit: int = 20) -> List[Dict[str, Any]]:
    """在商品/场景/推荐理由里全文匹配关键词，返回命中推荐（按 score 排序）。

    数据量小，先取候选推荐再在内存里做大小写不敏感匹配，简单可靠。
    """
    ql = q.strip().lower()
    if not ql:
        return get_recommendations(limit)
    with SessionLocal() as db:
        rows = (
            db.query(Recommendation)
            .order_by(Recommendation.score.desc())
            .limit(200)
            .all()
        )
        scenes = {s.id: s for s in db.query(Scene).all()}
        products = {p.id: p for p in db.query(Product).all()}
        matched = []
        for r in rows:
            s = scenes.get(r.scene_id)
            p = products.get(r.product_id)
            haystack = " ".join(_ for _ in [
                p.title if p else "",
                p.shop_name if p else "",
                p.category if p else "",
                " ".join(p.tags or []) if p else "",
                s.title if s else "",
                " ".join(s.keywords or []) if s else "",
                r.reason,
            ] if _).lower()
            if ql in haystack:
                matched.append(r)
        return _hydrate_from_objs(matched, scenes, products)[:limit]


# ============== 序列化 / 水合 ==============
def _serialize_product(p: Optional[Product]) -> Dict[str, Any]:
    if p is None:
        return {}
    return {
        "id": p.id,
        "sku": p.sku_id,
        "title": p.title,
        "price": float(p.price) if p.price is not None else 0,
        "origPrice": float(p.original_price) if p.original_price else None,
        "shop": p.shop_name,
        "goodRate": p.good_rate or "100%",
        "sales": p.sales or "0",
        "category": p.category or "",
        "icon": p.icon_emoji or "",
        "bgColor": p.bg_color or "#5cd65c",
        "tags": p.tags or [],
    }


def _hydrate(db, rows: List[Recommendation]) -> List[Dict[str, Any]]:
    """读推荐行，水合出 scene + product 对象。"""
    scene_ids = {r.scene_id for r in rows}
    product_ids = {r.product_id for r in rows}
    scenes = {s.id: s for s in db.query(Scene).filter(Scene.id.in_(scene_ids)).all()} if scene_ids else {}
    products = {p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()} if product_ids else {}
    return _hydrate_from_objs(rows, scenes, products)


def _hydrate_from_objs(rows: List[Recommendation], scenes: Dict[int, Scene], products: Dict[int, Product]) -> List[Dict[str, Any]]:
    items = []
    for r in rows:
        s = scenes.get(r.scene_id)
        p = products.get(r.product_id)
        items.append({
            "id": r.id,
            "scene_id": r.scene_id,
            "product_id": r.product_id,
            "score": float(r.score or 0),
            "reason": r.reason or "",
            "tags": r.tags or [],
            "scene": {
                "id": s.id,
                "title": s.title,
                "description": s.description,
                "keywords": s.keywords or [],
            } if s else None,
            "product": _serialize_product(p) if p else None,
        })
    return items
