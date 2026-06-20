"""时节感知（吸收自 JD 的 seasonal_perception.py）。

基于 data/festivals.json（传统节日/现代节日/节气，日期 MM-DD），
找出临近的事件，供 SenseAgent 生成时节场景。
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from core.config import ROOT, SEASONAL_DAYS_AFTER, SEASONAL_DAYS_BEFORE

FESTIVALS_PATH = ROOT / "data" / "festivals.json"


def _load_festivals() -> Dict:
    try:
        with open(FESTIVALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[seasonal] 节日数据未找到: {FESTIVALS_PATH}")
        return {"traditional_festivals": [], "modern_festivals": [], "solar_terms": []}
    except Exception as e:  # noqa: BLE001
        print(f"[seasonal] 加载节日数据失败: {e}")
        return {"traditional_festivals": [], "modern_festivals": [], "solar_terms": []}


def _all_events() -> List[Dict]:
    d = _load_festivals()
    return (d.get("traditional_festivals", []) +
            d.get("modern_festivals", []) +
            d.get("solar_terms", []))


def parse_event_date(date_str: str, today: Optional[datetime] = None) -> datetime:
    """MM-DD → 当年（已过则取明年）的 datetime。"""
    today = today or datetime.now()
    try:
        month, day = map(int, date_str.split("-"))
        d = datetime(today.year, month, day)
        if d < today:
            d = datetime(today.year + 1, month, day)
        return d
    except Exception:  # noqa: BLE001
        return today


def get_current_seasonal_events(
    days_before: int = SEASONAL_DAYS_BEFORE,
    days_after: int = SEASONAL_DAYS_AFTER,
) -> List[Dict]:
    """获取当前窗口内的时节事件，按距离今天的天数排序。"""
    today = datetime.now()
    start = today - timedelta(days=days_before)
    end = today + timedelta(days=days_after)
    events: List[Dict] = []
    for ev in _all_events():
        d = parse_event_date(ev["date"], today)
        if start <= d <= end:
            events.append({**ev, "date_obj": d, "days_until": (d - today).days})
    events.sort(key=lambda x: abs(x["days_until"]))
    return events


def calculate_temporal_scope(event_date: datetime, days_until: int) -> str:
    """时节事件的时间范围（移植自 JD）。"""
    start = event_date - timedelta(days=7)
    end = event_date + timedelta(days=3)
    return f"{start.strftime('%Y-%m-%d')} 至 {end.strftime('%Y-%m-%d')}"
