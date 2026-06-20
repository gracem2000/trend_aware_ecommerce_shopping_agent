"""
热点电商导购系统 - FastAPI 后端
- 4 Agent 流水线（mock 演示模式）
- 6 个 REST API
- 自动调度（每 5 分钟）
- Supabase 持久化
"""
import asyncio
import json
import os
import random
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 把 supabase_client 加进 sys.path
sys.path.insert(0, str(Path(__file__).parent / "src" / "storage" / "database"))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from postgrest.exceptions import APIError
from supabase_client import get_supabase_client


# ============== 静态资源 ==============
ROOT = Path(__file__).parent
STATIC_DIR = ROOT

# ============== 工具 ==============
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def time_str(dt: Optional[datetime] = None) -> str:
    dt = dt or now_utc()
    return dt.strftime("%H:%M:%S")

def time_since(dt: Optional[datetime]) -> str:
    if not dt:
        return "--"
    delta = now_utc() - dt
    sec = int(delta.total_seconds())
    if sec < 60:
        return f"{sec} 秒前"
    if sec < 3600:
        return f"{sec // 60} 分钟前"
    return f"{sec // 3600} 小时前"

def random_choice(arr):
    return random.choice(arr) if arr else None

def random_range(a, b):
    return random.uniform(a, b)

# ============== Agent 状态 ==============
AGENT_DEFS = [
    {"key": "sense",   "name": "感知 Agent",   "icon": "🛰️", "task": "抓取热点 / 提取消费场景"},
    {"key": "match",   "name": "挂品 Agent",   "icon": "🛒", "task": "场景-商品匹配 / 入关联库"},
    {"key": "copy",    "name": "导购生成",     "icon": "✍️", "task": "生成推荐理由 / 标签"},
    {"key": "deliver", "name": "分发 Agent",   "icon": "📡", "task": "响应首页 / 搜索请求"},
]

# 调度器状态
pipeline_state = {
    "running": False,
    "last_run_at": None,
    "next_run_at": None,
    "current_agent": None,
    "log_id_counter": 0,
}

# ============== DB 辅助函数 ==============
def db():
    return get_supabase_client()

def try_execute(fn, err_msg="操作失败"):
    """包装 try/except，捕获 APIError"""
    try:
        return fn()
    except APIError as e:
        raise HTTPException(status_code=500, detail=f"{err_msg}: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{err_msg}: {str(e)}")

# ============== 日志函数 ==============
def write_log(agent_name: str, level: str, message: str) -> Dict[str, Any]:
    """写一条 Agent 日志到数据库"""
    pipeline_state["log_id_counter"] += 1
    entry = {
        "id": pipeline_state["log_id_counter"],
        "agent_name": agent_name,
        "level": level,
        "message": message,
        "created_at": now_utc().isoformat(),
    }
    def _do():
        db().table("agent_logs").insert({
            "agent_name": agent_name,
            "level": level,
            "message": message,
        }).execute()
    try:
        _do()
    except APIError as e:
        print(f"[warn] 写日志失败: {e.message}")
    return entry

def set_agent_status(agent_name: str, status: str, task: Optional[str] = None):
    """更新 Agent 状态"""
    payload: Dict[str, Any] = {"status": status, "updated_at": now_utc().isoformat()}
    if task is not None:
        payload["current_task"] = task
    if status in ("done", "failed"):
        payload["last_run_at"] = now_utc().isoformat()

    def _do():
        # 存在则更新，不存在则插入
        r = db().table("agent_status").select("agent_name").eq("agent_name", agent_name).execute()
        if r.data:
            db().table("agent_status").update(payload).eq("agent_name", agent_name).execute()
        else:
            payload["agent_name"] = agent_name
            payload["current_task"] = task or "等待任务..."
            db().table("agent_status").insert(payload).execute()
    try:
        _do()
    except APIError as e:
        print(f"[warn] 更新状态失败: {e.message}")

def get_all_agent_status() -> List[Dict[str, Any]]:
    r = db().table("agent_status").select("*").execute()
    return r.data or []

