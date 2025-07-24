"""
等级相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Level(Base):
    """学习等级模型"""
    __tablename__ = "levels"

    id = Column(Integer, primary_key=True, index=True, comment="等级ID")
    name = Column(String(100), nullable=False, comment="等级名称")
    description = Column(Text, comment="等级描述")
    difficulty = Column(Integer, default=1, comment="难度等级(1-10)")
    required_score = Column(Integer, default=0, comment="所需积分")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联关系
    courses = relationship("Course", back_populates="level")

    def __repr__(self):
        return f"<Level(id={self.id}, name='{self.name}', difficulty={self.difficulty})>"
