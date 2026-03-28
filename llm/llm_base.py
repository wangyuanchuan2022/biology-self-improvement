"""
LLM客户端基类
定义所有LLM客户端的通用接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM配置"""
    model: str
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    timeout: int = 30
    additional_params: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """LLM响应"""
    text: str
    raw_response: Any
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """LLM错误"""
    pass


class LLMClient(ABC):
    """LLM客户端基类"""

    def __init__(self, config: LLMConfig):
        """
        初始化LLM客户端

        Args:
            config: LLM配置
        """
        self.config = config
        self.history = []

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 额外参数

        Returns:
            LLM响应

        Raises:
            LLMError: 生成失败时抛出
        """
        pass

    def generate_batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> List[LLMResponse]:
        """
        批量生成文本

        Args:
            prompts: 提示词列表
            system_prompt: 系统提示词
            **kwargs: 额外参数

        Returns:
            LLM响应列表
        """
        responses = []
        for prompt in prompts:
            try:
                response = self.generate(prompt, system_prompt, **kwargs)
                responses.append(response)
            except LLMError as e:
                # 记录错误但继续处理其他提示词
                self.history.append({
                    "prompt": prompt,
                    "error": str(e)
                })
                responses.append(LLMResponse(
                    text=f"Error: {str(e)}",
                    raw_response=None
                ))

        return responses

    def record_history(
        self,
        prompt: str,
        response: LLMResponse,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录历史

        Args:
            prompt: 提示词
            response: 响应
            metadata: 元数据
        """
        self.history.append({
            "prompt": prompt,
            "response": response,
            "metadata": metadata or {}
        })

    def get_history_summary(self) -> Dict[str, Any]:
        """
        获取历史摘要

        Returns:
            历史摘要
        """
        total_calls = len(self.history)
        successful_calls = sum(1 for item in self.history if item.get("response"))

        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": total_calls - successful_calls,
            "config": self.config
        }

    def clear_history(self):
        """清空历史"""
        self.history = []

    def __str__(self) -> str:
        return f"LLMClient(model={self.config.model}, calls={len(self.history)})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(config={self.config})"