def get_recent_logs(limit_per_agent: int = 15) -> Dict[str, List[Dict[str, Any]]]:
    """获取每个 Agent 的最近 N 条日志"""
    result = {a["key"]: [] for a in AGENT_DEFS}
    try:
        # 一次性拉最近 200 条
        r = db().table("agent_logs").select("*").order("id", desc=True).limit(200).execute()
        rows = r.data or []
        for row in rows:
            name = row["agent_name"]
            if name in result and len(result[name]) < limit_per_agent:
                result[name].append({
                    "id": row["id"],
                    "time": time_str(_parse_dt(row.get("created_at"))),
                    "level": row.get("level", "info"),
                    "message": row.get("message", ""),
                })
    except APIError as e:
        print(f"[warn] 拉日志失败: {e.message}")
    return result

def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

# ============== 初始演示数据 ==============
INITIAL_SCENES = [
    {"title": "夏季户外运动场景", "description": "高温来袭，速干、防晒、便携装备需求激增", "target_user": "户外爱好者 / 跑者", "confidence": 0.92, "keywords": ["夏季", "户外", "运动", "速干", "防晒"], "source_hotspot": "全国多地高温预警 跑步经济升温"},
    {"title": "居家健身场景",     "description": "足不出户，瑜伽、力量训练装备成新宠",         "target_user": "都市白领 / 学生",   "confidence": 0.88, "keywords": ["健身", "瑜伽", "居家", "运动", "蛋白"], "source_hotspot": "居家健身视频播放量破百亿"},
    {"title": "露营经济场景",     "description": "精致露营持续走热，户外装备升级换代",         "target_user": "亲子家庭 / 户外玩家", "confidence": 0.95, "keywords": ["露营", "户外", "帐篷", "野餐"], "source_hotspot": "小红书露营话题累计曝光 50 亿"},
    {"title": "美白防晒场景",     "description": "防晒意识觉醒，防护产品全渠道爆卖",         "target_user": "年轻女性 / 户外党",   "confidence": 0.91, "keywords": ["防晒", "美白", "夏季", "护肤"], "source_hotspot": "夏季防晒产品销量同比 +180%"},
    {"title": "智能厨电场景",     "description": "健康饮食理念带动智能厨电走入千家万户",     "target_user": "年轻家庭 / 美食爱好者", "confidence": 0.85, "keywords": ["厨电", "智能", "厨房", "健康"], "source_hotspot": "健康轻食风潮席卷社交媒体"},
    {"title": "智能穿戴场景",     "description": "健康监测需求带动智能穿戴品类持续增长",     "target_user": "科技爱好者 / 健身人群", "confidence": 0.83, "keywords": ["智能", "手环", "监测", "数码"], "source_hotspot": "智能穿戴市场 Q2 销量同比 +45%"},
]

