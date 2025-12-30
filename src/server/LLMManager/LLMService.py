"""LLM服务"""
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from server.config import settings
from .PromptManager import prompt_manager

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("LangChain未安装，LLM功能将不可用")


class LLMService:
    """LLM服务"""
    
    def __init__(self):
        self.llm_models = {}
        self._initialize_models()
    
    def _load_llm_config(self) -> Dict[str, Any]:
        """从配置文件加载LLM配置"""
        config_path = settings.USRDATA_DIR / "llm_config.json"
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "base_url": data.get("base_url") or settings.OPENAI_BASE_URL,
                        "api_key": data.get("api_key") or settings.OPENAI_API_KEY,
                        "default_model": data.get("default_model") or settings.DEFAULT_LLM_MODEL,
                    }
            except (IOError, json.JSONDecodeError):
                pass
        # 回退到环境变量配置
        return {
            "base_url": settings.OPENAI_BASE_URL,
            "api_key": settings.OPENAI_API_KEY,
            "default_model": settings.DEFAULT_LLM_MODEL,
        }
    
    def _get_available_models_from_api(self, base_url: str, api_key: Optional[str] = None) -> List[str]:
        """从API获取可用模型列表"""
        try:
            import httpx
        except ImportError:
            return []
        
        try:
            base = base_url.rstrip("/")
            # 兼容用户已经在 Base URL 里写了 /v1 的情况
            if base.endswith("/v1"):
                url = base + "/models"
            else:
                url = base + "/v1/models"
            
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
            
            raw_models = data.get("data", [])
            return [m.get("id") for m in raw_models if m.get("id")]
        except Exception as e:
            print(f"从API获取模型列表失败: {e}")
            return []
    
    def _initialize_models(self):
        """初始化LLM模型（从配置动态加载）"""
        if not LANGCHAIN_AVAILABLE:
            print("LangChain不可用，跳过模型初始化")
            return
        
        # 清空现有模型
        self.llm_models = {}
        
        # 加载配置
        config = self._load_llm_config()
        base_url = config.get("base_url")
        api_key = config.get("api_key")
        default_model = config.get("default_model")
        
        if not base_url:
            print("未配置 LLM Base URL，跳过模型初始化")
            return
        
        if not api_key:
            print("未配置 API Key，跳过模型初始化")
            return
        
        try:
            # 尝试从API获取可用模型列表
            available_models = self._get_available_models_from_api(base_url, api_key)
            
            # 确定要初始化的模型列表
            models_to_init = []
            if default_model:
                # 优先初始化默认模型
                if default_model in available_models:
                    models_to_init.append(default_model)
                elif available_models:
                    # 如果默认模型不在列表中，使用第一个可用模型
                    print(f"警告: 默认模型 '{default_model}' 不在可用模型列表中，将使用 '{available_models[0]}'")
                    models_to_init.append(available_models[0])
                else:
                    # 如果无法获取模型列表，尝试直接初始化默认模型
                    models_to_init.append(default_model)
            elif available_models:
                # 如果没有默认模型，初始化第一个可用模型
                models_to_init.append(available_models[0])
            
            # 初始化模型
            for model_name in models_to_init:
                try:
                    # 根据模型名称推断合适的 max_tokens
                    max_tokens = 2000
                    if "gpt-4" in model_name.lower() or "turbo" in model_name.lower():
                        max_tokens = 4000
                    elif "32k" in model_name.lower() or "128k" in model_name.lower():
                        max_tokens = 8000
                    
                    self.llm_models[model_name] = ChatOpenAI(
                        model=model_name,
                        api_key=api_key,
                        base_url=base_url,
                        temperature=0.7,
                        max_tokens=max_tokens
                    )
                    print(f"成功初始化模型: {model_name}")
                except Exception as e:
                    print(f"初始化模型 '{model_name}' 失败: {e}")
            
            if self.llm_models:
                print(f"成功初始化 {len(self.llm_models)} 个LLM模型: {list(self.llm_models.keys())}")
            else:
                print("警告: 未能初始化任何LLM模型")
            
        except Exception as e:
            print(f"初始化LLM模型失败: {e}")
    
    def reinitialize_models(self) -> Dict[str, Any]:
        """重新初始化模型（供外部调用）"""
        try:
            self._initialize_models()
            return {
                "success": True,
                "message": f"成功初始化 {len(self.llm_models)} 个模型",
                "models": list(self.llm_models.keys()),
                "count": len(self.llm_models)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"重新初始化失败: {str(e)}",
                "models": [],
                "count": 0
            }
    
    async def generate_summary(
        self, 
        content: str, 
        template_name: str = "default",
        model_name: str = None,
        custom_prompt: str = None,
        **kwargs
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """生成总结"""
        try:
            # 选择模型
            model_name = model_name or settings.DEFAULT_LLM_MODEL
            llm = self.llm_models.get(model_name)
            
            if not llm:
                return False, f"模型 '{model_name}' 不可用", None
            
            # 准备提示
            if custom_prompt:
                prompt = custom_prompt
            else:
                success, prompt = prompt_manager.format_template(
                    template_name, content=content, **kwargs
                )
                if not success:
                    return False, prompt, None
            
            # 生成总结
            messages = [
                SystemMessage(content="你是一个专业的研究助手，擅长分析和总结各种文档内容。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            summary = response.content
            
            # 生成元数据
            metadata = {
                "model_used": model_name,
                "template_used": template_name,
                "prompt_length": len(prompt),
                "response_length": len(summary),
                "generated_at": datetime.now().isoformat(),
                "custom_prompt": custom_prompt is not None
            }
            
            return True, summary, metadata
            
        except Exception as e:
            return False, f"生成总结失败: {str(e)}", None
    
    async def analyze_content(
        self, 
        content: str, 
        analysis_type: str = "general",
        model_name: str = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """分析内容"""
        try:
            model_name = model_name or settings.DEFAULT_LLM_MODEL
            llm = self.llm_models.get(model_name)
            
            if not llm:
                return False, None, {"error": f"模型 '{model_name}' 不可用"}
            
            # 根据分析类型选择提示
            prompts = {
                "general": "请分析以下内容的主要特点和关键信息：",
                "sentiment": "请分析以下内容的情感倾向和态度：",
                "keywords": "请提取以下内容的关键词和主题：",
                "structure": "请分析以下内容的结构和组织方式：",
                "quality": "请评估以下内容的质量和可信度："
            }
            
            prompt = prompts.get(analysis_type, prompts["general"])
            
            messages = [
                SystemMessage(content="你是一个专业的内容分析师。"),
                HumanMessage(content=f"{prompt}\n\n{content}")
            ]
            
            response = await llm.ainvoke(messages)
            analysis_result = response.content
            
            # 解析分析结果
            parsed_result = self._parse_analysis_result(analysis_result, analysis_type)
            
            metadata = {
                "analysis_type": analysis_type,
                "model_used": model_name,
                "content_length": len(content),
                "analysis_length": len(analysis_result),
                "generated_at": datetime.now().isoformat()
            }
            
            return True, parsed_result, metadata
            
        except Exception as e:
            return False, None, {"error": f"内容分析失败: {str(e)}"}
    
    async def generate_questions(
        self, 
        content: str, 
        question_count: int = 5,
        question_type: str = "comprehensive",
        model_name: str = None
    ) -> Tuple[bool, Optional[List[str]], Optional[Dict[str, Any]]]:
        """生成问题"""
        try:
            model_name = model_name or settings.DEFAULT_LLM_MODEL
            llm = self.llm_models.get(model_name)
            
            if not llm:
                return False, None, {"error": f"模型 '{model_name}' 不可用"}
            
            # 根据问题类型选择提示
            type_prompts = {
                "comprehensive": "请生成全面性的问题",
                "critical": "请生成批判性思考问题",
                "creative": "请生成创新性问题",
                "practical": "请生成实践性问题"
            }
            
            type_prompt = type_prompts.get(question_type, type_prompts["comprehensive"])
            
            prompt = f"""基于以下内容，请生成 {question_count} 个{type_prompt}：

内容：
{content}

要求：
1. 问题要有针对性和深度
2. 问题要能引发思考
3. 问题要简洁明了
4. 每个问题单独一行

问题："""
            
            messages = [
                SystemMessage(content="你是一个专业的问题生成专家。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            questions_text = response.content
            
            # 解析问题
            questions = self._parse_questions(questions_text)
            
            metadata = {
                "question_count": len(questions),
                "question_type": question_type,
                "model_used": model_name,
                "content_length": len(content),
                "generated_at": datetime.now().isoformat()
            }
            
            return True, questions, metadata
            
        except Exception as e:
            return False, None, {"error": f"生成问题失败: {str(e)}"}
    
    async def translate_content(
        self, 
        content: str, 
        target_language: str = "中文",
        model_name: str = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """翻译内容"""
        try:
            model_name = model_name or settings.DEFAULT_LLM_MODEL
            llm = self.llm_models.get(model_name)
            
            if not llm:
                return False, None, {"error": f"模型 '{model_name}' 不可用"}
            
            prompt = f"""请将以下内容翻译成{target_language}，保持原文的格式和结构：

{content}

翻译："""
            
            messages = [
                SystemMessage(content="你是一个专业的翻译专家，能够准确翻译各种语言的内容。"),
                HumanMessage(content=prompt)
            ]
            
            response = await llm.ainvoke(messages)
            translation = response.content
            
            metadata = {
                "target_language": target_language,
                "model_used": model_name,
                "original_length": len(content),
                "translation_length": len(translation),
                "generated_at": datetime.now().isoformat()
            }
            
            return True, translation, metadata
            
        except Exception as e:
            return False, None, {"error": f"翻译失败: {str(e)}"}
    
    def _parse_analysis_result(self, result: str, analysis_type: str) -> Dict[str, Any]:
        """解析分析结果"""
        parsed = {
            "raw_result": result,
            "analysis_type": analysis_type,
            "summary": "",
            "details": {}
        }
        
        # 简单的解析逻辑
        lines = result.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检测标题
            if line.endswith('：') or line.endswith(':'):
                current_section = line[:-1]
                parsed["details"][current_section] = []
            elif current_section:
                parsed["details"][current_section].append(line)
            else:
                parsed["summary"] += line + " "
        
        return parsed
    
    def _parse_questions(self, questions_text: str) -> List[str]:
        """解析问题列表"""
        questions = []
        
        lines = questions_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and ('?' in line or '？' in line or line.startswith(('1.', '2.', '3.', '4.', '5.'))):
                # 清理问题格式
                question = line
                if question.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
                    question = question[2:].strip()
                
                if question:
                    questions.append(question)
        
        return questions
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.llm_models.keys())
    
    def is_model_available(self, model_name: str) -> bool:
        """检查模型是否可用"""
        return model_name in self.llm_models
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        if model_name not in self.llm_models:
            return None
        
        model = self.llm_models[model_name]
        
        return {
            "name": model_name,
            "type": "openai",
            "max_tokens": getattr(model, 'max_tokens', 2000),
            "temperature": getattr(model, 'temperature', 0.7),
            "available": True
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "langchain_available": LANGCHAIN_AVAILABLE,
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "available_models": len(self.llm_models),
            "models": list(self.llm_models.keys()),
            "default_model": settings.DEFAULT_LLM_MODEL
        }


# 全局LLM服务实例
llm_service = LLMService()
