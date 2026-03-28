"""
智能体基类
定义所有智能体的通用接口和行为
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass


@dataclass
class AgentContext:
    """智能体执行上下文"""
    question_id: str
    iteration: int
    previous_output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentInput:
    """智能体输入数据"""
    question_text: str
    scoring_standard: str
    context: Optional[AgentContext] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class AgentOutput:
    """智能体输出数据"""
    answer: str
    score: Optional[float] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    improvements: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAgent(ABC):
    """智能体基类"""

    def __init__(
        self,
        name: str,
        llm_client: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化智能体

        Args:
            name: 智能体名称
            llm_client: LLM客户端实例
            config: 配置字典
        """
        self.name = name
        self.llm_client = llm_client
        self.config = config or {}
        self.history = []

    @abstractmethod
    def process(self, input_data: AgentInput) -> AgentOutput:
        """
        处理输入数据，生成输出

        Args:
            input_data: 输入数据

        Returns:
            处理结果

        Raises:
            AgentError: 处理失败时抛出
        """
        pass

    def record_history(
        self,
        iteration: int,
        input_data: AgentInput,
        output_data: AgentOutput
    ):
        """
        记录处理历史

        Args:
            iteration: 迭代次数
            input_data: 输入数据
            output_data: 输出数据
        """
        self.history.append({
            "iteration": iteration,
            "input": input_data,
            "output": output_data
        })

    def get_summary(self) -> Dict[str, Any]:
        """
        获取智能体摘要信息

        Returns:
            摘要信息字典
        """
        return {
            "name": self.name,
            "total_iterations": len(self.history),
            "config": self.config,
            "last_processing": self.history[-1] if self.history else None
        }

    def reset(self):
        """重置智能体状态"""
        self.history = []

    def __str__(self) -> str:
        return f"Agent(name='{self.name}', iterations={len(self.history)})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"