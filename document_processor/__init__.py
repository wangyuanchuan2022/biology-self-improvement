"""
文档处理器模块
"""

from .models import (
    DocumentImage,
    TextBlock,
    DocumentContent,
    AgentInput,
    ImageType
)

from .word_extractor import WordExtractor
from .pdf_extractor import PDFExtractor
from .image_describer import ImageDescriber
from .text_formatter import TextFormatter, BiologyQuestionFormatter
from .main import DocumentProcessor

__all__ = [
    # 数据模型
    "DocumentImage",
    "TextBlock",
    "DocumentContent",
    "AgentInput",
    "ImageType",

    # 处理器类
    "WordExtractor",
    "PDFExtractor",
    "ImageDescriber",
    "TextFormatter",
    "BiologyQuestionFormatter",
    "DocumentProcessor",

    # 版本信息
    "__version__"
]

__version__ = "0.1.0"