"""
AI相关业务逻辑服务
"""

import logging
from typing import Optional, Dict, Any, List
import random

from app.schemas.level import LevelCheckResponse, GeneratedLevelsResponse, GeneratedLevel

logger = logging.getLogger(__name__)


class AIService:
    """AI服务类，提供智能处理功能"""

    def __init__(self):
        self.is_initialized = True
        logger.info("AI服务初始化完成（模拟模式）")
    
    def generate_levels_from_git(self, git_url: str, project_name: Optional[str] = None,
                                max_levels: int = 10) -> GeneratedLevelsResponse:
        """
        基于Git仓库生成关卡（模拟实现）

        Args:
            git_url: Git仓库URL
            project_name: 项目名称
            max_levels: 最大关卡数量

        Returns:
            GeneratedLevelsResponse: 生成的关卡数据
        """
        try:
            logger.info(f"开始为Git仓库生成关卡: {git_url}")

            # 模拟生成关卡数据
            generated_levels = []

            # 预定义的关卡模板
            level_templates = [
                {
                    "name": "项目环境搭建",
                    "description": "学习如何搭建项目开发环境，包括依赖安装和配置",
                    "requirements": "成功搭建项目环境并运行基本示例"
                },
                {
                    "name": "代码结构分析",
                    "description": "理解项目的代码结构和架构设计",
                    "requirements": "分析并描述项目的主要模块和功能"
                },
                {
                    "name": "核心功能实现",
                    "description": "学习项目的核心功能实现原理",
                    "requirements": "实现一个简化版本的核心功能"
                },
                {
                    "name": "单元测试编写",
                    "description": "为项目功能编写单元测试",
                    "requirements": "编写至少3个有效的单元测试用例"
                },
                {
                    "name": "代码优化改进",
                    "description": "分析代码并提出优化建议",
                    "requirements": "提交代码优化方案并实现改进"
                }
            ]

            # 根据max_levels生成关卡
            for i in range(min(max_levels, len(level_templates))):
                template = level_templates[i]
                generated_level = GeneratedLevel(
                    name=template["name"],
                    description=template["description"],
                    requirements=template["requirements"],
                    order_number=i + 1
                )
                generated_levels.append(generated_level)

            logger.info(f"成功生成 {len(generated_levels)} 个关卡")

            return GeneratedLevelsResponse(
                success=True,
                levels=generated_levels,
                message=f"成功生成 {len(generated_levels)} 个关卡",
                total_levels=len(generated_levels)
            )

        except Exception as e:
            logger.error(f"生成关卡异常: {e}")
            return GeneratedLevelsResponse(
                success=False,
                levels=[],
                message=f"生成关卡异常: {str(e)}",
                total_levels=0
            )
    
    def check_user_answer(self, level_title: str, level_description: Optional[str],
                         requirements: str, user_answer: str,
                         level_content: Optional[Dict[str, Any]] = None) -> LevelCheckResponse:
        """
        检查用户答案（智能评估）

        Args:
            level_title: 关卡标题
            level_description: 关卡描述
            requirements: 通过要求
            user_answer: 用户答案
            level_content: 关卡内容

        Returns:
            LevelCheckResponse: 检查结果
        """
        try:
            logger.info(f"开始检查关卡答案: {level_title}")

            # 使用智能规则检查
            return self._intelligent_answer_check(
                level_title, level_description, requirements, user_answer, level_content
            )

        except Exception as e:
            logger.error(f"检查用户答案异常: {e}")
            # 返回基本的检查结果
            return self._simple_answer_check(user_answer, requirements)

    def _intelligent_answer_check(self, level_title: str, level_description: Optional[str],
                                 requirements: str, user_answer: str,
                                 level_content: Optional[Dict[str, Any]] = None) -> LevelCheckResponse:
        """
        智能答案检查

        Args:
            level_title: 关卡标题
            level_description: 关卡描述
            requirements: 要求
            user_answer: 用户答案
            level_content: 关卡内容

        Returns:
            LevelCheckResponse: 检查结果
        """
        try:
            # 基本检查：答案不能为空
            if not user_answer.strip():
                return LevelCheckResponse(
                    passed=False,
                    feedback="答案不能为空，请提交您的代码或解答。",
                    score=0,
                    suggestions=["请仔细阅读关卡要求", "提交完整的代码或解答"]
                )

            # 长度检查
            answer_length = len(user_answer.strip())
            if answer_length < 20:
                return LevelCheckResponse(
                    passed=False,
                    feedback="答案过于简短，请提供更详细的解答。",
                    score=30,
                    suggestions=["增加代码注释", "提供更完整的实现", "解释你的思路"]
                )

            # 关键词检查（基于关卡标题和要求）
            score = 60  # 基础分数
            feedback_parts = []
            suggestions = []

            # 检查是否包含相关关键词
            keywords = self._extract_keywords(level_title, requirements)
            found_keywords = 0
            for keyword in keywords:
                if keyword.lower() in user_answer.lower():
                    found_keywords += 1
                    score += 10

            if found_keywords > 0:
                feedback_parts.append(f"很好！你的答案涉及了 {found_keywords} 个相关概念。")
            else:
                feedback_parts.append("建议在答案中包含更多相关的技术概念。")
                suggestions.append("仔细阅读关卡要求，确保答案切题")

            # 代码结构检查
            if any(keyword in user_answer for keyword in ['def ', 'class ', 'import ', 'from ']):
                score += 15
                feedback_parts.append("代码结构良好！")
            else:
                suggestions.append("考虑使用更规范的代码结构")

            # 注释检查
            if '#' in user_answer or '"""' in user_answer or "'''" in user_answer:
                score += 10
                feedback_parts.append("很好的代码注释习惯！")
            else:
                suggestions.append("添加适当的代码注释")

            # 确定是否通过
            passed = score >= 70

            # 生成反馈
            if passed:
                feedback_parts.insert(0, "恭喜！你的答案通过了检查。")
            else:
                feedback_parts.insert(0, "答案需要改进，请参考建议进行修改。")

            feedback = " ".join(feedback_parts)

            return LevelCheckResponse(
                passed=passed,
                feedback=feedback,
                score=min(score, 100),
                suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"智能答案检查异常: {e}")
            return self._simple_answer_check(user_answer, requirements)

    def _extract_keywords(self, level_title: str, requirements: str) -> List[str]:
        """
        从关卡标题和要求中提取关键词

        Args:
            level_title: 关卡标题
            requirements: 要求

        Returns:
            List[str]: 关键词列表
        """
        # 预定义的技术关键词
        tech_keywords = [
            'python', 'java', 'javascript', 'html', 'css', 'sql',
            'function', 'class', 'variable', 'loop', 'condition',
            'array', 'list', 'dict', 'string', 'int', 'float',
            'import', 'module', 'package', 'library',
            'test', 'debug', 'error', 'exception'
        ]

        # 从标题和要求中提取词汇
        text = (level_title + " " + requirements).lower()
        found_keywords = []

        for keyword in tech_keywords:
            if keyword in text:
                found_keywords.append(keyword)

        return found_keywords

    def _simple_answer_check(self, user_answer: str, requirements: str) -> LevelCheckResponse:
        """
        简单的答案检查（备用方案）
        
        Args:
            user_answer: 用户答案
            requirements: 要求
            
        Returns:
            LevelCheckResponse: 检查结果
        """
        try:
            # 基本检查：答案不能为空
            if not user_answer.strip():
                return LevelCheckResponse(
                    passed=False,
                    feedback="答案不能为空，请提交您的代码或解答。",
                    score=0,
                    suggestions=["请仔细阅读关卡要求", "提交完整的代码或解答"]
                )
            
            # 基本检查：答案长度
            if len(user_answer.strip()) < 10:
                return LevelCheckResponse(
                    passed=False,
                    feedback="答案过于简短，请提供更详细的解答。",
                    score=30,
                    suggestions=["增加代码注释", "提供更完整的实现"]
                )
            
            # 基本通过
            return LevelCheckResponse(
                passed=True,
                feedback="基本检查通过！建议使用AI进行更详细的代码审查。",
                score=75,
                suggestions=["考虑优化代码结构", "添加错误处理"]
            )
            
        except Exception as e:
            logger.error(f"简单答案检查异常: {e}")
            return LevelCheckResponse(
                passed=False,
                feedback="检查过程中出现错误，请重试。",
                score=0,
                suggestions=["检查代码语法", "确保代码完整"]
            )
    
    async def get_generated_levels_status(self) -> Dict[str, Any]:
        """
        获取AI生成关卡的状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        try:
            return {
                "status": "ready",
                "mode": "simulation",
                "available_services": ["level_generation", "code_review", "intelligent_feedback"],
                "features": [
                    "基于Git仓库生成关卡",
                    "智能代码审查",
                    "自适应评分系统"
                ]
            }
        except Exception as e:
            logger.error(f"获取AI服务状态失败: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
