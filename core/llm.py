"""LLM 抽象层。

当前只提供 MockLLMClient（返回与原 demo 一致的模板化文案，无需任何 API key）。
后续接真模型（DeepSeek / GLM / OpenAI 等）只需新增一个子类、覆盖 complete()，
并在 get_llm() 里按环境变量切换，其余代码不用改 —— 这就是留给你的「可替换接口」。
"""
import os
import random
from typing import Dict, Optional


class LLMClient:
    """LLM 抽象接口。输入 prompt 字符串，输出文本。"""

    def complete(self, prompt: str) -> str:  # noqa: D401
        raise NotImplementedError


# 推荐理由模板与亮点词（与原 main.py 保持一致）
_REASON_TEMPLATES = [
    "针对【{scene}】，这款【{product}】{highlight}，是【{user}】的优质选择",
    "【{user}】都在买的【{product}】，完美匹配【{scene}】，{highlight}",
    "热门【{scene}】下，【{product}】凭借{highlight}登顶推荐榜",
]
_HIGHLIGHTS = [
    "拥有超高性价比",
    "累计销量破万",
    "用户好评率超 98%",
    "本季新品，口碑爆款",
    "材质升级，体验翻倍",
]


def _parse_field(prompt: str, label: str) -> str:
    """从 prompt 里解析 'label：value' 形式的字段。"""
    for line in prompt.splitlines():
        line = line.strip()
        if line.startswith(label):
            return line[len(label):].strip()
    return ""


class MockLLMClient(LLMClient):
    """本地 mock：识别 prompt 中的字段，套模板返回推荐理由。不联网、无 key。"""

    def complete(self, prompt: str) -> str:
        # 推荐理由生成任务
        if "推荐理由" in prompt:
            scene = _parse_field(prompt, "场景：") or "当前场景"
            product = _parse_field(prompt, "商品：") or "该商品"
            user = _parse_field(prompt, "人群：") or "用户"
            highlight = _parse_field(prompt, "亮点：") or random.choice(_HIGHLIGHTS)
            tmpl = random.choice(_REASON_TEMPLATES)
            return tmpl.format(scene=scene, product=product[:10], user=user, highlight=highlight)
        # 默认：返回提示里最后一个问句的占位回答
        return "（mock）已处理"


_LLM_SINGLETON: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    """返回 LLM 客户端单例。

    通过环境变量 LLM_PROVIDER 切换：
      - 未设置 / "mock"  -> MockLLMClient（默认，演示用）
      - 后续可扩展 "deepseek" / "openai" / "glm" 等
    """
    global _LLM_SINGLETON
    if _LLM_SINGLETON is not None:
        return _LLM_SINGLETON

    provider = os.environ.get("LLM_PROVIDER", "mock").lower()
    if provider == "mock":
        _LLM_SINGLETON = MockLLMClient()
    else:
        # 预留：接真模型时在这里加 elif，例如：
        #   elif provider == "deepseek":
        #       from core.llm_deepseek import DeepSeekLLMClient
        #       _LLM_SINGLETON = DeepSeekLLMClient()
        raise ValueError(
            f"未知 LLM_PROVIDER={provider}；当前仅支持 'mock'。"
            "接真模型时在 core/llm.py:get_llm() 增加分支。"
        )
    return _LLM_SINGLETON