INITIAL_PRODUCTS = [
    {"sku_id": "JD-100001", "title": "便携式榨汁杯 USB 充电款",     "price": 89,  "original_price": 159, "shop_name": "绿野小铺",   "good_rate": "98%", "sales": "5.2万",  "category": "小家电", "icon_emoji": "💚", "bg_color": "#5cd65c", "sprite": "juicer",     "tags": ["高性价比", "便携"]},
    {"sku_id": "JD-100002", "title": "蓝牙耳机入耳式降噪长续航",     "price": 159, "original_price": 299, "shop_name": "声潮数码",   "good_rate": "97%", "sales": "12.8万", "category": "数码",   "icon_emoji": "💜", "bg_color": "#b366ff", "sprite": "earphone",   "tags": ["降噪", "热销"]},
    {"sku_id": "JD-100003", "title": "电动牙刷成人声波震动",         "price": 299, "original_price": 499, "shop_name": "齿白之家",   "good_rate": "99%", "sales": "8.3万",  "category": "个护",   "icon_emoji": "🔵", "bg_color": "#3aaaff", "sprite": "toothbrush", "tags": ["新品", "高性价比"]},
    {"sku_id": "JD-100004", "title": "防晒霜 SPF50+ 防水防汗",      "price": 79,  "original_price": 129, "shop_name": "美夏护肤",   "good_rate": "98%", "sales": "15.6万", "category": "美妆",   "icon_emoji": "🟡", "bg_color": "#ffd633", "sprite": "sunscreen",  "tags": ["爆款潜力", "夏季必备"]},
    {"sku_id": "JD-100005", "title": "空气炸锅家用 5L 大容量",      "price": 399, "original_price": 699, "shop_name": "厨易旗舰店", "good_rate": "97%", "sales": "6.7万",  "category": "厨房",   "icon_emoji": "🟠", "bg_color": "#ff8c4d", "sprite": "airfryer",   "tags": ["新品", "智能"]},
    {"sku_id": "JD-100006", "title": "露营帐篷便携式 3-4 人防雨",   "price": 599, "original_price": 899, "shop_name": "野趣户外",   "good_rate": "98%", "sales": "3.4万",  "category": "户外",   "icon_emoji": "🟢", "bg_color": "#2eb85c", "sprite": "tent",       "tags": ["全网热销", "露营"]},
    {"sku_id": "JD-100007", "title": "瑜伽垫加厚加宽防滑 NBR",      "price": 129, "original_price": 199, "shop_name": "悦动健身",   "good_rate": "99%", "sales": "9.1万",  "category": "运动",   "icon_emoji": "🟣", "bg_color": "#a280ff", "sprite": "yogamat",    "tags": ["高性价比", "健身"]},
    {"sku_id": "JD-100008", "title": "速干运动 T 恤 男士夏季透气",   "price": 99,  "original_price": 169, "shop_name": "潮动运动",   "good_rate": "96%", "sales": "11.2万", "category": "服饰",   "icon_emoji": "⚪", "bg_color": "#a8a8b8", "sprite": "tshirt",     "tags": ["夏季必备", "速干"]},
    {"sku_id": "JD-100009", "title": "便携折叠水壶 户外露营直饮",   "price": 69,  "original_price": 129, "shop_name": "野趣户外",   "good_rate": "97%", "sales": "2.1万",  "category": "户外",   "icon_emoji": "🟢", "bg_color": "#5cd65c", "sprite": "juicer",     "tags": ["户外", "便携"]},
    {"sku_id": "JD-100010", "title": "智能手环 心率睡眠监测",       "price": 199, "original_price": 349, "shop_name": "声潮数码",   "good_rate": "96%", "sales": "7.8万",  "category": "数码",   "icon_emoji": "💜", "bg_color": "#b366ff", "sprite": "earphone",   "tags": ["新品", "智能"]},
    {"sku_id": "JD-100011", "title": "蛋白棒 健身代餐 6 支装",      "price": 49,  "original_price": 89,  "shop_name": "悦动健身",   "good_rate": "98%", "sales": "4.5万",  "category": "运动",   "icon_emoji": "🔵", "bg_color": "#3aaaff", "sprite": "toothbrush", "tags": ["健身", "高性价比"]},
    {"sku_id": "JD-100012", "title": "天幕帐篷 户外遮阳 4 米加宽",  "price": 459, "original_price": 799, "shop_name": "野趣户外",   "good_rate": "98%", "sales": "1.9万",  "category": "户外",   "icon_emoji": "🟢", "bg_color": "#2eb85c", "sprite": "tent",       "tags": ["露营", "全网热销"]},
]

async def seed_initial_data():
    """首次启动时插入演示数据（仅当表为空时）"""
    # 1. 商品
    r = db().table("products").select("id", count="exact").limit(1).execute()
    if not (r.count and r.count > 0):
        print("[seed] 插入初始商品数据...")
        for p in INITIAL_PRODUCTS:
            payload = dict(p)
            payload["tags"] = json.dumps(payload["tags"])
            db().table("products").insert(payload).execute()
    # 2. 场景
    r = db().table("scenes").select("id", count="exact").limit(1).execute()
    if not (r.count and r.count > 0):
        print("[seed] 插入初始场景数据...")
        for s in INITIAL_SCENES:
            payload = dict(s)
            payload["keywords"] = json.dumps(payload["keywords"])
            payload["expires_at"] = (now_utc() + timedelta(hours=72)).isoformat()
            db().table("scenes").insert(payload).execute()
    # 3. Agent 状态（4 个）
    for a in AGENT_DEFS:
        try:
            r = db().table("agent_status").select("agent_name").eq("agent_name", a["key"]).execute()
            if not r.data:
                db().table("agent_status").insert({
                    "agent_name": a["key"],
                    "status": "idle",
                    "current_task": a["task"],
                }).execute()
        except APIError as e:
            print(f"[seed] 初始化 {a['key']} 状态失败: {e.message}")

