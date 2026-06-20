"""GLM（智谱）真实 LLM 客户端 —— 吸收自 JD 项目的 src/llm_client.py。

实现 core.llm.LLMClient 接口，用 zai-sdk 调用智谱 GLM。
不传 base_url：zai-sdk 自带正确的原生端点（JD 里的 /api/anthropic 是给 Anthropic SDK 用的，给原生 SDK 会 404）。
"""
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from zai import ZhipuAiClient

from core.config import DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE, ZHIPU_API_KEY


class GLMClient:
    """智谱 GLM 客户端（实现 LLMClient 接口）。"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or ZHIPU_API_KEY
        self.model = model or DEFAULT_MODEL
        self.temperature = TEMPERATURE
        self.max_tokens = MAX_TOKENS
        self.client = None
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY 未设置")
        try:
            self.client = ZhipuAiClient(api_key=self.api_key)
            print(f"[llm] GLM 客户端就绪 (model={self.model})")
        except Exception as e:  # noqa: BLE001
            print(f"[llm] GLM 客户端初始化失败: {e}")
            self.client = None

    # ---------- 接口实现 ----------
    def complete(self, prompt: str) -> str:
        if not self.client:
            return ""
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:  # noqa: BLE001
            print(f"[llm] complete 失败: {e}")
            return ""

    def generate_scene(self, hot_topic: str) -> Dict[str, Any]:
        if not self.client:
            return self._empty_scene(hot_topic)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": self._build_scene_prompt(hot_topic)}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = resp.choices[0].message.content or ""
            data = self._parse_json_object(content)
            if data:
                return self._fix_temporal_scope_year(data)
            return self._fallback_scene(hot_topic, content)
        except Exception as e:  # noqa: BLE001
            print(f"[llm] generate_scene 失败: {e}")
            return self._empty_scene(hot_topic)

    def generate_multiple_scenes(self, topic: str, count: int) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": self._build_multi_prompt(topic, count)}],
                max_tokens=self.max_tokens * 3,
                temperature=0.8,
            )
            content = resp.choices[0].message.content or ""
            data = self._parse_json_array(content)
            return [self._fix_temporal_scope_year(s) for s in data] if data else []
        except Exception as e:  # noqa: BLE001
            print(f"[llm] generate_multiple_scenes 失败: {e}")
            return []

    def health_check(self) -> bool:
        return self.client is not None

    # ---------- Prompt / 解析（移植自 JD） ----------
    def _build_scene_prompt(self, hot_topic: str) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        year = datetime.now().year
        return f"""你是一个电商场景挖掘专家。请将以下热点话题转化为购物场景。

当前日期: {today}
热点话题: {hot_topic}

请分析这个热点话题可能引发的购物需求，并以 JSON 格式输出，包含以下字段:
- scene_name: 场景名称（简洁明了，4-8个字）
- scene_type: 场景类型（赛事/热点/节日/季节/生活等）
- trigger_event: 触发事件（简短描述）
- temporal_scope: 时间范围（必须是{year}年的日期，格式如"{today} 至 {year}-07-15"，持续性场景可写"全年"）
- geo_scope: 地理范围（如"全国"）
- user_intent: 用户意图描述（1-2句话）
- potential_keywords: 潜在商品关键词列表（5-8个）
- target_population: 目标人群

只返回JSON内容，不要其他说明文字。"""

    def _build_multi_prompt(self, topic: str, count: int) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        year = datetime.now().year
        return f"""你是一个电商场景挖掘专家。请基于"{topic}"生成 {count} 个不同角度的购物场景。

当前日期: {today}
主题: {topic}

请从不同角度（礼品赠送/家庭聚会出游/DIY自制/服饰穿搭/美食餐饮/祈福文化等）分析，以 JSON 数组输出 {count} 个场景，每个包含:
scene_name, scene_type, trigger_event, temporal_scope（必须是{year}年日期）, geo_scope, user_intent, potential_keywords（5-8个）, target_population

每个场景要有明显区分度。只返回JSON数组，不要其他说明文字。"""

    def _fix_temporal_scope_year(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """把 LLM 误写的年份修正为当前年。"""
        year = datetime.now().year
        scope = data.get("temporal_scope", "") or ""
        if not scope or "全年" in scope or "长期" in scope:
            return data
        fixed = re.sub(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", f"{year}-\\2-\\3", scope)
        fixed = re.sub(r"(\d{4})年(\d{1,2})月", f"{year}年\\2月", fixed)
        if fixed != scope:
            data["temporal_scope"] = fixed
        return data

    def _parse_json_object(self, content: str) -> Dict[str, Any]:
        try:
            content = self._strip_codefence(content)
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:  # noqa: BLE001
                    return {}
            return {}

    def _parse_json_array(self, content: str) -> List[Dict[str, Any]]:
        try:
            content = self._strip_codefence(content)
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            m = re.search(r"\[.*\]", content, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except Exception:  # noqa: BLE001
                    return []
            return []

    @staticmethod
    def _strip_codefence(content: str) -> str:
        content = (content or "").strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    @staticmethod
    def _empty_scene(hot_topic: str) -> Dict[str, Any]:
        return {
            "scene_name": f"场景: {hot_topic[:20]}",
            "scene_type": "未知", "trigger_event": hot_topic,
            "temporal_scope": "未知", "geo_scope": "未知",
            "user_intent": "暂无描述", "potential_keywords": [], "target_population": "未知",
        }

    @staticmethod
    def _fallback_scene(hot_topic: str, raw: str) -> Dict[str, Any]:
        return {
            "scene_name": f"场景: {hot_topic[:20]}",
            "scene_type": "需人工审核", "trigger_event": hot_topic,
            "temporal_scope": "待确定", "geo_scope": "待确定",
            "user_intent": (raw or "")[:100] or "暂无描述",
            "potential_keywords": [], "target_population": "待确定",
        }
