"""
关卡数据模型
"""

from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.database.connection import Base


class Level(Base):
    """关卡表模型"""
    
    __tablename__ = "levels"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="关卡ID")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="所属课程ID")
    commit_id = Column(Integer, nullable=True, comment="commit_id")
    title = Column(String(255), nullable=False, comment="关卡标题")
    description = Column(Text, comment="关卡描述")
    requirements = Column(Text, nullable=False, comment="通过要求")
    order_number = Column(Integer, nullable=False, comment="关卡顺序号")
    content = Column(JSON, comment="关卡具体内容")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    course = relationship("Course", back_populates="levels")
    
    def __repr__(self):
        return f"<Level(id={self.id}, title='{self.title}', course_id={self.course_id},commit_id={self.commit_id}, order={self.order_number})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "commit_id": self.commit_id,
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements,
            "order_number": self.order_number,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def to_dict_with_course(self):
        """转换为包含课程信息的字典格式"""
        level_dict = self.to_dict()
        if self.course:
            level_dict["course"] = {
                "id": self.course.id,
                "title": self.course.title,
                "tag": self.course.tag
            }
        return level_dict
