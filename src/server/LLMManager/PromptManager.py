"""提示模板管理器"""
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from config import settings


class PromptManager:
    """提示模板管理器"""
    
    def __init__(self):
        self.templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """加载默认模板"""
        self.templates = {
            "default": {
                "name": "默认模板",
                "description": "基础的研究总结模板",
                "template": """请分析以下文件内容并生成研究总结：

文件内容：
{content}

请按照以下要求生成总结：
1. 提取关键信息
2. 总结主要观点
3. 识别重要结论
4. 提供研究建议

总结：""",
                "variables": ["content"],
                "category": "research"
            },
            "academic_paper": {
                "name": "学术论文模板",
                "description": "专门用于分析学术论文的模板",
                "template": """请分析以下学术论文内容：

论文内容：
{content}

请按照学术标准生成分析报告：
1. 研究背景和目的
2. 研究方法
3. 主要发现
4. 结论和意义
5. 局限性和建议

分析报告：""",
                "variables": ["content"],
                "category": "academic"
            },
            "meeting_notes": {
                "name": "会议记录模板",
                "description": "用于整理会议记录的模板",
                "template": """请整理以下会议记录：

会议内容：
{content}

请生成结构化的会议总结：
1. 会议主题
2. 参与人员
3. 讨论要点
4. 决策事项
5. 后续行动

会议总结：""",
                "variables": ["content"],
                "category": "meeting"
            },
            "data_analysis": {
                "name": "数据分析模板",
                "description": "用于分析数据报告的模板",
                "template": """请分析以下数据内容：

数据内容：
{content}

请生成数据分析报告：
1. 数据概览
2. 关键指标
3. 趋势分析
4. 异常发现
5. 建议措施

分析报告：""",
                "variables": ["content"],
                "category": "data"
            },
            "literature_review": {
                "name": "文献综述模板",
                "description": "用于文献综述的模板",
                "template": """请对以下文献进行综述分析：

文献内容：
{content}

请生成文献综述：
1. 研究领域概述
2. 主要理论观点
3. 研究方法比较
4. 研究空白
5. 未来研究方向

文献综述：""",
                "variables": ["content"],
                "category": "literature"
            }
        }
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有模板"""
        return list(self.templates.values())
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类获取模板"""
        return [template for template in self.templates.values() 
                if template.get("category") == category]
    
    def add_template(
        self, 
        name: str, 
        description: str, 
        template: str, 
        category: str = "custom"
    ) -> Tuple[bool, Optional[str]]:
        """添加模板"""
        try:
            # 验证模板
            is_valid, error_msg = self._validate_template(template)
            if not is_valid:
                return False, error_msg
            
            # 提取变量
            variables = self._extract_variables(template)
            
            # 检查名称是否已存在
            if name in self.templates:
                return False, f"模板 '{name}' 已存在"
            
            # 添加模板
            self.templates[name] = {
                "name": name,
                "description": description,
                "template": template,
                "variables": variables,
                "category": category
            }
            
            return True, "模板添加成功"
            
        except Exception as e:
            return False, f"添加模板失败: {str(e)}"
    
    def update_template(
        self, 
        name: str, 
        description: str = None, 
        template: str = None, 
        category: str = None
    ) -> Tuple[bool, Optional[str]]:
        """更新模板"""
        try:
            if name not in self.templates:
                return False, f"模板 '{name}' 不存在"
            
            # 更新字段
            if description is not None:
                self.templates[name]["description"] = description
            
            if template is not None:
                # 验证模板
                is_valid, error_msg = self._validate_template(template)
                if not is_valid:
                    return False, error_msg
                
                # 更新模板和变量
                self.templates[name]["template"] = template
                self.templates[name]["variables"] = self._extract_variables(template)
            
            if category is not None:
                self.templates[name]["category"] = category
            
            return True, "模板更新成功"
            
        except Exception as e:
            return False, f"更新模板失败: {str(e)}"
    
    def delete_template(self, name: str) -> Tuple[bool, Optional[str]]:
        """删除模板"""
        try:
            if name not in self.templates:
                return False, f"模板 '{name}' 不存在"
            
            # 不允许删除默认模板
            if name in ["default", "academic_paper", "meeting_notes", "data_analysis", "literature_review"]:
                return False, "不能删除默认模板"
            
            del self.templates[name]
            return True, "模板删除成功"
            
        except Exception as e:
            return False, f"删除模板失败: {str(e)}"
    
    def format_template(self, template_name: str, **kwargs) -> Tuple[bool, Optional[str]]:
        """格式化模板"""
        try:
            template = self.get_template(template_name)
            if not template:
                return False, f"模板 '{template_name}' 不存在"
            
            template_content = template["template"]
            required_variables = template["variables"]
            
            # 检查必需变量
            missing_variables = []
            for var in required_variables:
                if var not in kwargs:
                    missing_variables.append(var)
            
            if missing_variables:
                return False, f"缺少必需变量: {', '.join(missing_variables)}"
            
            # 格式化模板
            formatted_content = template_content.format(**kwargs)
            
            return True, formatted_content
            
        except KeyError as e:
            return False, f"模板变量错误: {str(e)}"
        except Exception as e:
            return False, f"格式化模板失败: {str(e)}"
    
    def get_template_variables(self, template_name: str) -> List[str]:
        """获取模板变量"""
        template = self.get_template(template_name)
        return template["variables"] if template else []
    
    def validate_template_variables(self, template_name: str, **kwargs) -> Tuple[bool, Optional[str]]:
        """验证模板变量"""
        template = self.get_template(template_name)
        if not template:
            return False, f"模板 '{template_name}' 不存在"
        
        required_variables = template["variables"]
        missing_variables = []
        
        for var in required_variables:
            if var not in kwargs:
                missing_variables.append(var)
        
        if missing_variables:
            return False, f"缺少必需变量: {', '.join(missing_variables)}"
        
        return True, None
    
    def _validate_template(self, template: str) -> Tuple[bool, Optional[str]]:
        """验证模板格式"""
        try:
            # 检查模板是否为空
            if not template.strip():
                return False, "模板内容不能为空"
            
            # 检查变量格式
            variables = self._extract_variables(template)
            for var in variables:
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                    return False, f"变量名格式错误: {var}"
            
            # 尝试格式化（使用空值）
            test_values = {var: f"{{{var}}}" for var in variables}
            template.format(**test_values)
            
            return True, None
            
        except Exception as e:
            return False, f"模板格式错误: {str(e)}"
    
    def _extract_variables(self, template: str) -> List[str]:
        """提取模板变量"""
        # 使用正则表达式提取 {variable} 格式的变量
        pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}'
        variables = re.findall(pattern, template)
        
        # 去重并保持顺序
        unique_variables = []
        for var in variables:
            if var not in unique_variables:
                unique_variables.append(var)
        
        return unique_variables
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        total_templates = len(self.templates)
        
        categories = {}
        for template in self.templates.values():
            category = template.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_templates": total_templates,
            "categories": categories,
            "default_templates": len([t for t in self.templates.values() 
                                   if t.get("category") in ["research", "academic", "meeting", "data", "literature"]]),
            "custom_templates": len([t for t in self.templates.values() 
                                   if t.get("category") == "custom"])
        }
    
    def export_templates(self) -> Dict[str, Any]:
        """导出所有模板"""
        return {
            "templates": self.templates,
            "statistics": self.get_template_statistics(),
            "export_time": datetime.now().isoformat()
        }
    
    def import_templates(self, templates_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """导入模板"""
        try:
            if "templates" not in templates_data:
                return False, "导入数据格式错误"
            
            imported_count = 0
            for name, template_info in templates_data["templates"].items():
                try:
                    # 验证模板
                    template = template_info.get("template", "")
                    is_valid, error_msg = self._validate_template(template)
                    
                    if is_valid:
                        # 添加或更新模板
                        self.templates[name] = {
                            "name": name,
                            "description": template_info.get("description", ""),
                            "template": template,
                            "variables": self._extract_variables(template),
                            "category": template_info.get("category", "imported")
                        }
                        imported_count += 1
                    else:
                        print(f"跳过无效模板 {name}: {error_msg}")
                        
                except Exception as e:
                    print(f"导入模板 {name} 失败: {e}")
                    continue
            
            return True, f"成功导入 {imported_count} 个模板"
            
        except Exception as e:
            return False, f"导入模板失败: {str(e)}"


# 全局提示模板管理器实例
prompt_manager = PromptManager()
