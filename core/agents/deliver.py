"""分发 Agent：刷新首页推荐计数（查询型）。"""
from core.agents.base import BaseAgent
from core.database import SessionLocal
from core.models import Recommendation


class DeliverAgent(BaseAgent):
    key = "deliver"
    name = "分发 Agent"

    def run(self) -> int:
        self.status("running", "刷新首页推荐...")
        self.log("info", "[INIT] 分发 Agent 启动")
        self.sleep(200)

        with SessionLocal() as db:
            n = db.query(Recommendation).count()

        self.log("info", f"[FETCH] 推荐库现有 {n} 条")
        self.status("done", f"已下发 {n} 条到首页")
        self.log("info", "[DONE] 分发 Agent 完成")
        return n
