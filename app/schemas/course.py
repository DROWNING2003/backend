"""
课程相关Pydantic Schema
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from app.schemas.level import LevelResponse


class CourseBase(BaseModel):
    """课程基础Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="课程标题")
    description: Optional[str] = Field(None, description="课程描述")
    github_url: Optional[str] = Field(None, description="GitHub仓库URL")
    level_id: Optional[int] = Field(None, description="所属等级ID")
    difficulty: int = Field(1, ge=1, le=10, description="课程难度(1-10)")
    estimated_time: Optional[int] = Field(None, ge=0, description="预估学习时间(分钟)")
    is_published: bool = Field(False, description="是否发布")


class CourseCreate(CourseBase):
    """创建课程Schema"""
    pass


class CourseUpdate(BaseModel):
    """更新课程Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="课程标题")
    description: Optional[str] = Field(None, description="课程描述")
    github_url: Optional[str] = Field(None, description="GitHub仓库URL")
    level_id: Optional[int] = Field(None, description="所属等级ID")
    difficulty: Optional[int] = Field(None, ge=1, le=10, description="课程难度(1-10)")
    estimated_time: Optional[int] = Field(None, ge=0, description="预估学习时间(分钟)")
    is_published: Optional[bool] = Field(None, description="是否发布")


class CourseResponse(CourseBase):
    """课程响应Schema"""
    id: int = Field(..., description="课程ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    level: Optional[LevelResponse] = Field(None, description="所属等级信息")

    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """课程列表响应Schema"""
    courses: List[CourseResponse] = Field(..., description="课程列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
