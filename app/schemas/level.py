"""
关卡相关的数据验证模式
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict, Union
from datetime import datetime


class CourseInfo(BaseModel):
    """课程信息摘要"""
    id: int = Field(..., description="课程ID")
    title: str = Field(..., description="课程标题")
    tag: str = Field(..., description="课程标签")


class LevelGetRequest(BaseModel):
    """获取关卡详情的请求模式"""
    course_id: int = Field(..., description="课程ID")
    level_id: int = Field(..., description="关卡ID")
    update_to_latest: bool = Field(default=True, description="是否更新仓库到最新状态")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "course_id": 1,
                "level_id": 1,
                "update_to_latest": True
            }
        }
    }


class FileTreeNode(BaseModel):
    """文件树节点"""
    type: str = Field(..., description="节点类型: file 或 directory")
    uri: str = Field(..., description="文件URI")
    children: Optional[List['FileTreeNode']] = Field(None, description="子节点（仅目录有）")
    content: Optional[str] = Field(None, description="文件内容（仅文件有）")

# 解决前向引用问题
FileTreeNode.model_rebuild()

class LevelResponse(BaseModel):
    """关卡详情响应模式"""
    id: int = Field(..., description="关卡ID")
    course_id: int = Field(..., description="所属课程ID")
    title: str = Field(..., description="关卡标题")
    description: Optional[str] = Field(None, description="关卡描述")
    requirements: str = Field(..., description="通过要求")
    order_number: int = Field(..., description="关卡顺序号")
    content: Optional[Dict[str, Any]] = Field(None, description="关卡具体内容")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    course: Optional[CourseInfo] = Field(None, description="所属课程信息")
    file_tree: Optional[FileTreeNode] = Field(None, description="项目文件树结构")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "course_id": 1,
                "title": "变量和数据类型",
                "description": "学习Python中的基本数据类型和变量声明",
                "requirements": "创建不同类型的变量并进行基本操作",
                "order_number": 1,
                "content": {"examples": ["x = 10", "name = 'Python'"]},
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "course": {
                    "id": 1,
                    "title": "Python基础编程",
                    "tag": "编程语言"
                },
                "file_tree": {
                    "type": "directory",
                    "uri": "file:///project",
                    "children": [
                        {
                            "type": "file",
                            "uri": "file:///project/main.py",
                            "content": "print('Hello World')"
                        }
                    ]
                }
            }
        }
    }


class LevelCheckRequest(BaseModel):
    """检查关卡完成状态的请求模式"""
    level_id: int = Field(..., description="关卡ID")
    user_answer: str = Field(..., min_length=1, description="用户提交的答案/代码")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "level_id": 1,
                "user_answer": "x = 10\nname = 'Python'\nprint(f'数字: {x}, 字符串: {name}')"
            }
        }
    }


class LevelCheckResponse(BaseModel):
    """关卡完成检查响应模式"""
    passed: bool = Field(..., description="是否通过")
    feedback: str = Field(..., description="反馈信息")
    score: Optional[int] = Field(None, ge=0, le=100, description="得分(0-100)")
    suggestions: Optional[List[str]] = Field(None, description="改进建议")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "passed": True,
                "feedback": "很好！你成功创建了不同类型的变量并进行了输出。",
                "score": 95,
                "suggestions": ["可以尝试更多的数据类型", "考虑添加注释说明"]
            }
        }
    }


class GenerateLevelsRequest(BaseModel):
    """生成关卡的请求模式"""
    git_url: str = Field(..., description="Git仓库URL")
    project_name: Optional[str] = Field(None, description="项目名称")
    language: str = Field(default="chinese", description="输出语言")
    max_levels: int = Field(default=10, ge=1, le=20, description="最大关卡数量")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "git_url": "https://github.com/example/python-project",
                "project_name": "Python示例项目",
                "language": "chinese",
                "max_levels": 8
            }
        }
    }


class GeneratedLevel(BaseModel):
    """生成的关卡数据"""
    name: str = Field(..., description="关卡名称")
    description: str = Field(..., description="关卡描述")
    requirements: str = Field(..., description="通过要求")
    order_number: int = Field(..., description="顺序号")


class GeneratedLevelsResponse(BaseModel):
    """生成关卡的响应模式"""
    success: bool = Field(..., description="是否成功")
    levels: List[GeneratedLevel] = Field(default=[], description="生成的关卡列表")
    message: str = Field(..., description="处理消息")
    total_levels: int = Field(default=0, description="生成的关卡总数")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "levels": [
                    {
                        "name": "变量声明",
                        "description": "学习如何在Python中声明和使用变量",
                        "requirements": "创建至少3个不同类型的变量",
                        "order_number": 1
                    }
                ],
                "message": "成功生成8个关卡",
                "total_levels": 8
            }
        }
    }
