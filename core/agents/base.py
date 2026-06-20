"""Agent 基类：封装状态/日志/sleep/LLM 调用。"""
import time
from typing import Optional

from core.llm import LLMClient, get_llm
from core.repository import set_agent_status, write_log


class BaseAgent:
    """所有 Agent 的基类。子类实现 run()，返回处理条数。"""
    key: str = ""
    name: str = ""

    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or get_llm()

    # ---- 工具方法 ----
    def status(self, status: str, task: Optional[str] = None) -> None:
        set_agent_status(self.key, status, task)

    def log(self, level: str, message: str) -> None:
        write_log(self.key, level, message)

    def sleep(self, ms: int) -> None:
        time.sleep(ms / 1000)

    # ---- 子类实现 ----
    def run(self) -> int:
        raise NotImplementedError
