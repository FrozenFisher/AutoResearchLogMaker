"""文本处理工具"""
import re
from typing import Dict, List, Any, Optional
from .ToolRegistry import BaseTool


class TextProcessorTool(BaseTool):
    """文本处理工具"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(
            name="text_processor",
            description="处理文本内容，进行清理和格式化",
            config=config or {}
        )
        
        self.remove_extra_spaces = self.config.get("remove_extra_spaces", True)
        self.remove_special_chars = self.config.get("remove_special_chars", False)
        self.min_text_length = self.config.get("min_text_length", 10)
        self.max_text_length = self.config.get("max_text_length", 10000)
    
    async def process(self, input_data: Any) -> Dict[str, Any]:
        """处理文本数据"""
        if isinstance(input_data, str):
            text = input_data
        elif isinstance(input_data, dict) and "text_content" in input_data:
            text = input_data["text_content"]
        else:
            raise ValueError("输入数据必须是字符串或包含text_content的字典")
        
        try:
            # 文本清理
            cleaned_text = self._clean_text(text)
            
            # 文本分析
            analysis = self._analyze_text(cleaned_text)
            
            # 文本分段
            segments = self._segment_text(cleaned_text)
            
            result = {
                "original_text": text,
                "cleaned_text": cleaned_text,
                "text_analysis": analysis,
                "segments": segments,
                "processing_info": {
                    "original_length": len(text),
                    "cleaned_length": len(cleaned_text),
                    "segment_count": len(segments),
                    "processing_applied": {
                        "remove_extra_spaces": self.remove_extra_spaces,
                        "remove_special_chars": self.remove_special_chars
                    }
                }
            }
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"文本处理失败: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        cleaned = text
        
        # 移除多余空格
        if self.remove_extra_spaces:
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.strip()
        
        # 移除特殊字符
        if self.remove_special_chars:
            cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', cleaned)
        
        # 长度限制
        if len(cleaned) > self.max_text_length:
            cleaned = cleaned[:self.max_text_length] + "..."
        
        return cleaned
    
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """分析文本"""
        analysis = {
            "length": len(text),
            "word_count": len(text.split()),
            "line_count": len(text.split('\n')),
            "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
            "language_detection": self._detect_language(text),
            "has_numbers": bool(re.search(r'\d', text)),
            "has_special_chars": bool(re.search(r'[^\w\s\u4e00-\u9fff]', text)),
            "sentiment_score": self._calculate_sentiment(text)
        }
        
        return analysis
    
    def _segment_text(self, text: str) -> List[Dict[str, Any]]:
        """文本分段"""
        segments = []
        
        # 按段落分段
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for i, paragraph in enumerate(paragraphs):
            if len(paragraph) >= self.min_text_length:
                segments.append({
                    "segment_id": i + 1,
                    "type": "paragraph",
                    "content": paragraph,
                    "length": len(paragraph),
                    "word_count": len(paragraph.split())
                })
        
        # 如果没有段落，按句子分段
        if not segments:
            sentences = re.split(r'[.!?。！？]', text)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) >= self.min_text_length:
                    segments.append({
                        "segment_id": i + 1,
                        "type": "sentence",
                        "content": sentence,
                        "length": len(sentence),
                        "word_count": len(sentence.split())
                    })
        
        return segments
    
    def _detect_language(self, text: str) -> str:
        """检测语言（简单实现）"""
        # 中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 英文字符
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        # 日文字符
        japanese_chars = len(re.findall(r'[\u3040-\u309f\u30a0-\u30ff]', text))
        # 韩文字符
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        
        total_chars = chinese_chars + english_chars + japanese_chars + korean_chars
        
        if total_chars == 0:
            return "unknown"
        
        if chinese_chars / total_chars > 0.3:
            return "zh"
        elif japanese_chars / total_chars > 0.3:
            return "ja"
        elif korean_chars / total_chars > 0.3:
            return "ko"
        elif english_chars / total_chars > 0.3:
            return "en"
        else:
            return "mixed"
    
    def _calculate_sentiment(self, text: str) -> float:
        """计算情感分数（简单实现）"""
        # 简单的情感分析，基于关键词
        positive_words = ['好', '棒', '优秀', '满意', '喜欢', 'good', 'great', 'excellent', 'wonderful']
        negative_words = ['坏', '差', '糟糕', '不满', '讨厌', 'bad', 'terrible', 'awful', 'horrible']
        
        positive_count = sum(1 for word in positive_words if word in text.lower())
        negative_count = sum(1 for word in negative_words if word in text.lower())
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_words
        return max(-1.0, min(1.0, sentiment_score))  # 限制在-1到1之间
    
    def validate_config(self) -> bool:
        """验证工具配置"""
        try:
            if not isinstance(self.remove_extra_spaces, bool):
                return False
            
            if not isinstance(self.remove_special_chars, bool):
                return False
            
            if not isinstance(self.min_text_length, int) or self.min_text_length < 0:
                return False
            
            if not isinstance(self.max_text_length, int) or self.max_text_length <= 0:
                return False
            
            if self.min_text_length >= self.max_text_length:
                return False
            
            return True
            
        except Exception:
            return False
    
    def get_processing_capabilities(self) -> Dict[str, Any]:
        """获取处理能力"""
        return {
            "text_cleaning": True,
            "text_analysis": True,
            "text_segmentation": True,
            "language_detection": True,
            "sentiment_analysis": True,
            "min_text_length": self.min_text_length,
            "max_text_length": self.max_text_length,
            "supported_languages": ["zh", "en", "ja", "ko", "mixed"]
        }