# ============== 4 Agent 流水线 ==============
async def sleep_ms(ms: int):
    await asyncio.sleep(ms / 1000)

async def run_sense_agent() -> List[int]:
    """感知 Agent：抓取热点 → 提取场景 → 入库"""
    k = "sense"
    set_agent_status(k, "running", "正在抓取全网热点...")
    write_log(k, "info", "[INIT] 感知 Agent 启动")
    await sleep_ms(400)

    write_log(k, "info", "[FETCH] 接入微博/小红书/抖音热点 API...")
    await sleep_ms(300)

    hotspots = [
        "全国多地高温预警 跑步经济升温",
        "小红书露营话题累计曝光 50 亿",
        "居家健身视频播放量破百亿",
        "夏季防晒产品销量同比 +180%",
        "健康轻食风潮席卷社交媒体",
        "智能穿戴市场 Q2 销量同比 +45%",
    ]
    for h in hotspots:
        write_log(k, "highlight", f"[HOT] 抓取到热点: {h}")
        await sleep_ms(80)

    write_log(k, "info", "[LLM] 调用场景抽取模型 (mock)...")
    await sleep_ms(300)

    # 把 INITIAL_SCENES 入库（演示模式），按 title 判重
    existing = db().table("scenes").select("title").execute().data or []
    existing_titles = {row["title"] for row in existing}

    inserted_ids: List[int] = []
    for s in INITIAL_SCENES:
        if s["title"] in existing_titles:
            continue
        payload = dict(s)
        payload["keywords"] = json.dumps(payload["keywords"])
        payload["expires_at"] = (now_utc() + timedelta(hours=72)).isoformat()
        r = db().table("scenes").insert(payload).execute()
        if r.data:
            inserted_ids.append(r.data[0]["id"])
            write_log(k, "info", f"[EXTRACT] 新增场景: {s['title']}")

    write_log(k, "info", f"[STORE] 场景库当前 {len(existing_titles) + len(inserted_ids)} 条场景 (新增 {len(inserted_ids)} 条)")
    set_agent_status(k, "done", f"已更新 {len(inserted_ids)} 个新场景")
    write_log(k, "info", "[DONE] 感知 Agent 完成")
    return inserted_ids


async def run_match_agent() -> int:
    """挂品 Agent：场景-商品匹配 → 入关联库"""
    k = "match"
    set_agent_status(k, "running", "正在匹配场景-商品...")
    write_log(k, "info", "[INIT] 挂品 Agent 启动")
    await sleep_ms(300)

    # 读取近 24h 场景
    cutoff = (now_utc() - timedelta(hours=24)).isoformat()
    scenes = db().table("scenes").select("*").gte("created_at", cutoff).execute().data or []
    write_log(k, "info", f"[QUERY] 读取近 24h 场景: {len(scenes)} 条")
    await sleep_ms(200)

    # 读取商品
    products = db().table("products").select("*").execute().data or []
    write_log(k, "info", f"[LOAD] 商品库 products: {len(products)} SKU")
    await sleep_ms(200)

    # 清空旧关联（24h 前）+ 新建
    db().table("scene_products").delete().lt("created_at", cutoff).execute()

    total_pairs = 0
    for s in scenes:
        s_keywords = s.get("keywords", [])
        if isinstance(s_keywords, str):
            s_keywords = json.loads(s_keywords)
        # 匹配：商品 tags ∩ 场景 keywords，或 category ∈ keywords
        candidates = []
        for p in products:
            p_tags = p.get("tags", [])
            if isinstance(p_tags, str):
                p_tags = json.loads(p_tags)
            if any(t in s_keywords for t in p_tags) or p.get("category") in s_keywords:
                candidates.append(p)
        if not candidates:
            candidates = random.sample(products, min(4, len(products)))
        else:
            candidates = candidates[:4]

        for p in candidates:
            score = round(random_range(0.65, 0.97), 2)
            db().table("scene_products").insert({
                "scene_id": s["id"],
                "product_id": p["id"],
                "match_score": score,
            }).execute()
            total_pairs += 1
            write_log(k, "info", f"[MATCH] {s['title'][:6]} → {p['title'][:8]} ({int(score*100)}%)")
            await sleep_ms(30)

    write_log(k, "info", f"[STORE] 写入场景-商品关联: {total_pairs} 条")
    set_agent_status(k, "done", f"已建立 {total_pairs} 条关联")
    write_log(k, "info", "[DONE] 挂品 Agent 完成")
    return total_pairs


