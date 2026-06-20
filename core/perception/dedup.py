"""场景智能去重（吸收自 JD 的 scene_mining.py 相似度部分）。

判定依据：场景名/触发事件文本相似度（SequenceMatcher）+ 关键词 Jaccard 重叠 + 24h 时间窗。
用于避免同一热点/节日重复生成近似场景。
"""
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import List, Tuple

SIMILARITY_THRESHOLD = 0.75  # 名称/触发事件相似阈值
KEYWORD_OVERLAP_THRESHOLD = 0.6
TIME_WINDOW_HOURS = 24


def text_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def keyword_overlap(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    s1 = {k.lower() for k in a}
    s2 = {k.lower() for k in b}
    inter = s1 & s2
    union = s1 | s2
    return len(inter) / len(union) if union else 0.0


def _within_time_window(t1, t2) -> bool:
    try:
        d1 = t1 if isinstance(t1, datetime) else datetime.fromisoformat(str(t1))
        d2 = t2 if isinstance(t2, datetime) else datetime.fromisoformat(str(t2))
        return abs(d1 - d2) <= timedelta(hours=TIME_WINDOW_HOURS)
    except Exception:  # noqa: BLE001
        return True


def is_similar(new: dict, existing: dict) -> Tuple[bool, str]:
    """新场景与某个已有场景是否相似。返回 (是否相似, 原因)。"""
    name_sim = text_similarity(new.get("title", ""), existing.get("title", ""))
    if name_sim >= SIMILARITY_THRESHOLD:
        return True, f"名称相似 ({name_sim:.0%})"

    trig_sim = text_similarity(new.get("trigger_event", ""), existing.get("trigger_event", ""))
    if trig_sim >= SIMILARITY_THRESHOLD:
        return True, f"触发事件相似 ({trig_sim:.0%})"

    kw_ov = keyword_overlap(new.get("keywords") or [], existing.get("keywords") or [])
    if kw_ov >= KEYWORD_OVERLAP_THRESHOLD:
        return True, f"关键词重叠 ({kw_ov:.0%})"

    if (name_sim >= 0.5 and trig_sim >= 0.5 and
            _within_time_window(new.get("created_at"), existing.get("created_at"))):
        return True, f"综合相近 (名{name_sim:.0%}/事件{trig_sim:.0%})"
    return False, ""


def find_duplicate(new: dict, existing_scenes: List[dict]):
    """在已有场景里找第一个相似的，返回 (existing_dict, reason) 或 (None, '')。"""
    for ex in existing_scenes:
        sim, reason = is_similar(new, ex)
        if sim:
            return ex, reason
    return None, ""
