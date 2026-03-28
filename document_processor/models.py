"""
文档处理数据模型定义
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ImageType(Enum):
    """图片类型枚举"""
    EXPERIMENT = "experiment"  # 实验图
    CHART = "chart"            # 图表
    DIAGRAM = "diagram"        # 示意图/流程图
    MICROSCOPE = "microscope"  # 显微图
    STRUCTURE = "structure"    # 结构图
    TABLE = "table"            # 表格
    PDF_PAGE = "pdf_page"      # PDF页面
    OTHER = "other"            # 其他


@dataclass
class DocumentImage:
    """文档图片信息"""
    image_id: str                     # 图片唯一标识
    image_data: bytes                 # 图片二进制数据
    image_format: str                 # 图片格式 (jpg, png等)
    description: Optional[str] = None # 图片描述（由模型生成）
    image_type: ImageType = ImageType.OTHER  # 图片类型
    position_info: Optional[Dict[str, Any]] = None  # 位置信息


@dataclass
class TextBlock:
    """文本块信息"""
    text: str
    style: Optional[str] = None      # 样式信息（标题、正文等）
    is_after_image: bool = False     # 是否在图片后面


@dataclass
class DocumentContent:
    """文档内容完整表示"""
    # 原始内容
    images: List[DocumentImage]      # 图片列表
    text_blocks: List[TextBlock]     # 文本块列表

    # 处理后的内容
    formatted_text: Optional[str] = None  # 格式化后的完整文本
    image_descriptions: Optional[Dict[str, str]] = None  # 图片ID到描述的映射

    # 元数据
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AgentInput:
    """智能体输入格式"""
    question_text: str                # 试题文本（包含图片描述）
    scoring_standard: str             # 评分标准文本
    metadata: Optional[Dict[str, Any]] = None  # 附加元数据