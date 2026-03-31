"""
图片描述生成器
使用Ollama (qwen3-vl:8b) 生成图片描述
"""

import base64
import json
import time
from typing import List, Dict, Optional
import requests
from PIL import Image
import io

from .models import DocumentImage, ImageType


class ImageDescriber:
    """图片描述生成器"""

    def __init__(self, ollama_base_url: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化图片描述生成器

        Args:
            ollama_base_url: Ollama API基础URL（如果为None，则尝试从配置获取）
            model_name: 模型名称（如果为None，则尝试从配置获取）
        """
        if ollama_base_url is None:
            # 尝试从配置获取
            try:
                from utils.config import get_config
                config = get_config()
                self.ollama_base_url = config.get("ollama.base_url")
            except ImportError:
                self.ollama_base_url = "http://localhost:11434"
        else:
            self.ollama_base_url = ollama_base_url

        if model_name is None:
            # 尝试从配置获取
            try:
                from utils.config import get_config
                config = get_config()
                self.model_name = config.get("ollama.model")
            except ImportError:
                self.model_name = "qwen3-vl:8b"
        else:
            self.model_name = model_name

        # 图片类型到提示词的映射
        self.prompt_templates = {
            ImageType.EXPERIMENT: self._create_experiment_prompt(),
            ImageType.CHART: self._create_chart_prompt(),
            ImageType.DIAGRAM: self._create_diagram_prompt(),
            ImageType.MICROSCOPE: self._create_microscope_prompt(),
            ImageType.STRUCTURE: self._create_structure_prompt(),
            ImageType.TABLE: self._create_table_prompt(),
            ImageType.PDF_PAGE: self._create_pdf_page_prompt(),
            ImageType.OTHER: self._create_general_prompt()
        }

    def describe_images(self, images: List[DocumentImage]) -> Dict[str, str]:
        """
        为图片列表生成描述

        Args:
            images: 图片列表

        Returns:
            图片ID到描述的映射
        """
        descriptions = {}

        for image in images:
            try:
                description = self._describe_single_image(image)
                descriptions[image.image_id] = description
                image.description = description  # 更新图片对象
                print(f"图片 {image.image_id} 描述生成完成")
            except Exception as e:
                print(f"图片 {image.image_id} 描述生成失败: {e}")
                descriptions[image.image_id] = f"描述生成失败: {str(e)}"

        return descriptions

    def _describe_single_image(self, image: DocumentImage) -> str:
        """
        为单张图片生成描述

        Args:
            image: 图片对象

        Returns:
            图片描述文本
        """
        # 准备图片数据
        image_base64 = self._image_to_base64(image)

        # 获取对应类型的提示词
        prompt = self.prompt_templates.get(image.image_type, self.prompt_templates[ImageType.OTHER])

        # 调用Ollama API
        response = self._call_ollama_api(image_base64, prompt)

        return response.strip()

    def _image_to_base64(self, image: DocumentImage) -> str:
        """
        将图片转换为base64编码

        Args:
            image: 图片对象

        Returns:
            base64编码的图片字符串
        """
        try:
            # 使用PIL处理图片（如果需要调整大小或格式）
            img = Image.open(io.BytesIO(image.image_data))

            # 转换为RGB模式（如果必要）
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # 保存到字节流
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # 编码为base64
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            return image_base64

        except Exception as e:
            # 如果处理失败，直接使用原始数据
            print(f"图片处理失败，使用原始数据: {e}")
            return base64.b64encode(image.image_data).decode('utf-8')

    def _call_ollama_api(self, image_base64: str, prompt: str) -> str:
        """
        调用Ollama API生成描述

        Args:
            image_base64: base64编码的图片
            prompt: 提示词

        Returns:
            API响应文本
        """
        # 构建请求数据
        request_data = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {
                "temperature": 0.3,  # 较低温度以获得更准确的描述
                "top_p": 0.9,
                "top_k": 40
            }
        }

        # 发送请求
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json=request_data,
                timeout=60  # 60秒超时
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                raise Exception(f"Ollama API错误: {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            raise Exception("Ollama API请求超时")
        except requests.exceptions.ConnectionError:
            raise Exception(f"无法连接到Ollama服务: {self.ollama_base_url}")
        except Exception as e:
            raise Exception(f"Ollama API调用失败: {str(e)}")

    def _create_experiment_prompt(self) -> str:
        """创建实验图提示词"""
        return """请简洁描述这张生物学实验图的关键信息：
- 实验装置和材料
- 主要实验步骤
- 结果或现象
- 实验变量（自变量、因变量、控制变量）
- 标题和坐标轴标签（如果有）

请用准确、简洁的生物学语言描述。如果有数据，指出关键数值和趋势。"""

    def _create_chart_prompt(self) -> str:
        """创建图表提示词"""
        return """请简洁描述这张生物学图表的关键信息：
- 图表类型（柱状图、折线图、散点图等）
- 坐标轴标签和单位
- 数据组别和分组
- 数据趋势和关键数值
- 显著性标记（如*、#等）
- 图例说明

请准确、简洁地描述数据趋势和组间差异，指出生物学意义。"""

    def _create_diagram_prompt(self) -> str:
        """创建示意图/流程图提示词"""
        return """请简洁描述这张生物学示意图或流程图的关键信息：
- 整体结构和组成部分
- 各部分之间的连接和关系
- 流程方向（如果有）
- 关键生物学过程或机制
- 符号和标记的含义

请用逻辑清晰、简洁的语言描述，强调生物学原理。"""

    def _create_microscope_prompt(self) -> str:
        """创建显微图提示词"""
        return """请简洁描述这张生物学显微图的关键信息：
- 观察对象（细胞、组织、器官等）
- 放大倍数（如果标注）
- 染色方法（如果可识别）
- 关键结构特征
- 异常或特殊现象
- 比例尺信息

请使用准确、简洁的生物学术语描述结构特征。"""

    def _create_structure_prompt(self) -> str:
        """创建结构图提示词"""
        return """请简洁描述这张生物学结构图的关键信息：
- 结构名称和类型
- 组成部分的名称和功能
- 结构层次和空间关系
- 关键特征和特殊结构
- 标尺或比例信息

请使用准确、简洁的解剖学或分子生物学术语。"""

    def _create_table_prompt(self) -> str:
        """创建表格提示词"""
        return """请简洁描述这张生物学表格的关键信息：
- 表格标题和行列标题
- 数据内容和单位
- 数据趋势和模式
- 关键数值和比较结果
- 统计信息（如p值、标准差等）

请准确、简洁地提取和描述数据，指出生物学发现或趋势。"""

    def _create_pdf_page_prompt(self) -> str:
        """创建PDF页面提示词"""
        return """请描述这张生物学试题PDF页面的关键内容：
- 全部文本内容（题目、选项、说明等）
- 非文本元素（图片、图表等）及其内容
- 填空处（"____"或留空）的位置和上下文
- 页面布局（标题、编号等）
- 特殊符号或标记

对于填空处，请指出：
- 具体位置（如：第1题第2空）
- 前后文
- 可能要求的内容类型（名词、数字、短语等）

请用简洁、结构化的语言描述，确保填空处被准确标注。"""

    def _create_general_prompt(self) -> str:
        """创建通用提示词"""
        return """请简洁描述这张生物学图片的关键信息：
- 主要内容
- 关键生物学元素
- 图中显示的信息或数据
- 可能的生物学意义

请使用准确、简洁的生物学语言描述。"""


# 使用示例
if __name__ == "__main__":
    # 测试代码
    describer = ImageDescriber()

    # 创建测试图片（需要实际图片数据）
    test_images = []
    # 这里可以添加测试代码

    if test_images:
        descriptions = describer.describe_images(test_images)
        for img_id, desc in descriptions.items():
            print(f"\n{img_id}:\n{desc[:200]}...")  # 只显示前200字符
    else:
        print("无测试图片，跳过测试")