async def run_copy_agent() -> int:
    """导购生成 Agent：高分关联 → 推荐理由 + 标签 → 入库"""
    k = "copy"
    set_agent_status(k, "running", "正在生成推荐理由...")
    write_log(k, "info", "[INIT] 导购生成 Agent 启动")
    await sleep_ms(300)

    write_log(k, "info", "[QUERY] 读取高分关联 (score > 0.7)")
    await sleep_ms(200)
    # 拉所有高分关联
    sp = db().table("scene_products").select("scene_id,product_id,match_score").gte("match_score", 0.7).order("match_score", desc=True).limit(50).execute().data or []
    write_log(k, "info", "[LLM] 调用文案生成模型 (mock)...")
    await sleep_ms(200)

    # 批量加载场景和商品
    scene_ids = list({r["scene_id"] for r in sp})
    product_ids = list({r["product_id"] for r in sp})
    scenes = {r["id"]: r for r in (db().table("scenes").select("*").in_("id", scene_ids).execute().data or [])} if scene_ids else {}
    products = {r["id"]: r for r in (db().table("products").select("*").in_("id", product_ids).execute().data or [])} if product_ids else {}

    templates = [
        "针对【{scene}】,这款【{product}】{highlight},是【{user}】的优质选择",
        "【{user}】都在买的【{product}】,完美匹配【{scene}】,{highlight}",
        "热门【{scene}】下,【{product}】凭借{highlight}登顶推荐榜",
    ]
    highlights = [
        "拥有超高性价比",
        "累计销量破万",
        "用户好评率超 98%",
        "本季新品,口碑爆款",
        "材质升级,体验翻倍",
    ]
    extra_tags = ["爆款潜力", "全网热销", "高性价比", "智能优选", "夏季必备"]

    # 清旧推荐
    cutoff = (now_utc() - timedelta(hours=1)).isoformat()
    db().table("recommendations").delete().lt("created_at", cutoff).execute()

    count = 0
    for r in sp:
        s = scenes.get(r["scene_id"])
        p = products.get(r["product_id"])
        if not s or not p:
            continue
        s_keywords = s.get("keywords", [])
        if isinstance(s_keywords, str):
            s_keywords = json.loads(s_keywords)
        p_tags = p.get("tags", [])
        if isinstance(p_tags, str):
            p_tags = json.loads(p_tags)

        reason = random_choice(templates)\
            .replace("{scene}", s["title"])\
            .replace("{product}", p["title"][:10])\
            .replace("{user}", s.get("target_user", "用户"))\
            .replace("{highlight}", random_choice(highlights))
        tag1 = random_choice(p_tags) if p_tags else "推荐"
        tag2 = random_choice(extra_tags)
        score = round(r["match_score"] * 0.6 + random_range(0.3, 0.4), 2)

        db().table("recommendations").insert({
            "scene_id": s["id"],
            "product_id": p["id"],
            "reason": reason,
            "tags": json.dumps([tag1, tag2]),
            "score": score,
        }).execute()
        count += 1
        write_log(k, "info", f"[GEN] {p['title'][:6]}... → {tag1}/{tag2}")

    write_log(k, "info", f"[STORE] 写入推荐库: {count} 条")
    set_agent_status(k, "done", f"已生成 {count} 条推荐")
    write_log(k, "info", "[DONE] 导购生成 Agent 完成")
    return count


