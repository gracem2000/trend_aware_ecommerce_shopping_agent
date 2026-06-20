"""导购生成 Agent：高分关联 → 推荐理由 + 标签 → 入库。

文案生成走 self.llm.complete()（mock 返回模板化文案）；后续接真模型只换 LLMClient。
"""
import random
from datetime import timedelta

from core.agents.base import BaseAgent
from core.database import SessionLocal, _write_lock
from core.models import Product, Recommendation, Scene, SceneProduct, now_utc

EXTRA_TAGS = ["爆款潜力", "全网热销", "高性价比", "智能优选", "夏季必备"]


class CopyAgent(BaseAgent):
    key = "copy"
    name = "导购生成 Agent"

    def run(self) -> int:
        self.status("running", "正在生成推荐理由...")
        self.log("info", "[INIT] 导购生成 Agent 启动")
        self.sleep(300)

        self.log("info", "[QUERY] 读取高分关联 (score > 0.7)")
        self.sleep(200)

        with SessionLocal() as db:
            sp_rows = (
                db.query(SceneProduct)
                .filter(SceneProduct.match_score >= 0.7)
                .order_by(SceneProduct.match_score.desc())
                .limit(50)
                .all()
            )
            scene_ids = {r.scene_id for r in sp_rows}
            product_ids = {r.product_id for r in sp_rows}
            scenes = {
                s.id: {"title": s.title, "target_user": s.target_user}
                for s in db.query(Scene).filter(Scene.id.in_(scene_ids)).all()
            } if scene_ids else {}
            products = {
                p.id: {"title": p.title, "tags": p.tags or []}
                for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
            } if product_ids else {}
            sp_data = [(r.scene_id, r.product_id, float(r.match_score)) for r in sp_rows]

        self.log("info", "[LLM] 调用文案生成模型 (mock)...")
        self.sleep(200)

        new_recs = []
        log_lines = []
        for scene_id, product_id, match_score in sp_data:
            s = scenes.get(scene_id)
            p = products.get(product_id)
            if not s or not p:
                continue
            prompt = (
                "任务：生成推荐理由\n"
                f"场景：{s['title']}\n"
                f"商品：{p['title']}\n"
                f"人群：{s['target_user']}\n"
                "亮点：\n"
            )
            reason = self.llm.complete(prompt)
            tag1 = random.choice(p["tags"]) if p["tags"] else "推荐"
            tag2 = random.choice(EXTRA_TAGS)
            score = round(match_score * 0.6 + random.uniform(0.3, 0.4), 2)
            new_recs.append(Recommendation(
                scene_id=scene_id, product_id=product_id,
                reason=reason, tags=[tag1, tag2], score=score,
            ))
            log_lines.append((p["title"][:6], tag1, tag2))

        cutoff = now_utc() - timedelta(hours=1)
        with _write_lock, SessionLocal() as db:
            db.query(Recommendation).filter(Recommendation.created_at < cutoff).delete(synchronize_session=False)
            db.add_all(new_recs)
            db.commit()

        for ptitle, t1, t2 in log_lines:
            self.log("info", f"[GEN] {ptitle}... → {t1}/{t2}")

        self.log("info", f"[STORE] 写入推荐库: {len(new_recs)} 条")
        self.status("done", f"已生成 {len(new_recs)} 条推荐")
        self.log("info", "[DONE] 导购生成 Agent 完成")
        return len(new_recs)
