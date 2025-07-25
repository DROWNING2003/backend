"""
课程数据模型
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Course(Base):
    """课程表模型"""
    
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="课程ID")
    title = Column(String(255), nullable=False, comment="课程标题")
    tag = Column(String(100), nullable=False, comment="课程标签/范畴")
    description = Column(Text, comment="课程描述")
    git_url = Column(String(500), comment="Git仓库链接")
    image_url = Column(String(500), comment="课程图片URL")
    is_completed = Column(Boolean, default=False, nullable=False, comment="创作者是否完成课程创作")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    levels = relationship("Level", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', tag='{self.tag}')>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "tag": self.tag,
            "description": self.description,
            "git_url": self.git_url,
            "image_url": self.image_url,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_levels(self):
        """转换为包含关卡信息的字典格式"""
        course_dict = self.to_dict()
        course_dict["levels"] = [
            {
                "id": level.id,
                "title": level.title,
                "order_number": level.order_number
            }
            for level in sorted(self.levels, key=lambda x: x.order_number)
        ]
        course_dict["total_levels"] = len(self.levels)
        return course_dict
