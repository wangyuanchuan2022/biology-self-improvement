"""
智能体错误定义
"""


class AgentError(Exception):
    """智能体基础错误"""
    pass


class LLMError(AgentError):
    """LLM相关错误"""
    pass


class ValidationError(AgentError):
    """数据验证错误"""
    pass


class ConfigurationError(AgentError):
    """配置错误"""
    pass


class ProcessingError(AgentError):
    """处理错误"""
    pass


class TimeoutError(AgentError):
    """超时错误"""
    pass


class RetryExhaustedError(AgentError):
    """重试耗尽错误"""
    pass