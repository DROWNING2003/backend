"""
课程相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Course(Base):
    """课程模型"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, comment="课程ID")
    title = Column(String(200), nullable=False, comment="课程标题")
    description = Column(Text, comment="课程描述")
    github_url = Column(String(500), comment="GitHub仓库URL")
    level_id = Column(Integer, ForeignKey("levels.id"), comment="所属等级ID")
    difficulty = Column(Integer, default=1, comment="课程难度(1-10)")
    estimated_time = Column(Integer, comment="预估学习时间(分钟)")
    is_published = Column(Boolean, default=False, comment="是否发布")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联关系
    level = relationship("Level", back_populates="courses")

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', level_id={self.level_id})>"



