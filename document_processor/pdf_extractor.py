"""
PDF文档提取器
使用pdf2image和PyMuPDF提取PDF文档内容，每页转换为图片
"""
import os
import io
from typing import List, Optional, Tuple
from pathlib import Path

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from PIL import Image
from .models import DocumentImage, TextBlock, DocumentContent, ImageType


class PDFExtractor:
    """PDF文档提取器"""

    def __init__(self, dpi: int = 150):
        """
        初始化PDF提取器

        Args:
            dpi: 图片转换DPI（默认150）
        """
        self.dpi = dpi
        self._check_dependencies()

    def _check_dependencies(self):
        """检查依赖是否可用"""
        if not PDF2IMAGE_AVAILABLE:
            raise ImportError(
                "pdf2image未安装，请运行: pip install pdf2image poppler-utils"
            )
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF未安装，请运行: pip install pymupdf"
            )

    def extract(self, pdf_path: str) -> DocumentContent:
        """
        提取PDF文档内容，每页转换为图片

        Args:
            pdf_path: PDF文档路径

        Returns:
            DocumentContent: 文档内容
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文档不存在: {pdf_path}")

        print(f"开始处理PDF文档: {os.path.basename(pdf_path)}")

        # 提取图片（每页转换为图片）
        images = self._extract_pages_as_images(pdf_path)

        # 提取文本（尝试从PDF中提取原始文本）
        text_blocks = self._extract_text_from_pdf(pdf_path)

        # 创建文档内容对象
        content = DocumentContent(
            images=images,
            text_blocks=text_blocks,
            metadata={
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path),
                "total_pages": len(images),
                "total_text_blocks": len(text_blocks),
                "source_type": "pdf"
            }
        )

        return content

    def _extract_pages_as_images(self, pdf_path: str) -> List[DocumentImage]:
        """
        将PDF每页转换为图片

        Args:
            pdf_path: PDF文档路径

        Returns:
            图片列表，每页一张图片
        """
        images = []

        try:
            # 使用pdf2image将PDF转换为图片
            pil_images = convert_from_path(pdf_path, dpi=self.dpi)

            for i, pil_img in enumerate(pil_images):
                # 将PIL Image转换为字节
                img_byte_arr = io.BytesIO()
                pil_img.save(img_byte_arr, format='PNG')
                img_data = img_byte_arr.getvalue()

                # 创建图片对象
                image = DocumentImage(
                    image_id=f"pdf_page_{i+1:03d}",
                    image_data=img_data,
                    image_format="png",
                    image_type=ImageType.PDF_PAGE,  # PDF页面类型
                    position_info={
                        "page_number": i + 1,
                        "total_pages": len(pil_images),
                        "is_pdf_page": True
                    }
                )
                images.append(image)

            print(f"  转换完成: {len(images)} 页PDF -> {len(images)} 张图片")

        except Exception as e:
            raise RuntimeError(f"PDF转图片失败: {e}")

        return images

    def _extract_text_from_pdf(self, pdf_path: str) -> List[TextBlock]:
        """
        从PDF中提取文本内容

        Args:
            pdf_path: PDF文档路径

        Returns:
            文本块列表
        """
        text_blocks = []

        try:
            # 使用PyMuPDF提取文本
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text().strip()

                if text:
                    # 按段落分割文本
                    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

                    for para in paragraphs:
                        text_block = TextBlock(
                            text=para,
                            style="pdf_text",
                            is_after_image=False
                        )
                        text_blocks.append(text_block)

            doc.close()

            print(f"  文本提取: {len(text_blocks)} 个文本块")

        except Exception as e:
            print(f"  PDF文本提取警告: {e}")
            # 如果文本提取失败，返回空列表，后续依赖图片识别

        return text_blocks

    def extract_with_ocr_fallback(self, pdf_path: str) -> DocumentContent:
        """
        提取PDF内容，如果文本提取失败，则标记为需要OCR识别

        Args:
            pdf_path: PDF文档路径

        Returns:
            DocumentContent: 文档内容，标记需要OCR处理的页面
        """
        content = self.extract(pdf_path)

        # 如果文本块很少或没有，标记图片为需要OCR
        if len(content.text_blocks) < 3:  # 阈值可调整
            for image in content.images:
                image.description = None  # 确保描述为空，需要OCR识别

        return content


# 使用示例
if __name__ == "__main__":
    # 测试代码
    try:
        extractor = PDFExtractor(dpi=150)

        # 使用一个示例PDF路径
        test_pdf = "示例文档.pdf"  # 需要实际存在的文档
        if os.path.exists(test_pdf):
            content = extractor.extract(test_pdf)
            print(f"提取成功: {len(content.images)} 页图片, {len(content.text_blocks)} 个文本块")

            # 显示一些元数据
            if content.metadata:
                print(f"元数据: {content.metadata}")
        else:
            print("测试PDF文档不存在，跳过测试")
    except ImportError as e:
        print(f"依赖缺失: {e}")
    except Exception as e:
        print(f"提取失败: {e}")