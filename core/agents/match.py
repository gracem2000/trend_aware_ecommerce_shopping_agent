"""挂品 Agent：场景-商品匹配 → 入关联库（mock 评分）。"""
import random
from datetime import timedelta

from core.agents.base import BaseAgent
from core.database import SessionLocal, _write_lock
from core.models import Product, Scene, SceneProduct, now_utc


class MatchAgent(BaseAgent):
    key = "match"
    name = "挂品 Agent"

    def run(self) -> int:
        self.status("running", "正在匹配场景-商品...")
        self.log("info", "[INIT] 挂品 Agent 启动")
        self.sleep(300)

        cutoff = now_utc() - timedelta(hours=24)
        with SessionLocal() as db:
            scenes = db.query(Scene).filter(Scene.created_at >= cutoff).all()
            products = db.query(Product).all()
            # 提取为普通数据，避免 session 关闭后访问出错
            scene_data = [{
                "id": s.id, "title": s.title, "keywords": s.keywords or [],
            } for s in scenes]
            product_data = [{
                "id": p.id, "title": p.title, "category": p.category, "tags": p.tags or [],
            } for p in products]

        self.log("info", f"[QUERY] 读取近 24h 场景: {len(scene_data)} 条")
        self.sleep(200)
        self.log("info", f"[LOAD] 商品库 products: {len(product_data)} SKU")
        self.sleep(200)

        # 匹配：商品 tags ∩ 场景 keywords，或 category ∈ keywords；否则随机兜底
        pairs = []  # (scene_id, product_id, score, scene_title, product_title)
        for s in scene_data:
            kws = s["keywords"]
            candidates = [
                p for p in product_data
                if any(t in kws for t in p["tags"]) or p["category"] in kws
            ]
            if not candidates:
                candidates = random.sample(product_data, min(4, len(product_data)))
            else:
                candidates = candidates[:4]
            for p in candidates:
                score = round(random.uniform(0.65, 0.97), 2)
                pairs.append((s["id"], p["id"], score, s["title"], p["title"]))

        # 清旧关联（24h 前）+ 写入（一个短事务）
        with _write_lock, SessionLocal() as db:
            db.query(SceneProduct).filter(SceneProduct.created_at < cutoff).delete(synchronize_session=False)
            db.add_all([
                SceneProduct(scene_id=sid, product_id=pid, match_score=score)
                for sid, pid, score, _, _ in pairs
            ])
            db.commit()

        for _, _, score, stitle, ptitle in pairs:
            self.log("info", f"[MATCH] {stitle[:6]} → {ptitle[:8]} ({int(score * 100)}%)")
            self.sleep(30)

        self.log("info", f"[STORE] 写入场景-商品关联: {len(pairs)} 条")
        self.status("done", f"已建立 {len(pairs)} 条关联")
        self.log("info", "[DONE] 挂品 Agent 完成")
        return len(pairs)