async def run_deliver_agent() -> int:
    """分发 Agent：响应首页 / 搜索（这里是查询型）"""
    k = "deliver"
    set_agent_status(k, "running", "刷新首页推荐...")
    write_log(k, "info", "[INIT] 分发 Agent 启动")
    await sleep_ms(200)
    r = db().table("recommendations").select("id", count="exact").execute()
    n = r.count or 0
    write_log(k, "info", f"[FETCH] 推荐库现有 {n} 条")
    set_agent_status(k, "done", f"已下发 {n} 条到首页")
    write_log(k, "info", "[DONE] 分发 Agent 完成")
    return n


async def run_pipeline(trigger: str = "auto"):
    """完整流水线"""
    if pipeline_state["running"]:
        return {"ok": False, "message": "流水线正在运行"}

    pipeline_state["running"] = True
    pipeline_state["last_run_at"] = now_utc()
    pipeline_state["next_run_at"] = now_utc() + timedelta(minutes=5)
    write_log("system", "info", f"[PIPELINE] 启动 (trigger={trigger})")

    summary = {"trigger": trigger, "scenes_added": 0, "pairs": 0, "recommendations": 0}
    try:
        summary["scenes_added"] = len(await run_sense_agent())
        summary["pairs"] = await run_match_agent()
        summary["recommendations"] = await run_copy_agent()
        await run_deliver_agent()
        write_log("system", "info", f"[PIPELINE] 完成: 新增场景 {summary['scenes_added']} / 关联 {summary['pairs']} / 推荐 {summary['recommendations']}")
    except Exception as e:
        write_log("system", "error", f"[PIPELINE] 异常: {e}")
        summary["error"] = str(e)
    finally:
        # 所有 Agent 回到 idle
        for a in AGENT_DEFS:
            set_agent_status(a["key"], "idle", a["task"])
        pipeline_state["running"] = False
    return {"ok": True, "summary": summary}


# ============== 调度器 ==============
async def scheduler_loop():
    """每 5 分钟自动跑一次流水线"""
    await asyncio.sleep(5)  # 启动后 5s 跑一次
    while True:
        try:
            await run_pipeline("auto")
        except Exception as e:
            print(f"[scheduler] 异常: {e}")
        await asyncio.sleep(5 * 60)


# ============== FastAPI App ==============
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    print("[boot] 初始化初始数据...")
    try:
        await seed_initial_data()
    except Exception as e:
        print(f"[boot] 初始化失败: {e}")
    # 启动调度器
    task = asyncio.create_task(scheduler_loop())
    print("[boot] 调度器已启动 (每 5 分钟)")
    yield
    # 关闭时
    task.cancel()


app = FastAPI(title="热点电商导购 API", lifespan=lifespan)

# CORS（开发环境允许所有源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源
app.mount("/styles", StaticFiles(directory=str(ROOT / "styles")), name="styles")

# 根目录下的 script.js / DESIGN.md / AGENTS.md / 兜底页面
@app.get("/script.js")
def serve_script():
    return FileResponse(str(ROOT / "script.js"), media_type="application/javascript")

@app.get("/favicon.ico")
def favicon():
    return JSONResponse(status_code=204, content=None)


# ============== API: 首页 + 搜索 ==============
@app.get("/api/recommend")
def api_recommend(limit: int = Query(20, ge=1, le=100)):
    """首页推荐: top N 推荐"""
    def _do():
        r = db().table("recommendations").select("*").order("score", desc=True).limit(limit).execute()
        return _hydrate_recommendations(r.data or [])
    return try_execute(_do, "查询推荐失败")


