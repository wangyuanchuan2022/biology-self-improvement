"""
文本格式化器
将文档内容格式化为智能体输入格式
"""

from typing import List, Dict, Optional
import re

from .models import DocumentContent, AgentInput, TextBlock


class TextFormatter:
    """文本格式化器"""

    def __init__(self):
        # 图片占位符格式
        self.image_placeholder = "[图片{id}: {description}]"
        # 段落分隔符
        self.paragraph_separator = "\n\n"

    def format_for_agents(self, content: DocumentContent) -> AgentInput:
        """
        将文档内容格式化为智能体输入

        Args:
            content: 文档内容对象

        Returns:
            智能体输入对象
        """
        # 确保有图片描述
        if not content.image_descriptions and content.images:
            raise ValueError("文档包含图片但未生成描述")

        # 格式化试题文本
        question_text = self._format_question_text(content)

        # 格式化评分标准（如果有）
        scoring_standard = self._extract_scoring_standard(content)

        # 创建智能体输入
        agent_input = AgentInput(
            question_text=question_text,
            scoring_standard=scoring_standard,
            metadata={
                "source": content.metadata.get("file_name", "unknown"),
                "total_images": len(content.images),
                "image_descriptions_generated": bool(content.image_descriptions)
            }
        )

        return agent_input

    def _format_question_text(self, content: DocumentContent) -> str:
        """
        格式化试题文本

        Args:
            content: 文档内容

        Returns:
            格式化后的试题文本
        """
        formatted_parts = []

        # 处理文本块和图片的交替
        text_index = 0
        image_index = 0

        # 简单策略：先按顺序处理文本块，在适当位置插入图片描述
        for text_block in content.text_blocks:
            formatted_parts.append(text_block.text)

            # 检查是否需要在文本块后插入图片描述
            # 这里使用简单策略：根据文本内容判断
            if self._should_insert_image_after(text_block.text):
                if image_index < len(content.images):
                    image_desc = self._get_image_description(
                        content.images[image_index],
                        content.image_descriptions
                    )
                    formatted_parts.append(image_desc)
                    image_index += 1

        # 处理剩余的图片
        while image_index < len(content.images):
            image_desc = self._get_image_description(
                content.images[image_index],
                content.image_descriptions
            )
            formatted_parts.append(image_desc)
            image_index += 1

        # 合并所有部分
        formatted_text = self.paragraph_separator.join(
            part for part in formatted_parts if part.strip()
        )

        return formatted_text

    def _extract_scoring_standard(self, content: DocumentContent) -> str:
        """
        从文档内容中提取评分标准

        Args:
            content: 文档内容

        Returns:
            评分标准文本
        """
        scoring_parts = []

        # 简单策略：查找包含评分标准关键词的文本块
        scoring_keywords = [
            '评分标准', '评分细则', '评分参考', '参考答案',
            'scoring', 'rubric', 'answer key', 'reference answer'
        ]

        for text_block in content.text_blocks:
            text_lower = text_block.text.lower()

            # 检查是否包含评分标准关键词
            if any(keyword in text_lower for keyword in scoring_keywords):
                scoring_parts.append(text_block.text)

            # 检查样式是否为评分标准相关
            if text_block.style and any(
                style_keyword in text_block.style.lower()
                for style_keyword in ['answer', 'scoring', 'rubric']
            ):
                scoring_parts.append(text_block.text)

        if scoring_parts:
            return self.paragraph_separator.join(scoring_parts)
        else:
            # 如果没有找到评分标准，返回一个占位符
            return "【注意：未在文档中找到明确的评分标准部分，请根据试题内容自行判断评分要点】"

    def _get_image_description(
        self,
        image,
        image_descriptions: Optional[Dict[str, str]]
    ) -> str:
        """
        获取图片描述文本

        Args:
            image: 图片对象
            image_descriptions: 图片描述映射

        Returns:
            图片描述文本
        """
        if image_descriptions and image.image_id in image_descriptions:
            description = image_descriptions[image.image_id]
        elif image.description:
            description = image.description
        else:
            description = "未生成描述"

        # 创建图片占位符
        image_type_str = image.image_type.value
        placeholder = f"[{image_type_str}图片 {image.image_id}: {description}]"

        return placeholder

    def _should_insert_image_after(self, text: str) -> bool:
        """
        判断是否需要在文本后插入图片描述

        Args:
            text: 文本内容

        Returns:
            是否插入图片
        """
        # 检查文本是否包含图片引用
        image_references = [
            '如图所示', '见下图', '如图', '图例',
            '如图所示', '参见图', '图片显示',
            'as shown in the figure', 'see figure', 'figure'
        ]

        text_lower = text.lower()
        return any(ref in text_lower for ref in image_references)

    def create_structured_output(self, content: DocumentContent) -> Dict:
        """
        创建结构化输出（用于调试和分析）

        Args:
            content: 文档内容

        Returns:
            结构化输出字典
        """
        structured = {
            "metadata": content.metadata or {},
            "images": [],
            "text_blocks": [],
            "formatted_text": content.formatted_text
        }

        # 图片信息
        for image in content.images:
            structured["images"].append({
                "id": image.image_id,
                "type": image.image_type.value,
                "description": image.description or "未生成",
                "has_description": bool(image.description)
            })

        # 文本块信息
        for i, text_block in enumerate(content.text_blocks):
            structured["text_blocks"].append({
                "index": i,
                "text_preview": text_block.text[:100] + ("..." if len(text_block.text) > 100 else ""),
                "style": text_block.style or "unknown",
                "length": len(text_block.text)
            })

        return structured


