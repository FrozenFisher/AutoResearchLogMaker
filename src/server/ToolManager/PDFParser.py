"""PDF解析工具"""
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    fitz = None

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from .ToolRegistry import BaseTool
from server.config import settings


class PDFParserTool(BaseTool):
    """PDF解析工具"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="pdf_parser",
            description="解析PDF文件，提取文本和图像",
            config=config or {}
        )
        if not PYMUPDF_AVAILABLE:
            self.enabled = False
            print("⚠️  PDF解析工具已禁用: PyMuPDF 未安装")
            print("   安装命令: pip install pymupdf")
        self.extract_images = self.config.get("extract_images", True)
        self.extract_tables = self.config.get("extract_tables", True)
        self.max_pages = self.config.get("max_pages", 100)
        self.language = self.config.get("language", "zh")
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """处理PDF文件"""
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF 未安装，无法解析PDF文件。"
                "请运行: pip install pymupdf"
            )
        if isinstance(input_data, str):
            # 文件路径
            file_path = Path(input_data)
        elif isinstance(input_data, bytes):
            # PDF内容字节
            return await self._process_pdf_bytes(input_data)
        else:
            raise ValueError("输入数据必须是文件路径或PDF字节内容")
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"文件不是PDF格式: {file_path}")
        
        try:
            # 打开PDF文档
            doc = fitz.open(str(file_path))
            
            result = {
                "file_path": str(file_path),
                "page_count": len(doc),
                "text_content": "",
                "pages": [],
                "images": [],
                "tables": [],
                "metadata": {},
                "processing_info": {
                    "extracted_pages": 0,
                    "extracted_images": 0,
                    "extracted_tables": 0
                }
            }
            
            # 提取元数据
            result["metadata"] = self._extract_metadata(doc)
            
            # 处理页面
            pages_to_process = min(len(doc), self.max_pages)
            
            for page_num in range(pages_to_process):
                page = doc[page_num]
                page_data = await self._process_page(page, page_num)
                
                result["pages"].append(page_data)
                result["text_content"] += page_data["text"] + "\n"
                
                # 提取图像
                if self.extract_images:
                    images = await self._extract_page_images(page, page_num)
                    result["images"].extend(images)
                    result["processing_info"]["extracted_images"] += len(images)
                
                # 提取表格
                if self.extract_tables:
                    tables = await self._extract_page_tables(page, page_num)
                    result["tables"].extend(tables)
                    result["processing_info"]["extracted_tables"] += len(tables)
            
            result["processing_info"]["extracted_pages"] = pages_to_process
            
            doc.close()
            return result
            
        except Exception as e:
            raise RuntimeError(f"PDF解析失败: {str(e)}")
    
    async def _process_pdf_bytes(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """处理PDF字节内容"""
        try:
            # 从字节创建PDF文档
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            result = {
                "file_path": "memory",
                "page_count": len(doc),
                "text_content": "",
                "pages": [],
                "images": [],
                "tables": [],
                "metadata": {},
                "processing_info": {
                    "extracted_pages": 0,
                    "extracted_images": 0,
                    "extracted_tables": 0
                }
            }
            
            # 提取元数据
            result["metadata"] = self._extract_metadata(doc)
            
            # 处理页面
            pages_to_process = min(len(doc), self.max_pages)
            
            for page_num in range(pages_to_process):
                page = doc[page_num]
                page_data = await self._process_page(page, page_num)
                
                result["pages"].append(page_data)
                result["text_content"] += page_data["text"] + "\n"
                
                # 提取图像和表格
                if self.extract_images:
                    images = await self._extract_page_images(page, page_num)
                    result["images"].extend(images)
                    result["processing_info"]["extracted_images"] += len(images)
                
                if self.extract_tables:
                    tables = await self._extract_page_tables(page, page_num)
                    result["tables"].extend(tables)
                    result["processing_info"]["extracted_tables"] += len(tables)
            
            result["processing_info"]["extracted_pages"] = pages_to_process
            
            doc.close()
            return result
            
        except Exception as e:
            raise RuntimeError(f"PDF字节解析失败: {str(e)}")
    
    async def _process_page(self, page, page_num: int) -> Dict[str, Any]:
        """处理单个页面"""
        try:
            # 提取文本
            text = page.get_text()
            
            # 提取文本块
            text_blocks = page.get_text("dict")
            
            # 提取页面信息
            page_info = {
                "page_number": page_num + 1,
                "text": text,
                "text_blocks": text_blocks,
                "rect": page.rect,
                "rotation": page.rotation
            }
            
            return page_info
            
        except Exception as e:
            print(f"处理页面 {page_num + 1} 失败: {e}")
            return {
                "page_number": page_num + 1,
                "text": "",
                "text_blocks": {},
                "rect": None,
                "rotation": 0
            }
    
    async def _extract_page_images(self, page, page_num: int) -> List[Dict[str, Any]]:
        """提取页面图像"""
        images = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # 获取图像数据
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # 确保不是CMYK
                        img_data = pix.tobytes("png")
                        
                        image_info = {
                            "page_number": page_num + 1,
                            "image_index": img_index,
                            "xref": xref,
                            "width": pix.width,
                            "height": pix.height,
                            "colorspace": pix.colorspace.name if pix.colorspace else "unknown",
                            "data": img_data,
                            "format": "png"
                        }
                        
                        images.append(image_info)
                    
                    pix = None
                    
                except Exception as e:
                    print(f"提取图像 {img_index} 失败: {e}")
                    continue
            
        except Exception as e:
            print(f"提取页面 {page_num + 1} 图像失败: {e}")
        
        return images
    
    async def _extract_page_tables(self, page, page_num: int) -> List[Dict[str, Any]]:
        """提取页面表格"""
        tables = []
        
        try:
            # 使用PyMuPDF的表格提取功能
            table_list = page.find_tables()
            
            for table_index, table in enumerate(table_list):
                try:
                    # 提取表格数据
                    table_data = table.extract()
                    
                    table_info = {
                        "page_number": page_num + 1,
                        "table_index": table_index,
                        "bbox": table.bbox,
                        "data": table_data,
                        "rows": len(table_data),
                        "cols": len(table_data[0]) if table_data else 0
                    }
                    
                    tables.append(table_info)
                    
                except Exception as e:
                    print(f"提取表格 {table_index} 失败: {e}")
                    continue
            
        except Exception as e:
            print(f"提取页面 {page_num + 1} 表格失败: {e}")
        
        return tables
    
    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """提取PDF元数据"""
        try:
            metadata = doc.metadata
            
            return {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "keywords": metadata.get("keywords", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "page_count": len(doc),
                "file_size": doc.page_count  # 这里可以添加实际文件大小
            }
            
        except Exception as e:
            print(f"提取元数据失败: {e}")
            return {}
    
    def validate_config(self) -> bool:
        """验证工具配置"""
        try:
            # 检查配置参数
            if not isinstance(self.extract_images, bool):
                return False
            
            if not isinstance(self.extract_tables, bool):
                return False
            
            if not isinstance(self.max_pages, int) or self.max_pages <= 0:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return [".pdf"]
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """获取处理能力"""
        return {
            "text_extraction": True,
            "image_extraction": self.extract_images,
            "table_extraction": self.extract_tables,
            "metadata_extraction": True,
            "max_pages": self.max_pages,
            "supported_languages": ["zh", "en", "ja", "ko"]
        }
