"""场景组装：把 LLM 返回的 JD-schema 场景 dict → trend Scene 可直接入库的字段 dict。

JD schema:  scene_name/scene_type/trigger_event/temporal_scope/geo_scope/user_intent/potential_keywords/target_population
trend Scene: title/description/target_user/keywords/source_hotspot + scene_type/trigger_event/temporal_scope/geo_scope/user_intent/source + confidence/expires_at
"""
from datetime import timedelta
from typing import Any, Dict

from core.models import now_utc


def build_scene(
    topic: str,
    llm_data: Dict[str, Any],
    source: str = "hotspot",
    source_detail: str = "",
) -> Dict[str, Any]:
    """组装一条 Scene 字段 dict。

    Args:
        topic: 原始热点/主题文本（写入 source_hotspot）
        llm_data: LLM 返回的场景 dict（JD schema）
        source: hotspot / seasonal / manual
        source_detail: 来源详情（如节日名）
    """
    keywords = llm_data.get("potential_keywords") or []
    return {
        "title": llm_data.get("scene_name") or f"场景: {topic[:20]}",
        "description": llm_data.get("user_intent") or "",
        "target_user": llm_data.get("target_population") or "未知",
        "confidence": 0.8,
        "keywords": keywords,
        "source_hotspot": source_detail or topic,
        "scene_type": llm_data.get("scene_type"),
        "trigger_event": llm_data.get("trigger_event"),
        "temporal_scope": llm_data.get("temporal_scope"),
        "geo_scope": llm_data.get("geo_scope"),
        "user_intent": llm_data.get("user_intent"),
        "source": source,
        "expires_at": now_utc() + timedelta(hours=72),
    }
