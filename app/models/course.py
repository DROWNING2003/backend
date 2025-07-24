"""
课程数据模型
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime

from app.database.connection import Base


class Course(Base):
    """课程模型"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, comment="课程标题")
    description = Column(Text, nullable=True, comment="课程描述")
    github_url = Column(String(500), nullable=True, comment="GitHub仓库URL")
    difficulty = Column(Integer, default=1, comment="课程难度(1-10)")
    estimated_time = Column(Integer, nullable=True, comment="预估学习时间(分钟)")
    is_published = Column(Boolean, default=False, comment="是否发布")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关联关系已移除（Level模型已废弃）

    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', difficulty={self.difficulty})>"



