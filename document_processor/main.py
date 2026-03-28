"""
文档处理器主模块
整合Word提取、图片描述生成和文本格式化功能
"""

import os
import time
from typing import Optional

from .word_extractor import WordExtractor
from .image_describer import ImageDescriber
from .text_formatter import BiologyQuestionFormatter
from .models import DocumentContent, AgentInput


class DocumentProcessor:
    """文档处理器主类"""

    def __init__(
        self,
        ollama_base_url: str = "http://localhost:11434",
        enable_image_descriptions: bool = True
    ):
        """
        初始化文档处理器

        Args:
            ollama_base_url: Ollama API基础URL
            enable_image_descriptions: 是否启用图片描述生成
        """
        self.extractor = WordExtractor()
        self.describer = ImageDescriber(ollama_base_url) if enable_image_descriptions else None
        self.formatter = BiologyQuestionFormatter()

        # 处理统计
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_images": 0,
            "total_text_blocks": 0,
            "processing_times": []
        }

    def process_document(self, docx_path: str) -> AgentInput:
        """
        处理Word文档，生成智能体输入

        Args:
            docx_path: Word文档路径

        Returns:
            智能体输入对象

        Raises:
            FileNotFoundError: 如果文档不存在
            ValueError: 如果文档格式错误
        """
        start_time = time.time()

        try:
            print(f"开始处理文档: {os.path.basename(docx_path)}")

            # 1. 提取文档内容
            print("步骤1: 提取文档内容...")
            content = self.extractor.extract(docx_path)

            self.stats["total_images"] = len(content.images)
            self.stats["total_text_blocks"] = len(content.text_blocks)

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
            print(f"  图片: {len(content.images)} 张")
            print(f"  文本块: {len(content.text_blocks)} 个")

            return agent_input

        except Exception as e:
            # 记录失败
            processing_time = time.time() - start_time
            self.stats["failed"] += 1
            self.stats["total_processed"] += 1
            self.stats["processing_times"].append(processing_time)

            print(f"文档处理失败: {e}")
            raise

    def process_documents(
        self,
        docx_paths: list,
        output_dir: Optional[str] = None
    ) -> dict:
        """
        批量处理文档

        Args:
            docx_paths: 文档路径列表
            output_dir: 输出目录（如果为None则不保存输出文件）

        Returns:
            处理结果统计
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(docx_paths),
            "start_time": time.time()
        }

        for i, docx_path in enumerate(docx_paths, 1):
            print(f"\n处理进度: {i}/{len(docx_paths)}")

            try:
                # 处理文档
                agent_input = self.process_document(docx_path)

                # 保存输出（如果需要）
                if output_dir:
                    self._save_output(agent_input, docx_path, output_dir)

                # 记录成功
                results["successful"].append({
                    "file": docx_path,
                    "metadata": agent_input.metadata
                })

            except Exception as e:
                # 记录失败
                results["failed"].append({
                    "file": docx_path,
                    "error": str(e)
                })

        results["end_time"] = time.time()
        results["total_time"] = results["end_time"] - results["start_time"]

        return results

    def _save_output(
        self,
        agent_input: AgentInput,
        docx_path: str,
        output_dir: str
    ) -> str:
        """
        保存处理结果

        Args:
            agent_input: 智能体输入对象
            docx_path:原始文档路径
            output_dir:输出目录

        Returns:
            保存的文件路径
        """
        #创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        #生成输出文件名
        base_name=os.path.splitext(os.path.basename(docx_path))[0]
        output_file=os.path.join(output_dir, f"{base_name}_processed.txt")

        #保存内容
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"文档: {os.path.basename(docx_path)}\n")
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

    def get_statistics(self)->dict:
        """
        获取处理统计信息

        Returns:
            统计信息字典
        """
        if not self.stats["processing_times"]:
            avg_time=0
        else:
            avg_time=sum(self.stats["processing_times"]) / len(self.stats["processing_times"])

        stats_summary={
            "total_processed":self.stats["total_processed"],
            "successful":self.stats["successful"],
            "failed":self.stats["failed"],
            "total_images":self.stats["total_images"],
            "total_text_blocks":self.stats["total_text_blocks"],
            "average_processing_time":avg_time,
            "success_rate":(
                self.stats["successful"] / self.stats["total_processed"] * 100
                if self.stats["total_processed"]>0
                else 0
            )
        }

        return stats_summary

    def print_statistics(self)->None:
        """打印处理统计信息"""
        stats=self.get_statistics()

        print("\n"+ "=" * 60)
        print("文档处理统计")
        print("=" * 60)
        print(f"总处理文档数: {stats['total_processed']}")
        print(f"成功: {stats['successful']}")
        print(f"失败: {stats['failed']}")
        if self.stats["total_processed"]>0:
            print(f"成功率: {stats['success_rate']:.1f}%")
        else:
            print("成功率: 0.0%")
        print(f"平均处理时间: {stats['average_processing_time']:.2f}秒")
        print(f"处理总图片数: {stats['total_images']}")
        print(f"处理总文本块数: {stats['total_text_blocks']}")
        print("=" *60)


# 使用示例
if __name__=="__main__":
    # 创建处理器
    processor=DocumentProcessor(
        ollama_base_url="http://localhost:11434",
        enable_image_descriptions=True
    )

    # 测试文档路径
    test_docs=[]

    # 查找可用的测试文档
    possible_docs=[
        "test_question.docx",
        "sample_question.docx",
        "生物试题示例.docx"
    ]

    for doc in possible_docs:
        if os.path.exists(doc):
            test_docs.append(doc)

    if test_docs:
        print(f"找到{len(test_docs)}个测试文档")
        results=processor.process_documents(test_docs, output_dir="output")
        processor.print_statistics()

        #打印成功和失败列表
        if results["failed"]:
            print("\n失败的文档:")
            for fail in results["failed"]:
                print(f" - {fail['file']}: {fail['error']}")
    else:
        print("未找到测试文档，跳过演示")
        print("请创建一个测试Word文档进行测试")