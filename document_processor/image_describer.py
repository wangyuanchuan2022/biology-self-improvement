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

    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        """
        初始化图片描述生成器

        Args:
            ollama_base_url: Ollama API基础URL
        """
        self.ollama_base_url = ollama_base_url
        self.model_name = "qwen2.5-vl:8b"  # 使用qwen2.5-vl:8b模型

        # 图片类型到提示词的映射
        self.prompt_templates = {
            ImageType.EXPERIMENT: self._create_experiment_prompt(),
            ImageType.CHART: self._create_chart_prompt(),
            ImageType.DIAGRAM: self._create_diagram_prompt(),
            ImageType.MICROSCOPE: self._create_microscope_prompt(),
            ImageType.STRUCTURE: self._create_structure_prompt(),
            ImageType.TABLE: self._create_table_prompt(),
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
        return """请详细描述这张生物学实验图。请包括以下内容：
1. 实验装置和材料
2. 实验步骤的关键点
3. 图中显示的结果或现象
4. 可能的实验变量（自变量、因变量、控制变量）
5. 图的标题和坐标轴标签（如果有）

请用清晰、准确的语言描述，特别关注生物学相关的细节。如果图中有数据，请描述数据趋势和关键数值。"""

    def _create_chart_prompt(self) -> str:
        """创建图表提示词"""
        return """请详细描述这张生物学图表。请包括以下内容：
1. 图表类型（柱状图、折线图、散点图等）
2. 坐标轴标签和单位
3. 数据组别和分组情况
4. 数据趋势和关键数值
5. 显著性标记（如*、#等）
6. 图例说明

请准确描述数据变化趋势，比较不同组别之间的差异，并指出可能的生物学意义。"""

    def _create_diagram_prompt(self) -> str:
        """创建示意图/流程图提示词"""
        return """请详细描述这张生物学示意图或流程图。请包括以下内容：
1. 图的整体结构和组成部分
2. 各个部分之间的连接和关系
3. 流程方向（如果有）
4. 关键生物学过程或机制
5. 图中使用的符号和标记的含义

请用逻辑清晰的语言描述整个过程或机制，强调生物学原理。"""

    def _create_microscope_prompt(self) -> str:
        """创建显微图提示词"""
        return """请详细描述这张生物学显微图。请包括以下内容：
1. 观察对象（细胞、组织、器官等）
2. 放大倍数（如果标注）
3. 染色方法（如果可识别）
4. 关键结构特征
5. 异常或特殊现象
6. 比例尺信息

请使用准确的生物学术语描述结构特征，注意细胞器、细胞类型、组织层次等细节。"""

    def _create_structure_prompt(self) -> str:
        """创建结构图提示词"""
        return """请详细描述这张生物学结构图。请包括以下内容：
1. 结构名称和类型
2. 各个组成部分的名称和功能
3. 结构层次和空间关系
4. 关键特征和特殊结构
5. 标尺或比例信息

请使用准确的解剖学或分子生物学术语，注意细节和准确性。"""

    def _create_table_prompt(self) -> str:
        """创建表格提示词"""
        return """请详细描述这张生物学表格。请包括以下内容：
1. 表格标题和行列标题
2. 数据内容和单位
3. 数据趋势和模式
4. 关键数值和比较结果
5. 统计信息（如p值、标准差等）

请准确提取和描述表格数据，指出重要的生物学发现或趋势。"""

    def _create_general_prompt(self) -> str:
        """创建通用提示词"""
        return """请详细描述这张生物学相关的图片。请包括以下内容：
1. 图片的主要内容
2. 关键生物学元素
3. 图中显示的信息或数据
4. 可能的生物学意义

请使用准确、清晰的生物学语言进行描述，注意细节和准确性。"""


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