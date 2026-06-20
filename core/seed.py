"""种子数据 + 首次启动填充逻辑。

数据从原 main.py 的 INITIAL_PRODUCTS / INITIAL_SCENES / AGENT_DEFS 迁移。
tags / keywords 在 ORM 层是 JSON 列，直接传 list 即可。
"""
from datetime import timedelta

from core.models import AgentStatus, Product, Scene, now_utc

# 4 个 Agent 定义（key 与 agent_status.agent_name 对应）
AGENT_DEFS = [
    {"key": "sense",   "name": "感知 Agent",     "icon": "🛰️", "task": "抓取热点 / 提取消费场景"},
    {"key": "match",   "name": "挂品 Agent",     "icon": "🛒", "task": "场景-商品匹配 / 入关联库"},
    {"key": "copy",    "name": "导购生成 Agent", "icon": "✍️", "task": "生成推荐理由 / 标签"},
    {"key": "deliver", "name": "分发 Agent",     "icon": "📡", "task": "响应首页 / 搜索请求"},
]

INITIAL_SCENES = [
    {"title": "夏季户外运动场景", "description": "高温来袭，速干、防晒、便携装备需求激增",
     "target_user": "户外爱好者 / 跑者", "confidence": 0.92,
     "keywords": ["夏季", "户外", "运动", "速干", "防晒"], "source_hotspot": "全国多地高温预警 跑步经济升温"},
    {"title": "居家健身场景", "description": "足不出户，瑜伽、力量训练装备成新宠",
     "target_user": "都市白领 / 学生", "confidence": 0.88,
     "keywords": ["健身", "瑜伽", "居家", "运动", "蛋白"], "source_hotspot": "居家健身视频播放量破百亿"},
    {"title": "露营经济场景", "description": "精致露营持续走热，户外装备升级换代",
     "target_user": "亲子家庭 / 户外玩家", "confidence": 0.95,
     "keywords": ["露营", "户外", "帐篷", "野餐"], "source_hotspot": "小红书露营话题累计曝光 50 亿"},
    {"title": "美白防晒场景", "description": "防晒意识觉醒，防护产品全渠道爆卖",
     "target_user": "年轻女性 / 户外党", "confidence": 0.91,
     "keywords": ["防晒", "美白", "夏季", "护肤"], "source_hotspot": "夏季防晒产品销量同比 +180%"},
    {"title": "智能厨电场景", "description": "健康饮食理念带动智能厨电走入千家万户",
     "target_user": "年轻家庭 / 美食爱好者", "confidence": 0.85,
     "keywords": ["厨电", "智能", "厨房", "健康"], "source_hotspot": "健康轻食风潮席卷社交媒体"},
    {"title": "智能穿戴场景", "description": "健康监测需求带动智能穿戴品类持续增长",
     "target_user": "科技爱好者 / 健身人群", "confidence": 0.83,
     "keywords": ["智能", "手环", "监测", "数码"], "source_hotspot": "智能穿戴市场 Q2 销量同比 +45%"},
]

