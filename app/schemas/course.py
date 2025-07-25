"""
课程相关的数据验证模式
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime


class LevelSummary(BaseModel):
    """关卡摘要信息"""
    id: int = Field(..., description="关卡ID")
    title: str = Field(..., description="关卡标题")
    order_number: int = Field(..., description="关卡顺序号")


class CourseCreate(BaseModel):
    """创建课程的请求模式"""
    title: str = Field(..., min_length=1, max_length=255, description="课程标题")
    tag: str = Field(..., min_length=1, max_length=100, description="课程标签/范畴")
    description: Optional[str] = Field(None, description="课程描述")
    git_url: str = Field(..., description="Git仓库URL")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Python基础编程",
                "tag": "编程语言",
                "description": "学习Python编程的基础知识和核心概念",
                "git_url": "https://github.com/example/python-basics"
            }
        }
    }


class CourseResponse(BaseModel):
    """课程响应模式"""
    id: int = Field(..., description="课程ID")
    title: Optional[str] = Field(None, description="课程标题")
    tag: Optional[str] = Field(None, description="课程标签/范畴")
    description: Optional[str] = Field(None, description="课程描述")
    git_url: str = Field(..., description="Git仓库URL")
    image_url: Optional[str] = Field(None, description="课程图片URL")
    is_completed: bool = Field(default=False, description="创作者是否完成课程创作")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    levels: List[LevelSummary] = Field(default=[], description="关卡列表")
    total_levels: Optional[int] = Field(None, description="总关卡数")
    message: Optional[str] = Field(None, description="状态消息")
    generation_status: Optional[str] = Field(None, description="关卡生成状态")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "Python基础编程",
                "tag": "编程语言",
                "description": "学习Python编程的基础知识和核心概念",
                "git_url": "https://github.com/example/python-basics",
                "image_url": "https://example.com/images/python-course.jpg",
                "is_completed": False,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "levels": [
                    {"id": 1, "title": "变量和数据类型", "order_number": 1},
                    {"id": 2, "title": "控制流程", "order_number": 2}
                ],
                "total_levels": 2
            }
        }
    }


class CourseGenerationStatusResponse(BaseModel):
    """课程关卡生成状态响应模式"""
    course_id: int = Field(..., description="课程ID")
    status: str = Field(..., description="生成状态: generating, completed, failed")
    message: str = Field(..., description="状态描述信息")
    level_count: int = Field(..., description="已生成的关卡数量")
    is_completed: bool = Field(..., description="是否完成生成")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "course_id": 1,
                "status": "generating",
                "message": "关卡生成中，已生成 3 个关卡",
                "level_count": 3,
                "is_completed": False
            }
        }
    }


class CourseListResponse(BaseModel):
    """课程列表响应模式"""
    courses: List[CourseResponse] = Field(..., description="课程列表")
    total: int = Field(..., description="课程总数")

    model_config = {
        "json_schema_extra": {
            "example": {
                "courses": [
                    {
                        "id": 1,
                        "title": "Python基础编程",
                        "tag": "编程语言",
                        "description": "学习Python编程的基础知识",
                        "image_url": "https://example.com/images/python.jpg",
                        "is_completed": False,
                        "levels": [
                            {"id": 1, "title": "变量和数据类型", "order_number": 1}
                        ],
                        "total_levels": 1
                    }
                ],
                "total": 1
            }
        }
    }
