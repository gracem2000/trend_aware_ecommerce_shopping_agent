"""挂品 Agent：原理化匹配（吸收 JD 的 product_matching）。

打分策略（替换原随机分）：
- 标题命中关键词: +1.0
- 标签命中关键词: +0.8（每词计一次）
- 类目命中关键词: +0.5
按关键词数归一化到 0-1，过滤 < MIN_CONFIDENCE，取 top N。
"""
from core.agents.base import BaseAgent
from core.config import MIN_CONFIDENCE
from core.database import SessionLocal, _write_lock
from core.models import Product, Scene, SceneProduct

TOP_N_PER_SCENE = 4


class MatchAgent(BaseAgent):
    key = "match"
    name = "挂品 Agent"

    def run(self) -> int:
        self.status("running", "正在匹配场景-商品...")
        self.log("info", "[INIT] 挂品 Agent 启动")
        self.sleep(300)

        with SessionLocal() as db:
            scenes = db.query(Scene).all()
            products = db.query(Product).all()
            scene_data = [{"id": s.id, "title": s.title, "keywords": s.keywords or []} for s in scenes]
            product_data = [{"id": p.id, "title": p.title, "category": p.category, "tags": p.tags or []} for p in products]

        self.log("info", f"[QUERY] 场景: {len(scene_data)} 条")
        self.sleep(200)
        self.log("info", f"[LOAD] 商品库: {len(product_data)} SKU")
        self.sleep(200)

        pairs = []  # (scene_id, product_id, score, scene_title, product_title)
        for s in scene_data:
            scored = [(sc, p) for p in product_data
                      if (sc := self._relevance(p, s["keywords"])) >= MIN_CONFIDENCE]
            scored.sort(key=lambda x: x[0], reverse=True)
            for sc, p in scored[:TOP_N_PER_SCENE]:
                pairs.append((s["id"], p["id"], round(sc, 3), s["title"], p["title"]))

        # 每次全量重建关联：先清空再写入，避免跨多次流水线运行累积重复 (scene_id, product_id)
        with _write_lock, SessionLocal() as db:
            db.query(SceneProduct).delete(synchronize_session=False)
            db.add_all([SceneProduct(scene_id=sid, product_id=pid, match_score=sc)
                        for sid, pid, sc, _, _ in pairs])
            db.commit()

        for _, _, sc, st, pt in pairs:
            self.log("info", f"[MATCH] {st[:6]} → {pt[:8]} ({int(sc * 100)}%)")
            self.sleep(20)

        self.log("info", f"[STORE] 写入场景-商品关联: {len(pairs)} 条")
        self.status("done", f"已建立 {len(pairs)} 条关联")
        self.log("info", "[DONE] 挂品 Agent 完成")
        return len(pairs)

    @staticmethod
    def _relevance(product: dict, keywords) -> float:
        """商品与场景关键词的相关性（移植自 JD）。"""
        keywords = keywords or []
        if not keywords:
            return 0.0
        score = 0.0
        title = (product["title"] or "").lower()
        category = (product["category"] or "").lower()
        tags = product["tags"] or []
        for kw in keywords:
            kw = (kw or "").lower().strip()
            if not kw:
                continue
            if kw in title:
                score += 1.0
            for tag in tags:
                if kw in (tag or "").lower():
                    score += 0.8
                    break
            if kw in category:
                score += 0.5
        return min(score / len(keywords), 1.0)
