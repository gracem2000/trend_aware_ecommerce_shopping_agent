"""感知 Agent：抓取热点 → 提取消费场景 → 入库（mock）。"""
from datetime import timedelta

from core.agents.base import BaseAgent
from core.database import SessionLocal, _write_lock
from core.models import Scene, now_utc
from core.seed import INITIAL_SCENES

# mock 抓取到的热点（与原 demo 一致）
HOTSPOTS = [
    "全国多地高温预警 跑步经济升温",
    "小红书露营话题累计曝光 50 亿",
    "居家健身视频播放量破百亿",
    "夏季防晒产品销量同比 +180%",
    "健康轻食风潮席卷社交媒体",
    "智能穿戴市场 Q2 销量同比 +45%",
]


class SenseAgent(BaseAgent):
    key = "sense"
    name = "感知 Agent"

    def run(self) -> int:
        self.status("running", "正在抓取全网热点...")
        self.log("info", "[INIT] 感知 Agent 启动")
        self.sleep(400)

        self.log("info", "[FETCH] 接入微博/小红书/抖音热点 API...")
        self.sleep(300)
        for h in HOTSPOTS:
            self.log("highlight", f"[HOT] 抓取到热点: {h}")
            self.sleep(80)

        self.log("info", "[LLM] 调用场景抽取模型 (mock)...")
        self.sleep(300)

        # 读已有场景标题（判重）
        with SessionLocal() as db:
            existing_titles = {t for (t,) in db.query(Scene.title).all()}

        to_insert = []
        for s in INITIAL_SCENES:
            if s["title"] in existing_titles:
                continue
            payload = dict(s)
            payload["expires_at"] = now_utc() + timedelta(hours=72)
            to_insert.append(Scene(**payload))

        # 写入（短事务，提交后立即释放写锁）
        if to_insert:
            with _write_lock, SessionLocal() as db:
                db.add_all(to_insert)
                db.commit()
            for s in to_insert:
                self.log("info", f"[EXTRACT] 新增场景: {s.title}")

        self.log("info", f"[STORE] 场景库当前 {len(existing_titles) + len(to_insert)} 条场景 (新增 {len(to_insert)} 条)")
        self.status("done", f"已更新 {len(to_insert)} 个新场景")
        self.log("info", "[DONE] 感知 Agent 完成")
        return len(to_insert)
