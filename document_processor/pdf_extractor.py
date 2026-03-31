"""
PDF文档提取器
使用pdf2image和PyMuPDF提取PDF文档内容，每页转换为图片
优化版本：添加日志记录、错误处理和重试机制
"""
import os
import io
import logging
import time
from typing import List, Optional, Tuple
from pathlib import Path
from functools import wraps

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


# 配置日志记录器
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1.0, exceptions=(Exception,)):
    """
    重试装饰器，用于在失败时重试操作

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
        exceptions: 触发重试的异常类型
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {str(e)}"
                        )
                        time.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        logger.error(f"{func.__name__} 在 {max_retries + 1} 次尝试后失败: {str(e)}")
                        raise
            raise last_exception
        return wrapper
    return decorator


class PDFExtractor:
    """PDF文档提取器"""

    def __init__(self, dpi: Optional[int] = None):
        """
        初始化PDF提取器

        Args:
            dpi: 图片转换DPI（如果为None，则尝试从配置获取，默认150）
        """
        if dpi is None:
            # 尝试从配置获取DPI
            try:
                from utils.config import get_config
                config = get_config()
                self.dpi = config.get("document_processor.pdf_dpi", 150)
            except ImportError:
                self.dpi = 150
        else:
            self.dpi = dpi

        logger.info(f"初始化PDF提取器，DPI={self.dpi}")
        self._check_dependencies()

    def _check_dependencies(self):
        """检查依赖是否可用"""
        if not PDF2IMAGE_AVAILABLE:
            logger.error("pdf2image未安装")
            raise ImportError(
                "pdf2image未安装，请运行: pip install pdf2image poppler-utils"
            )
        if not PYMUPDF_AVAILABLE:
            logger.error("PyMuPDF未安装")
            raise ImportError(
                "PyMuPDF未安装，请运行: pip install pymupdf"
            )
        logger.debug("PDF提取器依赖检查通过")

    @retry_on_failure(max_retries=2, delay=0.5)
    def extract(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> DocumentContent:
        """
        提取PDF文档内容，每页转换为图片

        Args:
            pdf_path: PDF文档路径
            start_page: 起始页码（从1开始，如果为None则从第1页开始）
            end_page: 结束页码（包含此页，如果为None则到最后一页）

        Returns:
            DocumentContent: 文档内容
        """
        if not os.path.exists(pdf_path):
            error_msg = f"PDF文档不存在: {pdf_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"开始处理PDF文档: {os.path.basename(pdf_path)}")

        # 获取PDF总页数
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()
        except Exception as e:
            error_msg = f"无法打开PDF文件: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        # 处理页码范围
        if start_page is None:
            start_page = 1
        if end_page is None:
            end_page = total_pages

        # 验证页码范围
        if start_page < 1:
            start_page = 1
        if end_page > total_pages:
            end_page = total_pages
        if start_page > end_page:
            error_msg = f"起始页码({start_page})不能大于结束页码({end_page})"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"处理页码范围: {start_page}-{end_page} (共{total_pages}页)")

        # 提取图片（每页转换为图片）
        images = self._extract_pages_as_images(pdf_path, start_page, end_page)

        # 提取文本（尝试从PDF中提取原始文本）
        text_blocks = self._extract_text_from_pdf(pdf_path, start_page, end_page)

        # 创建文档内容对象
        content = DocumentContent(
            images=images,
            text_blocks=text_blocks,
            metadata={
                "file_path": pdf_path,
                "file_name": os.path.basename(pdf_path),
                "total_pages": total_pages,
                "processed_pages": end_page - start_page + 1,
                "page_range": f"{start_page}-{end_page}",
                "total_text_blocks": len(text_blocks),
                "source_type": "pdf"
            }
        )

        logger.info(f"PDF提取完成: {len(images)} 张图片, {len(text_blocks)} 个文本块")
        return content

    @retry_on_failure(max_retries=2, delay=0.5)
    def _extract_pages_as_images(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> List[DocumentImage]:
        """
        将PDF指定页面转换为图片

        Args:
            pdf_path: PDF文档路径
            start_page: 起始页码（从1开始）
            end_page: 结束页码（包含此页）

        Returns:
            图片列表，每页一张图片
        """
        images = []

        try:
            # 优先使用PyMuPDF直接转换（减少依赖）
            if PYMUPDF_AVAILABLE:
                images = self._extract_with_pymupdf(pdf_path, start_page, end_page)
            elif PDF2IMAGE_AVAILABLE:
                # 回退到pdf2image
                images = self._extract_with_pdf2image(pdf_path, start_page, end_page)
            else:
                error_msg = "需要安装PyMuPDF或pdf2image来处理PDF文件"
                logger.error(error_msg)
                raise ImportError(error_msg)

        except Exception as e:
            error_msg = f"PDF转图片失败: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

        logger.debug(f"成功提取 {len(images)} 张图片")
        return images

    @retry_on_failure(max_retries=2, delay=0.5)
    def _extract_with_pymupdf(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> List[DocumentImage]:
        """
        使用PyMuPDF直接转换PDF页面为图片

        Args:
            pdf_path: PDF文档路径
            start_page: 起始页码（从1开始）
            end_page: 结束页码（包含此页）

        Returns:
            图片列表
        """
        images = []
        doc = fitz.open(pdf_path)

        try:
            # 处理页码范围
            if start_page is None:
                start_page = 1
            if end_page is None:
                end_page = len(doc)

            # 转换为0-based索引
            start_idx = start_page - 1
            end_idx = end_page  # end_page是包含的，所以这里不减1

            for page_idx in range(start_idx, end_idx):
                if page_idx >= len(doc):
                    break

                page = doc[page_idx]

                # 使用PyMuPDF的get_pixmap方法转换页面为图片
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)  # 缩放矩阵
                pix = page.get_pixmap(matrix=mat)

                # 将 pixmap 转换为 PNG 字节数据
                img_data = pix.tobytes("png")

                # 创建图片对象
                image = DocumentImage(
                    image_id=f"pdf_page_{page_idx+1:03d}",
                    image_data=img_data,
                    image_format="png",
                    image_type=ImageType.PDF_PAGE,
                    position_info={
                        "page_number": page_idx + 1,
                        "total_pages": len(doc),
                        "is_pdf_page": True,
                        "extraction_method": "pymupdf"
                    }
                )
                images.append(image)

            logger.info(f"PyMuPDF转换完成: {len(images)} 页PDF -> {len(images)} 张图片")

        except Exception as e:
            logger.error(f"PyMuPDF转换失败: {e}")
            raise
        finally:
            doc.close()

        return images

    def _extract_with_pdf2image(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> List[DocumentImage]:
        """
        使用pdf2image转换PDF页面为图片

        Args:
            pdf_path: PDF文档路径
            start_page: 起始页码（从1开始）
            end_page: 结束页码（包含此页）

        Returns:
            图片列表
        """
        images = []

        # 构建页码列表
        page_numbers = None
        if start_page is not None or end_page is not None:
            # 获取总页数
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            doc.close()

            if start_page is None:
                start_page = 1
            if end_page is None:
                end_page = total_pages

            page_numbers = list(range(start_page, end_page + 1))

        # 使用pdf2image将PDF转换为图片
        pil_images = convert_from_path(pdf_path, dpi=self.dpi, first_page=start_page, last_page=end_page)

        for i, pil_img in enumerate(pil_images):
            # 计算实际页码
            actual_page = (start_page or 1) + i

            # 将PIL Image转换为字节
            img_byte_arr = io.BytesIO()
            pil_img.save(img_byte_arr, format='PNG')
            img_data = img_byte_arr.getvalue()

            # 创建图片对象
            image = DocumentImage(
                image_id=f"pdf_page_{actual_page:03d}",
                image_data=img_data,
                image_format="png",
                image_type=ImageType.PDF_PAGE,
                position_info={
                    "page_number": actual_page,
                    "total_pages": len(pil_images),
                    "is_pdf_page": True,
                    "extraction_method": "pdf2image"
                }
            )
            images.append(image)

        print(f"  pdf2image转换完成: {len(images)} 页PDF -> {len(images)} 张图片")

        return images

    def _extract_text_from_pdf(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> List[TextBlock]:
        """
        从PDF中提取指定页面的文本内容

        Args:
            pdf_path: PDF文档路径
            start_page: 起始页码（从1开始）
            end_page: 结束页码（包含此页）

        Returns:
            文本块列表
        """
        text_blocks = []

        try:
            # 使用PyMuPDF提取文本
            doc = fitz.open(pdf_path)

            # 处理页码范围
            if start_page is None:
                start_page = 1
            if end_page is None:
                end_page = len(doc)

            # 转换为0-based索引
            start_idx = start_page - 1
            end_idx = end_page

            for page_idx in range(start_idx, end_idx):
                if page_idx >= len(doc):
                    break

                page = doc[page_idx]
                text = page.get_text().strip()

                if text:
                    # 按段落分割文本
                    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

                    for para in paragraphs:
                        text_block = TextBlock(
                            text=para,
                            style="pdf_text",
                            is_after_image=False,
                            position_info={
                                "page_number": page_idx + 1,
                                "extraction_method": "pymupdf_text"
                            }
                        )
                        text_blocks.append(text_block)

            doc.close()

            print(f"  文本提取: {len(text_blocks)} 个文本块 (页面 {start_page}-{end_page})")

        except Exception as e:
            print(f"  PDF文本提取警告: {e}")
            # 如果文本提取失败，返回空列表，后续依赖图片识别

        return text_blocks

    def extract_with_ocr_fallback(self, pdf_path: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> DocumentContent:
        """
        提取PDF指定页面内容，如果文本提取失败，则标记为需要OCR识别

        Args:
            pdf_path: PDF文档路径
            start_page: 起始页码（从1开始）
            end_page: 结束页码（包含此页）

        Returns:
            DocumentContent: 文档内容，标记需要OCR处理的页面
        """
        content = self.extract(pdf_path, start_page, end_page)

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