# 高级格式化器：针对生物学试题优化
class BiologyQuestionFormatter(TextFormatter):
    """生物学试题专用格式化器"""

    def __init__(self):
        super().__init__()
        # 生物学特定的图片占位符格式
        self.image_placeholder = "【{type}图: {description}】"

    def _extract_scoring_standard(self, content: DocumentContent) -> str:
        """
        生物学试题专用的评分标准提取

        Args:
            content: 文档内容

        Returns:
            评分标准文本
        """
        scoring_parts = []

        # 生物学特定的评分标准关键词
        biology_scoring_keywords = [
            '评分标准', '评分细则', '参考答案', '答案要点',
            '得分点', '赋分', '评分参考',
            # 英文关键词
            'scoring rubric', 'answer key', 'marking scheme'
        ]

        # 查找评分标准部分（通常出现在文档后半部分）
        for i, text_block in enumerate(content.text_blocks):
            text_lower = text_block.text.lower()

            # 检查评分标准标题
            if any(keyword in text_lower for keyword in biology_scoring_keywords):
                # 添加标题
                scoring_parts.append(f"## {text_block.text}")

                # 添加后续内容（直到下一个标题或结束）
                for j in range(i + 1, len(content.text_blocks)):
                    next_block = content.text_blocks[j]
                    # 如果遇到新标题，停止
                    if self._is_new_section(next_block.text):
                        break
                    scoring_parts.append(next_block.text)

        if scoring_parts:
            return self.paragraph_separator.join(scoring_parts)
        else:
            # 尝试提取可能包含答案的文本块
            return self._extract_possible_answers(content)

    def _is_new_section(self, text: str) -> bool:
        """
        判断是否为新的章节标题

        Args:
            text: 文本

        Returns:
            是否为标题
        """
        # 检查是否包含常见标题模式
        patterns = [
            r'^第[一二三四五六七八九十\d]+[题章节]',
            r'^[A-Z][\.、]',
            r'^[\d]+[\.、]',
            r'^【',
            r'^###',
            r'^##',
            r'^[A-Z].*:$'
        ]

        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True

        return False

    def _extract_possible_answers(self, content: DocumentContent) -> str:
        """
        提取可能的答案部分

        Args:
            content: 文档内容

        Returns:
            可能的答案文本
        """
        answer_parts = []

        # 查找可能包含答案的文本块
        answer_indicators = [
            '答案', '答：', '答案：', '参考答案',
            '解答', '解析', '说明',
            'answer', 'solution', 'explanation'
        ]

        for text_block in content.text_blocks:
            text_lower = text_block.text.lower()
            if any(indicator in text_lower for indicator in answer_indicators):
                answer_parts.append(text_block.text)

        if answer_parts:
            return self.paragraph_separator.join([f"【可能的评分参考】"] + answer_parts)
        else:
            return "【提示：请根据生物学知识和试题要求自行制定评分标准】"


# 使用示例
if __name__ == "__main__":
    # 测试代码
    formatter = BiologyQuestionFormatter()

    # 创建测试内容
    test_content = DocumentContent(
        images=[],
        text_blocks=[
            TextBlock(text="1. 请描述细胞有丝分裂的过程。", style="heading"),
            TextBlock(text="如图所示为细胞有丝分裂的示意图。", style="normal"),
            TextBlock(text="评分标准：", style="heading"),
            TextBlock(text="1. 准确描述各时期特征（3分）", style="normal"),
            TextBlock(text="2. 正确使用专业术语（2分）", style="normal")
        ],
        metadata={"file_name": "test_question.docx"}
    )

    try:
        agent_input = formatter.format_for_agents(test_content)
        print("试题文本:")
        print(agent_input.question_text)
        print("\n评分标准:")
        print(agent_input.scoring_standard)
    except Exception as e:
        print(f"格式化失败: {e}")