INITIAL_PRODUCTS = [
    {"sku_id": "JD-100001", "title": "便携式榨汁杯 USB 充电款",   "price": 89,  "original_price": 159, "shop_name": "绿野小铺",   "good_rate": "98%", "sales": "5.2万",  "category": "小家电", "icon_emoji": "🥤", "bg_color": "#5cd65c", "tags": ["高性价比", "便携"]},
    {"sku_id": "JD-100002", "title": "蓝牙耳机入耳式降噪长续航",  "price": 159, "original_price": 299, "shop_name": "声潮数码",   "good_rate": "97%", "sales": "12.8万", "category": "数码",   "icon_emoji": "🎧", "bg_color": "#b366ff", "tags": ["降噪", "热销"]},
    {"sku_id": "JD-100003", "title": "电动牙刷成人声波震动",      "price": 299, "original_price": 499, "shop_name": "齿白之家",   "good_rate": "99%", "sales": "8.3万",  "category": "个护",   "icon_emoji": "🪥", "bg_color": "#3aaaff", "tags": ["新品", "高性价比"]},
    {"sku_id": "JD-100004", "title": "防晒霜 SPF50+ 防水防汗",     "price": 79,  "original_price": 129, "shop_name": "美夏护肤",   "good_rate": "98%", "sales": "15.6万", "category": "美妆",   "icon_emoji": "🧴", "bg_color": "#ffd633", "tags": ["爆款潜力", "夏季必备"]},
    {"sku_id": "JD-100005", "title": "空气炸锅家用 5L 大容量",     "price": 399, "original_price": 699, "shop_name": "厨易旗舰店", "good_rate": "97%", "sales": "6.7万",  "category": "厨房",   "icon_emoji": "🍟", "bg_color": "#ff8c4d", "tags": ["新品", "智能"]},
    {"sku_id": "JD-100006", "title": "露营帐篷便携式 3-4 人防雨", "price": 599, "original_price": 899, "shop_name": "野趣户外",   "good_rate": "98%", "sales": "3.4万",  "category": "户外",   "icon_emoji": "⛺", "bg_color": "#2eb85c", "tags": ["全网热销", "露营"]},
    {"sku_id": "JD-100007", "title": "瑜伽垫加厚加宽防滑 NBR",     "price": 129, "original_price": 199, "shop_name": "悦动健身",   "good_rate": "99%", "sales": "9.1万",  "category": "运动",   "icon_emoji": "🧘", "bg_color": "#a280ff", "tags": ["高性价比", "健身"]},
    {"sku_id": "JD-100008", "title": "速干运动 T 恤 男士夏季透气", "price": 99,  "original_price": 169, "shop_name": "潮动运动",   "good_rate": "96%", "sales": "11.2万", "category": "服饰",   "icon_emoji": "👕", "bg_color": "#a8a8b8", "tags": ["夏季必备", "速干"]},
    {"sku_id": "JD-100009", "title": "便携折叠水壶 户外露营直饮",  "price": 69,  "original_price": 129, "shop_name": "野趣户外",   "good_rate": "97%", "sales": "2.1万",  "category": "户外",   "icon_emoji": "🚰", "bg_color": "#5cd65c", "tags": ["户外", "便携"]},
    {"sku_id": "JD-100010", "title": "智能手环 心率睡眠监测",      "price": 199, "original_price": 349, "shop_name": "声潮数码",   "good_rate": "96%", "sales": "7.8万",  "category": "数码",   "icon_emoji": "⌚", "bg_color": "#b366ff", "tags": ["新品", "智能"]},
    {"sku_id": "JD-100011", "title": "蛋白棒 健身代餐 6 支装",     "price": 49,  "original_price": 89,  "shop_name": "悦动健身",   "good_rate": "98%", "sales": "4.5万",  "category": "运动",   "icon_emoji": "🍫", "bg_color": "#3aaaff", "tags": ["健身", "高性价比"]},
    {"sku_id": "JD-100012", "title": "天幕帐篷 户外遮阳 4 米加宽", "price": 459, "original_price": 799, "shop_name": "野趣户外",   "good_rate": "98%", "sales": "1.9万",  "category": "户外",   "icon_emoji": "🏖️", "bg_color": "#2eb85c", "tags": ["露营", "全网热销"]},
]


def seed_if_empty(db):
    """仅当表为空时插入种子数据（幂等）。"""
    seeded = []

    if db.query(Product).count() == 0:
        for p in INITIAL_PRODUCTS:
            db.add(Product(**p))
        seeded.append(f"{len(INITIAL_PRODUCTS)} 商品")

    if db.query(Scene).count() == 0:
        for s in INITIAL_SCENES:
            payload = dict(s)
            payload["expires_at"] = now_utc() + timedelta(hours=72)
            db.add(Scene(**payload))
        seeded.append(f"{len(INITIAL_SCENES)} 场景")

    for a in AGENT_DEFS:
        if not db.query(AgentStatus).filter_by(agent_name=a["key"]).first():
            db.add(AgentStatus(agent_name=a["key"], status="idle", current_task=a["task"]))

    db.commit()
    return seeded
