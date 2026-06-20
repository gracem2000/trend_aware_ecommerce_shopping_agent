"""感知 Agent：真实版（吸收 JD）。

抓百度热搜（失败回退内置）→ LLM 场景挖掘（mock/glm）→ 智能去重 → 入库；
再挖掘临近节日/节气的时节场景。
无 GLM key 时自动走 mock LLM，系统仍可演示。
"""
from typing import List

from core.agents.base import BaseAgent
from core.config import HOT_FETCH_LIMIT, SCENE_LIMIT_PER_RUN
from core.llm import is_mock
from core.perception import dedup, hot, scene_builder, seasonal
from core import repository as r

# 抓取失败时的内置兜底热点
MOCK_HOTSPOTS = [
    "全国多地高温预警 跑步经济升温",
    "小红书露营话题累计曝光 50 亿",
    "居家健身视频播放量破百亿",
    "夏季防晒产品销量同比 +180%",
    "健康轻食风潮席卷社交媒体",
    "智能穿戴市场 Q2 销量同比 +45%",
]

# 每次最多挖掘几个时节场景（控 LLM 成本）
SEASONAL_CAP = 2


class SenseAgent(BaseAgent):
    key = "sense"
    name = "感知 Agent"

    def run(self) -> int:
        self.status("running", "正在抓取全网热点...")
        self.log("info", "[INIT] 感知 Agent 启动")
        self.sleep(300)

        # 1. 抓取热点（失败回退）
        self.log("info", "[FETCH] 接入百度热搜...")
        topics = hot.fetch_baidu_hot(limit=HOT_FETCH_LIMIT)
        if topics:
            for t in topics:
                self.log("highlight", f"[HOT] {t['title'][:40]}")
            titles = [t["title"] for t in topics]
            self.log("info", f"[FETCH] 百度热搜抓到 {len(titles)} 条")
        else:
            self.log("warn", "[FETCH] 百度抓取失败/为空，回退内置热点")
            titles = MOCK_HOTSPOTS[:]
            for t in titles:
                self.log("highlight", f"[HOT](内置) {t}")

        existing: List[dict] = r.get_scenes(100)
        inserted = skipped = 0

        # 2. 热点场景挖掘
        mode = "mock" if is_mock() else "GLM"
        self.log("info", f"[LLM] 调用场景挖掘模型 ({mode})，处理前 {SCENE_LIMIT_PER_RUN} 条...")
        for topic in titles[:SCENE_LIMIT_PER_RUN]:
            ok = self._mine_one(topic, source="hotspot", existing=existing)
            if ok:
                inserted += 1
            else:
                skipped += 1

        # 3. 时节场景挖掘
        events = seasonal.get_current_seasonal_events()
        if events:
            cap = min(SEASONAL_CAP, len(events))
            self.log("info", f"[SEASON] 临近时节事件 {len(events)} 个，挖掘前 {cap} 个")
            for ev in events[:cap]:
                ok = self._mine_one(
                    ev["name"], source="seasonal", source_detail=ev["name"],
                    existing=existing,
                    temporal_override=seasonal.calculate_temporal_scope(ev["date_obj"], ev["days_until"]),
                )
                if ok:
                    inserted += 1
                else:
                    skipped += 1

        self.log("info", f"[STORE] 场景库新增 {inserted} / 去重跳过 {skipped}")
        self.status("done", f"已更新 {inserted} 个新场景")
        self.log("info", "[DONE] 感知 Agent 完成")
        return inserted

    def _mine_one(self, topic: str, source: str, existing: List[dict],
                  source_detail: str = "", temporal_override: str = "") -> bool:
        """挖掘单条主题：LLM 生成 → 组装 → 去重 → 入库。返回是否成功插入。"""
        self.sleep(200)
        data = self.llm.generate_scene(topic)
        scene = scene_builder.build_scene(topic, data, source=source, source_detail=source_detail)
        if temporal_override:
            cur = scene.get("temporal_scope") or ""
            if (not cur) or "全年" in cur or "未知" in cur:
                scene["temporal_scope"] = temporal_override

        dup, reason = dedup.find_duplicate(scene, existing)
        if dup:
            tag = "时节" if source == "seasonal" else ""
            self.log("info", f"[SKIP] {tag}「{scene['title']}」与已有「{dup['title']}」重复: {reason}")
            return False

        sid = r.insert_scene(scene)
        existing.insert(0, {**scene, "id": sid, "created_at": None})
        label = "时节场景" if source == "seasonal" else "场景"
        self.log("info", f"[EXTRACT] 新增{label}: {scene['title']}（{scene.get('scene_type') or source}）")
        return True
