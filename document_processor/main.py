"""
文档处理器主模块
整合Word提取、PDF提取、图片描述生成和文本格式化功能
支持从配置加载参数
"""

import os
import time
from typing import Optional, Union
from pathlib import Path

from .word_extractor import WordExtractor
from .pdf_extractor import PDFExtractor
from .image_describer import ImageDescriber
from .text_formatter import BiologyQuestionFormatter
from .models import DocumentContent, AgentInput


class DocumentProcessor:
    """文档处理器主类，支持Word和PDF格式"""

    def __init__(
        self,
        config: Optional[dict] = None,
        ollama_base_url: Optional[str] = None,
        ollama_model: Optional[str] = None,
        enable_image_descriptions: bool = True,
        pdf_dpi: int = 150
    ):
        """
        初始化文档处理器

        Args:
            config: 配置字典（可选，如果提供则优先使用）
            ollama_base_url: Ollama API基础URL
            ollama_model: Ollama模型名称
            enable_image_descriptions: 是否启用图片描述生成
            pdf_dpi: PDF转图片的DPI
        """
        # 从配置或参数获取设置
        if config:
            self.ollama_base_url = config.get("ollama_base_url")
            self.ollama_model = config.get("ollama_model")
            self.enable_image_descriptions = config.get("enable_image_descriptions")
            self.pdf_dpi = config.get("pdf_dpi")

            # 如果config字典中缺少值（None），尝试从全局配置获取
            try:
                from utils.config import get_config
                global_config = get_config()
                if self.ollama_base_url is None:
                    self.ollama_base_url = global_config.get("ollama.base_url")
                if self.ollama_model is None:
                    self.ollama_model = global_config.get("ollama.model")
                if self.enable_image_descriptions is None:
                    self.enable_image_descriptions = global_config.get("document_processor.enable_image_descriptions")
                if self.pdf_dpi is None:
                    self.pdf_dpi = global_config.get("document_processor.pdf_dpi")
            except ImportError:
                # 如果配置模块不可用，使用硬编码默认值
                if self.ollama_base_url is None:
                    self.ollama_base_url = "http://localhost:11434"
                if self.ollama_model is None:
                    self.ollama_model = "qwen3-vl:8b"
                if self.enable_image_descriptions is None:
                    self.enable_image_descriptions = True
                if self.pdf_dpi is None:
                    self.pdf_dpi = 150
        else:
            # 尝试从全局配置获取值
            try:
                from utils.config import get_config
                global_config = get_config()
                if ollama_base_url is None:
                    self.ollama_base_url = global_config.get("ollama.base_url")
                else:
                    self.ollama_base_url = ollama_base_url

                if ollama_model is None:
                    self.ollama_model = global_config.get("ollama.model")
                else:
                    self.ollama_model = ollama_model

                if enable_image_descriptions is None:
                    self.enable_image_descriptions = global_config.get("document_processor.enable_image_descriptions")
                else:
                    self.enable_image_descriptions = enable_image_descriptions

                if pdf_dpi is None:
                    self.pdf_dpi = global_config.get("document_processor.pdf_dpi")
                else:
                    self.pdf_dpi = pdf_dpi
            except ImportError:
                # 如果配置模块不可用，使用参数或硬编码默认值
                if ollama_base_url is None:
                    self.ollama_base_url = "http://localhost:11434"
                else:
                    self.ollama_base_url = ollama_base_url

                if ollama_model is None:
                    self.ollama_model = "qwen3-vl:8b"
                else:
                    self.ollama_model = ollama_model

                if enable_image_descriptions is None:
                    self.enable_image_descriptions = True
                else:
                    self.enable_image_descriptions = enable_image_descriptions

                if pdf_dpi is None:
                    self.pdf_dpi = 150
                else:
                    self.pdf_dpi = pdf_dpi

        # 初始化提取器
        self.word_extractor = WordExtractor()
        self.pdf_extractor = PDFExtractor(dpi=self.pdf_dpi)
        self.describer = ImageDescriber(self.ollama_base_url, self.ollama_model) if self.enable_image_descriptions else None
        self.formatter = BiologyQuestionFormatter()

        # 处理统计
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_images": 0,
            "total_text_blocks": 0,
            "total_pdf_pages": 0,
            "processing_times": []
        }

    def process_document(self, file_path: str) -> AgentInput:
        """
        处理文档（Word或PDF），生成智能体输入

        Args:
            file_path: 文档路径（支持.docx或.pdf）

        Returns:
            智能体输入对象

        Raises:
            FileNotFoundError: 如果文档不存在
            ValueError: 如果文档格式不支持
        """
        start_time = time.time()

        try:
            print(f"开始处理文档: {os.path.basename(file_path)}")

            # 1. 根据文件类型提取文档内容
            print("步骤1: 提取文档内容...")
            content = self._extract_content(file_path)

            # 更新统计
            self.stats["total_images"] = len(content.images)
            self.stats["total_text_blocks"] = len(content.text_blocks)
            if content.metadata and content.metadata.get("source_type") == "pdf":
                self.stats["total_pdf_pages"] = content.metadata.get("total_pages", 0)

            # 2. 生成图片描述（如果启用）
            if self.describer and content.images:
                print(f"步骤2: 为 {len(content.images)} 张图片生成描述...")
                image_descriptions = self.describer.describe_images(content.images)
                content.image_descriptions = image_descriptions
            else:
                print("步骤2: 图片描述生成已禁用或无需处理")

            # 3. 格式化输出
            print("步骤3: 格式化输出...")
            agent_input = self.formatter.format_for_agents(content)
            content.formatted_text = agent_input.question_text

            # 记录成功
            processing_time = time.time() - start_time
            self.stats["successful"] += 1
            self.stats["total_processed"] += 1
            self.stats["processing_times"].append(processing_time)

            print(f"文档处理完成! 用时: {processing_time:.2f} 秒")
            print(f"  图片/页数: {len(content.images)}")
            print(f"  文本块: {len(content.text_blocks)} 个")
            if content.metadata and content.metadata.get("source_type"):
                print(f"  文档类型: {content.metadata['source_type']}")

            return agent_input

        except Exception as e:
            # 记录失败
            processing_time = time.time() - start_time
            self.stats["failed"] += 1
            self.stats["total_processed"] += 1
            self.stats["processing_times"].append(processing_time)

            print(f"文档处理失败: {e}")
            raise

    def _extract_content(self, file_path: str) -> DocumentContent:
        """
        根据文件扩展名选择提取器

        Args:
            file_path: 文档路径

        Returns:
            文档内容

        Raises:
            ValueError: 如果文件格式不支持
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext in ['.docx', '.doc']:
            return self.word_extractor.extract(file_path)
        elif file_ext == '.pdf':
            return self.pdf_extractor.extract(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}。支持格式: .docx, .pdf")

    def process_documents(
        self,
        file_paths: list,
        output_dir: Optional[str] = None
    ) -> dict:
        """
        批量处理文档

        Args:
            file_paths: 文档路径列表（支持混合格式）
            output_dir: 输出目录（如果为None则不保存输出文件）

        Returns:
            处理结果统计
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(file_paths),
            "start_time": time.time()
        }

        for i, file_path in enumerate(file_paths, 1):
            print(f"\n处理进度: {i}/{len(file_paths)}")

            try:
                # 处理文档
                agent_input = self.process_document(file_path)

                # 保存输出（如果需要）
                if output_dir:
                    self._save_output(agent_input, file_path, output_dir)

                # 记录成功
                results["successful"].append({
                    "file": file_path,
                    "metadata": agent_input.metadata
                })

            except Exception as e:
                # 记录失败
                results["failed"].append({
                    "file": file_path,
                    "error": str(e)
                })

        results["end_time"] = time.time()
        results["total_time"] = results["end_time"] - results["start_time"]

        return results

    def _save_output(
        self,
        agent_input: AgentInput,
        file_path: str,
        output_dir: str
    ) -> str:
        """
        保存处理结果

        Args:
            agent_input: 智能体输入对象
            file_path: 原始文档路径
            output_dir: 输出目录

        Returns:
            保存的文件路径
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成输出文件名
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}_processed.txt")

        # 保存内容
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"文档: {os.path.basename(file_path)}\n")
            f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            f.write("【试题内容】\n")
            f.write("-" * 40 + "\n")
            f.write(agent_input.question_text)
            f.write("\n\n")

            f.write("【评分标准】\n")
            f.write("-" * 40 + "\n")
            f.write(agent_input.scoring_standard)
            f.write("\n\n")

            f.write("【元数据】\n")
            f.write("-" * 40 + "\n")
            for key, value in agent_input.metadata.items():
                f.write(f"{key}: {value}\n")

        print(f"输出已保存到: {output_file}")

        return output_file

    def get_statistics(self) -> dict:
        """
        获取处理统计信息

        Returns:
            统计信息字典
        """
        if not self.stats["processing_times"]:
            avg_time = 0
        else:
            avg_time = sum(self.stats["processing_times"]) / len(self.stats["processing_times"])

        stats_summary = {
            "total_processed": self.stats["total_processed"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "total_images": self.stats["total_images"],
            "total_text_blocks": self.stats["total_text_blocks"],
            "total_pdf_pages": self.stats["total_pdf_pages"],
            "average_processing_time": avg_time,
            "success_rate": (
                self.stats["successful"] / self.stats["total_processed"] * 100
                if self.stats["total_processed"] > 0
                else 0
            )
        }

        return stats_summary

    def print_statistics(self) -> None:
        """打印处理统计信息"""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("文档处理统计")
        print("=" * 60)
        print(f"总处理文档数: {stats['total_processed']}")
        print(f"成功: {stats['successful']}")
        print(f"失败: {stats['failed']}")
        if self.stats["total_processed"] > 0:
            print(f"成功率: {stats['success_rate']:.1f}%")
        else:
            print("成功率: 0.0%")
        print(f"平均处理时间: {stats['average_processing_time']:.2f}秒")
        print(f"处理总图片/页数: {stats['total_images']}")
        if stats['total_pdf_pages'] > 0:
            print(f"其中PDF页数: {stats['total_pdf_pages']}")
        print(f"处理总文本块数: {stats['total_text_blocks']}")
        print("=" * 60)


# 使用示例
if __name__ == "__main__":
    # 从配置加载
    try:
        from utils.config import get_config
        config_obj = get_config()

        # 从配置创建处理器
        processor = DocumentProcessor(
            config={
                "ollama_base_url": config_obj.get("ollama.base_url"),
                "ollama_model": config_obj.get("ollama.model"),
                "enable_image_descriptions": config_obj.get("document_processor.enable_image_descriptions"),
                "pdf_dpi": config_obj.get("document_processor.pdf_dpi")
            }
        )
        print("从配置初始化文档处理器")
    except ImportError:
        print("配置模块不可用，使用默认设置")
        processor = DocumentProcessor(
            ollama_base_url="http://localhost:11434",
            enable_image_descriptions=True
        )

    # 测试文档路径
    test_docs = []

    # 查找可用的测试文档（支持Word和PDF）
    possible_docs = [
        "test_question.docx",
        "test_question.pdf",
        "sample_question.docx",
        "sample_question.pdf",
        "生物试题示例.docx",
        "生物试题示例.pdf"
    ]

    for doc in possible_docs:
        if os.path.exists(doc):
            test_docs.append(doc)

    if test_docs:
        print(f"找到 {len(test_docs)} 个测试文档")
        results = processor.process_documents(test_docs, output_dir="output")
        processor.print_statistics()

        # 打印成功和失败列表
        if results["failed"]:
            print("\n失败的文档:")
            for fail in results["failed"]:
                print(f" - {fail['file']}: {fail['error']}")
    else:
        print("未找到测试文档，跳过演示")
        print("请创建一个测试Word或PDF文档进行测试")