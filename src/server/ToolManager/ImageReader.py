"""图像读取工具"""
import io
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from PIL import Image
import numpy as np
from .ToolRegistry import BaseTool
from config import settings

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    print("PaddleOCR未安装，图像OCR功能将不可用")


class ImageReaderTool(BaseTool):
    """图像读取工具"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="image_reader",
            description="读取图像文件，进行OCR文字识别",
            config=config or {}
        )
        
        self.language = self.config.get("language", settings.OCR_LANGUAGE)
        self.use_gpu = self.config.get("use_gpu", settings.OCR_USE_GPU)
        self.enable_detection = self.config.get("enable_detection", True)
        self.enable_recognition = self.config.get("enable_recognition", True)
        self.enable_classification = self.config.get("enable_classification", False)
        
        # 初始化PaddleOCR
        self.ocr_engine = None
        if PADDLEOCR_AVAILABLE:
            try:
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=self.enable_classification,
                    lang=self.language,
                    use_gpu=self.use_gpu,
                    show_log=False
                )
            except Exception as e:
                print(f"初始化PaddleOCR失败: {e}")
                self.ocr_engine = None
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """处理图像文件"""
        if isinstance(input_data, str):
            # 文件路径
            file_path = Path(input_data)
        elif isinstance(input_data, bytes):
            # 图像字节内容
            return await self._process_image_bytes(input_data)
        else:
            raise ValueError("输入数据必须是文件路径或图像字节内容")
        
        if not file_path.exists():
            raise FileNotFoundError(f"图像文件不存在: {file_path}")
        
        # 检查文件格式
        if not self._is_supported_image_format(file_path):
            raise ValueError(f"不支持的图像格式: {file_path.suffix}")
        
        try:
            # 打开图像
            image = Image.open(file_path)
            
            result = {
                "file_path": str(file_path),
                "image_info": self._get_image_info(image),
                "ocr_results": [],
                "text_content": "",
                "processing_info": {
                    "ocr_enabled": self.ocr_engine is not None,
                    "text_regions": 0,
                    "total_text_length": 0
                }
            }
            
            # 进行OCR识别
            if self.ocr_engine and self.enable_recognition:
                ocr_results = await self._perform_ocr(image)
                result["ocr_results"] = ocr_results
                result["text_content"] = self._extract_text_from_ocr(ocr_results)
                result["processing_info"]["text_regions"] = len(ocr_results)
                result["processing_info"]["total_text_length"] = len(result["text_content"])
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"图像处理失败: {str(e)}")
    
    async def _process_image_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """处理图像字节内容"""
        try:
            # 从字节创建图像
            image = Image.open(io.BytesIO(image_bytes))
            
            result = {
                "file_path": "memory",
                "image_info": self._get_image_info(image),
                "ocr_results": [],
                "text_content": "",
                "processing_info": {
                    "ocr_enabled": self.ocr_engine is not None,
                    "text_regions": 0,
                    "total_text_length": 0
                }
            }
            
            # 进行OCR识别
            if self.ocr_engine and self.enable_recognition:
                ocr_results = await self._perform_ocr(image)
                result["ocr_results"] = ocr_results
                result["text_content"] = self._extract_text_from_ocr(ocr_results)
                result["processing_info"]["text_regions"] = len(ocr_results)
                result["processing_info"]["total_text_length"] = len(result["text_content"])
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"图像字节处理失败: {str(e)}")
    
    async def _perform_ocr(self, image: Image.Image) -> List[Dict[str, Any]]:
        """执行OCR识别"""
        if not self.ocr_engine:
            return []
        
        try:
            # 转换图像格式
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 转换为numpy数组
            img_array = np.array(image)
            
            # 执行OCR
            ocr_results = self.ocr_engine.ocr(img_array, cls=self.enable_classification)
            
            # 处理结果
            processed_results = []
            
            if ocr_results and ocr_results[0]:
                for line in ocr_results[0]:
                    if line:
                        # 提取边界框和文本
                        bbox = line[0]  # 边界框坐标
                        text_info = line[1]  # (文本, 置信度)
                        
                        if len(text_info) >= 2:
                            text = text_info[0]
                            confidence = text_info[1]
                            
                            processed_results.append({
                                "bbox": bbox,
                                "text": text,
                                "confidence": confidence,
                                "center": self._calculate_bbox_center(bbox)
                            })
            
            return processed_results
            
        except Exception as e:
            print(f"OCR识别失败: {e}")
            return []
    
    def _extract_text_from_ocr(self, ocr_results: List[Dict[str, Any]]) -> str:
        """从OCR结果中提取文本"""
        texts = []
        
        # 按位置排序文本
        sorted_results = sorted(ocr_results, key=lambda x: (x["center"][1], x["center"][0]))
        
        for result in sorted_results:
            texts.append(result["text"])
        
        return "\n".join(texts)
    
    def _calculate_bbox_center(self, bbox: List[List[float]]) -> Tuple[float, float]:
        """计算边界框中心点"""
        x_coords = [point[0] for point in bbox]
        y_coords = [point[1] for point in bbox]
        
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        
        return (center_x, center_y)
    
    def _get_image_info(self, image: Image.Image) -> Dict[str, Any]:
        """获取图像信息"""
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
            "size_bytes": len(image.tobytes()) if hasattr(image, 'tobytes') else 0,
            "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
        }
    
    def _is_supported_image_format(self, file_path: Path) -> bool:
        """检查是否支持该图像格式"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        return file_path.suffix.lower() in supported_formats
    
    def validate_config(self) -> bool:
        """验证工具配置"""
        try:
            # 检查语言设置
            supported_languages = ['ch', 'en', 'ja', 'ko', 'fr', 'german', 'it', 'xi', 'pu', 'ru', 'ar', 'ta', 'ug', 'fa', 'ur', 'rs', 'oc', 'rsc', 'bg', 'uk', 'be', 'te', 'kn', 'ch_tra', 'hi', 'mr', 'ne', 'hi', 'sa', 'ml', 'cy', 'ar', 'ta', 'ug', 'fa', 'ur', 'rs', 'oc', 'rsc', 'bg', 'uk', 'be', 'te', 'kn', 'ch_tra', 'hi', 'mr', 'ne', 'hi', 'sa', 'ml', 'cy']
            
            if self.language not in supported_languages:
                print(f"不支持的语言: {self.language}")
                return False
            
            # 检查其他配置
            if not isinstance(self.use_gpu, bool):
                return False
            
            if not isinstance(self.enable_detection, bool):
                return False
            
            if not isinstance(self.enable_recognition, bool):
                return False
            
            if not isinstance(self.enable_classification, bool):
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式"""
        return ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """获取处理能力"""
        return {
            "ocr_enabled": self.ocr_engine is not None,
            "text_detection": self.enable_detection,
            "text_recognition": self.enable_recognition,
            "text_classification": self.enable_classification,
            "language": self.language,
            "gpu_acceleration": self.use_gpu,
            "supported_languages": ['ch', 'en', 'ja', 'ko', 'fr', 'german', 'it', 'xi', 'pu', 'ru', 'ar', 'ta', 'ug', 'fa', 'ur', 'rs', 'oc', 'rsc', 'bg', 'uk', 'be', 'te', 'kn', 'ch_tra', 'hi', 'mr', 'ne', 'hi', 'sa', 'ml', 'cy']
        }
    
    def get_ocr_engine_status(self) -> Dict[str, Any]:
        """获取OCR引擎状态"""
        return {
            "paddleocr_available": PADDLEOCR_AVAILABLE,
            "engine_initialized": self.ocr_engine is not None,
            "language": self.language,
            "use_gpu": self.use_gpu,
            "capabilities": self.get_processing_capabilities()
        }