@app.get("/api/search")
def api_search(q: str = Query("", min_length=0, max_length=200), limit: int = Query(20, ge=1, le=100)):
    """搜索: 商品标题/店铺/类目/标签 + 场景关键词 + 推荐理由"""
    if not q.strip():
        return api_recommend(limit=limit)

    query = q.strip()
    write_log("deliver", "info", f"[SEARCH] 关键词: {query}")

    # 1. 商品匹配
    product_ids: set = set()
    # 标题/店铺/类目用 ilike
    for col in ("title", "shop_name", "category"):
        r = db().table("products").select("id").ilike(col, f"%{query}%").execute()
        for row in (r.data or []):
            product_ids.add(row["id"])
    # 标签是 jsonb，转 text 后 ilike（Supabase SDK 暂不支持 ::text cast）
    r = db().table("products").select("id, tags").execute()
    for row in (r.data or []):
        tags = row.get("tags")
        if isinstance(tags, list):
            for t in tags:
                if query in str(t):
                    product_ids.add(row["id"])
                    break
        elif isinstance(tags, str):
            # 已经是 JSON 字符串化
            if query in tags:
                product_ids.add(row["id"])

    # 2. 场景关键词匹配
    scene_ids: set = set()
    r = db().table("scenes").select("id, keywords").execute()
    for row in (r.data or []):
        kws = row.get("keywords")
        if isinstance(kws, list):
            for k in kws:
                if query in str(k):
                    scene_ids.add(row["id"])
                    break
        elif isinstance(kws, str):
            if query in kws:
                scene_ids.add(row["id"])
    r = db().table("scenes").select("id").ilike("title", f"%{query}%").execute()
    for row in (r.data or []):
        scene_ids.add(row["id"])

    # 3. 取所有命中的推荐
    rec_ids: set = set()
    if product_ids:
        r = db().table("recommendations").select("id").in_("product_id", list(product_ids)).execute()
        for row in (r.data or []):
            rec_ids.add(row["id"])
    if scene_ids:
        r = db().table("recommendations").select("id").in_("scene_id", list(scene_ids)).execute()
        for row in (r.data or []):
            rec_ids.add(row["id"])
    # 4. 推荐理由中包含关键词
    r = db().table("recommendations").select("id").ilike("reason", f"%{query}%").execute()
    for row in (r.data or []):
        rec_ids.add(row["id"])

    if not rec_ids:
        return {"items": [], "total": 0, "query": query}

    r = db().table("recommendations").select("*").in_("id", list(rec_ids)).order("score", desc=True).limit(limit).execute()
    items = _hydrate_recommendations(r.data or [])
    return {"items": items, "total": len(items), "query": query}


# ============== API: 场景 ==============
@app.get("/api/scenes")
def api_scenes():
    def _do():
        r = db().table("scenes").select("*").order("confidence", desc=True).limit(50).execute()
        scenes = []
        for row in (r.data or []):
            kw = row.get("keywords", [])
            if isinstance(kw, str):
                kw = json.loads(kw)
            scenes.append({
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "target_user": row["target_user"],
                "confidence": row["confidence"],
                "keywords": kw,
                "source_hotspot": row.get("source_hotspot", ""),
                "created_at": row.get("created_at"),
            })
        return {"scenes": scenes, "total": len(scenes)}
    return try_execute(_do, "查询场景失败")


# ============== API: 商品 ==============
@app.get("/api/products")
def api_products(limit: int = Query(50, ge=1, le=200)):
    def _do():
        r = db().table("products").select("*").order("id").limit(limit).execute()
        items = [_serialize_product(row) for row in (r.data or [])]
        return {"items": items, "total": len(items)}
    return try_execute(_do, "查询商品失败")


# ============== API: Agent 日志 + 状态 ==============
@app.get("/api/agents/logs")
def api_agents_logs(limit_per_agent: int = Query(15, ge=1, le=100)):
    logs = get_recent_logs(limit_per_agent)
    return {"agents": [
        {
            "key": a["key"],
            "name": a["name"],
            "icon": a["icon"],
            "logs": logs.get(a["key"], []),
        }
        for a in AGENT_DEFS
    ]}


