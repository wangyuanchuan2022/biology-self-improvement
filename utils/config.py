"""
配置管理模块
处理API密钥、路径和其他配置
"""

import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
import dotenv


class Config:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径（可选）
        """
        # 加载环境变量
        dotenv.load_dotenv()

        # 配置存储
        self.config: Dict[str, Any] = {}

        # 默认配置
        self._load_defaults()

        # 加载配置文件
        if config_file:
            self.load_config(config_file)
        else:
            # 尝试加载默认配置文件
            default_configs = [
                "config.json",
                ".config.json",
                "config/config.json"
            ]
            for config_path in default_configs:
                if os.path.exists(config_path):
                    self.load_config(config_path)
                    break

        # 加载环境变量覆盖
        self._load_from_env()

    def _load_defaults(self):
        """加载默认配置"""
        self.config = {
            # LLM配置
            "deepseek": {
                "api_key": "",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-chat",
                "timeout": 30,
                "max_tokens": 2000
            },
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "qwen2.5-vl:8b",
                "timeout": 60
            },
            # 文档处理配置
            "document_processor": {
                "enable_image_descriptions": True,
                "image_quality": 85,
                "max_image_size": (1024, 1024),
                "output_dir": "processed_output"
            },
            # 智能体配置
            "agents": {
                "max_iterations": 3,
                "temperature": 0.7,
                "enable_logging": True,
                "log_dir": "logs"
            },
            # 系统配置
            "system": {
                "data_dir": "data",
                "cache_dir": "cache",
                "log_level": "INFO",
                "debug": False
            }
        }

    def _load_from_env(self):
        """从环境变量加载配置"""
        # Deepseek配置
        if api_key := os.getenv("DEEPSEEK_API_KEY"):
            self.config["deepseek"]["api_key"] = api_key

        if base_url := os.getenv("DEEPSEEK_BASE_URL"):
            self.config["deepseek"]["base_url"] = base_url

        if model := os.getenv("DEEPSEEK_MODEL"):
            self.config["deepseek"]["model"] = model

        # Ollama配置
        if base_url := os.getenv("OLLAMA_BASE_URL"):
            self.config["ollama"]["base_url"] = base_url

        if model := os.getenv("OLLAMA_MODEL"):
            self.config["ollama"]["model"] = model

        # 系统配置
        if log_level := os.getenv("LOG_LEVEL"):
            self.config["system"]["log_level"] = log_level

        if debug := os.getenv("DEBUG"):
            self.config["system"]["debug"] = debug.lower() in ("true", "1", "yes")

    def load_config(self, config_file: str):
        """
        从JSON文件加载配置

        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # 递归合并配置
            self._merge_configs(self.config, loaded_config)
            print(f"配置已从 {config_file} 加载")

        except FileNotFoundError:
            print(f"配置文件 {config_file} 不存在，使用默认配置")
        except json.JSONDecodeError as e:
            print(f"配置文件 {config_file} JSON解析错误: {e}")
        except Exception as e:
            print(f"加载配置文件 {config_file} 时出错: {e}")

    def _merge_configs(self, base: Dict, update: Dict):
        """
        递归合并配置字典

        Args:
            base: 基础配置字典
            update: 更新配置字典
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value

    def save_config(self, config_file: str):
        """
        保存配置到JSON文件

        Args:
            config_file: 配置文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(config_file)), exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            print(f"配置已保存到 {config_file}")

        except Exception as e:
            print(f"保存配置文件 {config_file} 时出错: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key_path: 配置键路径，用点分隔，如 "deepseek.api_key"
            default: 默认值

        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any):
        """
        设置配置值

        Args:
            key_path: 配置键路径，用点分隔
            value: 配置值
        """
        keys = key_path.split('.')
        config = self.config

        # 遍历到最后一个键的父级
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # 设置值
        config[keys[-1]] = value

    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.get("document_processor.output_dir", "processed_output"),
            self.get("agents.log_dir", "logs"),
            self.get("system.data_dir", "data"),
            self.get("system.cache_dir", "cache"),
        ]

        for directory in directories:
            if directory:  # 确保目录不为空
                os.makedirs(directory, exist_ok=True)
                print(f"目录已创建/确认: {directory}")

    def validate(self) -> bool:
        """
        验证配置完整性

        Returns:
            配置是否有效
        """
        errors = []

        # 检查必要的API密钥
        if not self.get("deepseek.api_key"):
            errors.append("Deepseek API密钥未设置")

        # 检查必要的目录
        required_dirs = [
            self.get("document_processor.output_dir"),
            self.get("system.data_dir")
        ]

        for dir_path in required_dirs:
            if dir_path:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except Exception as e:
                    errors.append(f"无法创建目录 {dir_path}: {e}")

        if errors:
            print("配置验证错误:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def print_summary(self):
        """打印配置摘要"""
        print("\n" + "=" * 60)
        print("配置摘要")
        print("=" * 60)

        # LLM配置
        print("\nLLM配置:")
        deepseek_config = self.get("deepseek")
        if deepseek_config and deepseek_config.get("api_key"):
            print(f"  Deepseek: {deepseek_config.get('model')} (API密钥已设置)")
        else:
            print("  Deepseek: API密钥未设置")

        ollama_config = self.get("ollama")
        if ollama_config:
            print(f"  Ollama: {ollama_config.get('model')} at {ollama_config.get('base_url')}")

        # 文档处理配置
        print("\n文档处理配置:")
        doc_config = self.get("document_processor")
        if doc_config:
            print(f"  图片描述: {'启用' if doc_config.get('enable_image_descriptions') else '禁用'}")
            print(f"  输出目录: {doc_config.get('output_dir')}")

        # 智能体配置
        print("\n智能体配置:")
        agent_config = self.get("agents")
        if agent_config:
            print(f"  最大迭代次数: {agent_config.get('max_iterations')}")
            print(f"  日志目录: {agent_config.get('log_dir')}")

        # 系统配置
        print("\n系统配置:")
        sys_config = self.get("system")
        if sys_config:
            print(f"  数据目录: {sys_config.get('data_dir')}")
            print(f"  日志级别: {sys_config.get('log_level')}")
            print(f"  调试模式: {'是' if sys_config.get('debug') else '否'}")

        print("=" * 60)


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(config_file: Optional[str] = None) -> Config:
    """
    获取全局配置实例

    Args:
        config_file: 配置文件路径

    Returns:
        配置实例
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = Config(config_file)

    return _config_instance


def init_config(config_file: Optional[str] = None) -> Config:
    """
    初始化配置并验证

    Args:
        config_file: 配置文件路径

    Returns:
        配置实例

    Raises:
        ValueError: 如果配置验证失败
    """
    config = get_config(config_file)

    # 确保目录存在
    config.ensure_directories()

    # 验证配置
    if not config.validate():
        raise ValueError("配置验证失败，请检查配置")

    config.print_summary()

    return config


# 使用示例
if __name__ == "__main__":
    # 测试配置
    try:
        config = init_config()
        print("\n配置初始化成功!")
    except ValueError as e:
        print(f"配置初始化失败: {e}")
        print("请设置必要的环境变量或配置文件")