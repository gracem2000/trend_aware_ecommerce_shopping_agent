"""LLM 抽象层。

一处接口、两套实现：
- MockLLMClient：无 key 时的本地演示（结构化场景 + 模板文案，不联网）。
- GLMClient（core/llm_glm.py）：智谱 GLM 真实调用（吸收自 JD 项目）。

通过环境变量 LLM_PROVIDER 切换：未设置 / "mock" → Mock；"glm"（且配 ZHIPU_API_KEY）→ GLM。
接真模型时只改 get_llm() 的分支，上层 SenseAgent/CopyAgent 不用动 —— 这就是留给你的「可替换接口」。
"""
import os
import random
from typing import Any, Dict, List, Optional

from core.config import DEFAULT_MODEL, LLM_PROVIDER, MAX_TOKENS, TEMPERATURE, ZHIPU_API_KEY


class LLMClient:
    """LLM 抽象接口。同时服务「场景挖掘」（结构化）和「文案生成」（纯文本）。"""

    def complete(self, prompt: str) -> str:
        """通用文本补全（CopyAgent 生成推荐理由用）。"""
        raise NotImplementedError

    def generate_scene(self, hot_topic: str) -> Dict[str, Any]:
        """把一条热点/主题 → 结构化购物场景 dict（JD 场景 schema）。"""
        raise NotImplementedError

    def generate_multiple_scenes(self, topic: str, count: int) -> List[Dict[str, Any]]:
        """一个主题 → 多个不同角度的场景（时节感知用）。"""
        raise NotImplementedError

    def health_check(self) -> bool:
        """客户端是否可用。"""
        return False


# ============ 文案模板（与原 demo 一致） ============
_REASON_TEMPLATES = [
    "针对【{scene}】，这款【{product}】{highlight}，是【{user}】的优质选择",
    "【{user}】都在买的【{product}】，完美匹配【{scene}】，{highlight}",
    "热门【{scene}】下，【{product}】凭借{highlight}登顶推荐榜",
]
_HIGHLIGHTS = [
    "拥有超高性价比", "累计销量破万", "用户好评率超 98%",
    "本季新品，口碑爆款", "材质升级，体验翻倍",
]


def _parse_field(prompt: str, label: str) -> str:
    for line in prompt.splitlines():
        line = line.strip()
        if line.startswith(label):
            return line[len(label):].strip()
    return ""


# ============ Mock 场景素材 ============
_SCENE_TYPES = ["赛事/热点", "热点", "生活", "季节", "节日"]
_USER_INTENTS = [
    "抓住热点红利，提前备货相关用品",
    "应对突发需求，快速满足即买即用",
    "提升生活品质，顺应趋势升级装备",
    "场景化一站式购齐，省心省力",
]
_POPULATIONS = ["都市白领", "年轻家庭", "户外爱好者", "学生党", "亲子家庭", "数码发烧友"]
_KEYWORD_POOL = [
    "便携", "高性价比", "新品", "热销", "防晒", "速干", "降噪", "智能",
    "露营", "健身", "夏季", "居家", "户外", "便携", "升级款", "网红同款",
]


class MockLLMClient(LLMClient):
    """本地 mock：不联网、无 key。返回结构化场景 + 模板文案。"""

    def complete(self, prompt: str) -> str:
        if "推荐理由" in prompt:
            scene = _parse_field(prompt, "场景：") or "当前场景"
            product = _parse_field(prompt, "商品：") or "该商品"
            user = _parse_field(prompt, "人群：") or "用户"
            highlight = _parse_field(prompt, "亮点：") or random.choice(_HIGHLIGHTS)
            return random.choice(_REASON_TEMPLATES).format(
                scene=scene, product=product[:10], user=user, highlight=highlight)
        return "（mock）已处理"

    def generate_scene(self, hot_topic: str) -> Dict[str, Any]:
        kw = random.sample(_KEYWORD_POOL, 6)
        return {
            "scene_name": f"{hot_topic[:6]}场景",
            "scene_type": random.choice(_SCENE_TYPES),
            "trigger_event": hot_topic,
            "temporal_scope": "本周至下月",
            "geo_scope": "全国",
            "user_intent": random.choice(_USER_INTENTS),
            "potential_keywords": kw,
            "target_population": random.choice(_POPULATIONS),
        }

    def generate_multiple_scenes(self, topic: str, count: int) -> List[Dict[str, Any]]:
        return [self.generate_scene(f"{topic}-{i}") for i in range(count)]

    def health_check(self) -> bool:
        return True


_LLM_SINGLETON: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """返回 LLM 客户端单例（按 LLM_PROVIDER 切换；glm 无 key 时自动降级 mock）。"""
    global _LLM_SINGLETON
    if _LLM_SINGLETON is not None:
        return _LLM_SINGLETON

    provider = LLM_PROVIDER
    if provider == "glm":
        if not ZHIPU_API_KEY:
            print("[llm] LLM_PROVIDER=glm 但未设置 ZHIPU_API_KEY，降级为 mock")
            _LLM_SINGLETON = MockLLMClient()
        else:
            try:
                from core.llm_glm import GLMClient
                _LLM_SINGLETON = GLMClient()
            except Exception as e:  # noqa: BLE001
                print(f"[llm] GLMClient 初始化失败 ({e})，降级为 mock")
                _LLM_SINGLETON = MockLLMClient()
    else:
        _LLM_SINGLETON = MockLLMClient()
    return _LLM_SINGLETON


def is_mock() -> bool:
    """当前是否运行在 mock 模式（用于 UI/日志提示）。"""
    return isinstance(get_llm(), MockLLMClient)