@app.get("/api/agents/status")
def api_agents_status():
    status_rows = {r["agent_name"]: r for r in get_all_agent_status()}
    agents = []
    for a in AGENT_DEFS:
        row = status_rows.get(a["key"], {})
        last_run = _parse_dt(row.get("last_run_at"))
        agents.append({
            "key": a["key"],
            "name": a["name"],
            "icon": a["icon"],
            "task": a["task"],
            "status": row.get("status", "idle"),
            "current_task": row.get("current_task", a["task"]),
            "last_run_at": row.get("last_run_at"),
            "last_run_ago": time_since(last_run),
        })
    return {
        "agents": agents,
        "pipeline": {
            "running": pipeline_state["running"],
            "last_run_at": pipeline_state["last_run_at"].isoformat() if pipeline_state["last_run_at"] else None,
            "last_run_ago": time_since(pipeline_state["last_run_at"]),
            "next_run_at": pipeline_state["next_run_at"].isoformat() if pipeline_state["next_run_at"] else None,
        },
    }


# ============== API: 手动触发流水线 ==============
@app.post("/api/run")
async def api_run():
    result = await run_pipeline("manual")
    return result


@app.get("/api/run/status")
def api_run_status():
    return {
        "running": pipeline_state["running"],
        "last_run_at": pipeline_state["last_run_at"].isoformat() if pipeline_state["last_run_at"] else None,
        "last_run_ago": time_since(pipeline_state["last_run_at"]),
        "next_run_at": pipeline_state["next_run_at"].isoformat() if pipeline_state["next_run_at"] else None,
    }


# ============== 辅助：序列化 ==============
def _serialize_product(row: Dict[str, Any]) -> Dict[str, Any]:
    tags = row.get("tags", [])
    if isinstance(tags, str):
        tags = json.loads(tags)
    return {
        "id": row["id"],
        "sku": row["sku_id"],
        "title": row["title"],
        "price": float(row["price"]) if row.get("price") is not None else 0,
        "origPrice": float(row["original_price"]) if row.get("original_price") else None,
        "shop": row["shop_name"],
        "goodRate": row.get("good_rate", "100%"),
        "sales": row.get("sales", "0"),
        "category": row.get("category", ""),
        "icon": row.get("icon_emoji", ""),
        "bgColor": row.get("bg_color", "#5cd65c"),
        "sprite": row.get("sprite", "juicer"),
        "tags": tags or [],
    }


def _hydrate_recommendations(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """把推荐行的 scene_id/product_id 展开为完整对象"""
    if not rows:
        return []
    scene_ids = list({r["scene_id"] for r in rows})
    product_ids = list({r["product_id"] for r in rows})
    scenes = {r["id"]: r for r in (db().table("scenes").select("*").in_("id", scene_ids).execute().data or [])} if scene_ids else {}
    products = {r["id"]: r for r in (db().table("products").select("*").in_("id", product_ids).execute().data or [])} if product_ids else {}

    items = []
    for r in rows:
        s = scenes.get(r["scene_id"], {})
        p = products.get(r["product_id"], {})
        rec_tags = r.get("tags", [])
        if isinstance(rec_tags, str):
            rec_tags = json.loads(rec_tags)
        s_keywords = s.get("keywords", [])
        if isinstance(s_keywords, str):
            s_keywords = json.loads(s_keywords)
        items.append({
            "id": r["id"],
            "scene_id": r["scene_id"],
            "product_id": r["product_id"],
            "score": float(r.get("score", 0)),
            "reason": r.get("reason", ""),
            "tags": rec_tags or [],
            "scene": {
                "id": s.get("id"),
                "title": s.get("title", ""),
                "description": s.get("description", ""),
                "keywords": s_keywords,
            } if s else None,
            "product": _serialize_product(p) if p else None,
        })
    return items


# ============== 静态首页 ==============
@app.get("/")
def index():
    return FileResponse(str(ROOT / "index.html"))


@app.get("/favicon.ico")
def favicon():
    return JSONResponse(status_code=204, content=None)


# ============== 健康检查 ==============
@app.get("/healthz")
def healthz():
    return {"ok": True, "ts": now_utc().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("DEPLOY_RUN_PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
