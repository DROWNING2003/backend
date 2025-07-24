"""
等级相关Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class LevelBase(BaseModel):
    """等级基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="等级名称")
    description: Optional[str] = Field(None, description="等级描述")
    difficulty: int = Field(1, ge=1, le=10, description="难度等级(1-10)")
    required_score: int = Field(0, ge=0, description="所需积分")
    is_active: bool = Field(True, description="是否激活")


class LevelCreate(LevelBase):
    """创建等级Schema"""
    pass


class LevelUpdate(BaseModel):
    """更新等级Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="等级名称")
    description: Optional[str] = Field(None, description="等级描述")
    difficulty: Optional[int] = Field(None, ge=1, le=10, description="难度等级(1-10)")
    required_score: Optional[int] = Field(None, ge=0, description="所需积分")
    is_active: Optional[bool] = Field(None, description="是否激活")


class LevelResponse(LevelBase):
    """等级响应Schema"""
    id: int = Field(..., description="等级ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class LevelCheckRequest(BaseModel):
    """等级检查请求Schema"""
    user_score: int = Field(..., ge=0, description="用户当前积分")
    current_level_id: Optional[int] = Field(None, description="用户当前等级ID")


class LevelCheckResponse(BaseModel):
    """等级检查响应Schema"""
    can_upgrade: bool = Field(..., description="是否可以升级")
    next_level: Optional[LevelResponse] = Field(None, description="下一个等级信息")
    current_level: Optional[LevelResponse] = Field(None, description="当前等级信息")
    score_needed: int = Field(0, description="升级所需积分")
