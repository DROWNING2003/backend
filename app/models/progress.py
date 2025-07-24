"""
精简的用户学习进度数据模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.connection import Base


class UserProgress(Base):
    """精简的用户学习进度模型"""
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True, comment="用户ID")
    tutorial_id = Column(Integer, nullable=False, comment="教程ID")

    # 核心进度信息
    status = Column(String(50), default="not_started", comment="状态: not_started, in_progress, completed, paused")
    progress_percentage = Column(Float, default=0.0, comment="完成百分比 0-100")
    current_step = Column(String(255), nullable=True, comment="当前学习步骤/章节")

    # 学习统计（精简）
    total_time_spent = Column(Integer, default=0, comment="总学习时间(分钟)")
    score = Column(Float, default=0.0, comment="总分数")

    # 扩展数据（JSON格式，灵活存储）
    extra_data = Column(JSON, nullable=True, comment="扩展数据：章节进度、成就等")

    # 时间戳（精简）
    started_at = Column(DateTime, default=datetime.utcnow, comment="开始时间")
    last_accessed_at = Column(DateTime, default=datetime.utcnow, comment="最后访问时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<UserProgress(user_id='{self.user_id}', tutorial_id={self.tutorial_id}, status='{self.status}')>"

    def get_chapter_progress(self, chapter_id):
        """获取特定章节的进度"""
        if not self.extra_data or 'chapters' not in self.extra_data:
            return None
        return self.extra_data['chapters'].get(str(chapter_id))

    def update_chapter_progress(self, chapter_id, chapter_data):
        """更新章节进度"""
        if not self.extra_data:
            self.extra_data = {}
        if 'chapters' not in self.extra_data:
            self.extra_data['chapters'] = {}

        self.extra_data['chapters'][str(chapter_id)] = {
            'status': chapter_data.get('status', 'not_started'),
            'score': chapter_data.get('score', 0.0),
            'time_spent': chapter_data.get('time_spent', 0),
            'attempts': chapter_data.get('attempts', 0),
            'completed_at': chapter_data.get('completed_at'),
            'updated_at': datetime.utcnow().isoformat()
        }

        # 标记为已修改，确保SQLAlchemy检测到变化
        self.extra_data = dict(self.extra_data)


class Tutorial(Base):
    """精简的教程模型"""
    __tablename__ = "tutorials"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, comment="教程标题")
    description = Column(Text, nullable=True, comment="教程描述")
    difficulty = Column(String(50), default="beginner", comment="难度级别")
    estimated_time = Column(Integer, default=0, comment="预估学习时间(分钟)")

    # 状态（精简）
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 扩展数据（JSON格式）
    extra_data = Column(JSON, nullable=True, comment="扩展数据：章节信息、统计数据等")

    # 时间戳（精简）
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    def __repr__(self):
        return f"<Tutorial(id={self.id}, title='{self.title}')>"

    def get_chapters(self):
        """获取教程章节列表"""
        if not self.extra_data or 'chapters' not in self.extra_data:
            return []
        return self.extra_data.get('chapters', [])

    def add_chapter(self, chapter_data):
        """添加章节"""
        if not self.extra_data:
            self.extra_data = {}
        if 'chapters' not in self.extra_data:
            self.extra_data['chapters'] = []

        chapter_data['id'] = len(self.extra_data['chapters']) + 1
        chapter_data['created_at'] = datetime.utcnow().isoformat()
        self.extra_data['chapters'].append(chapter_data)

        # 标记为已修改
        self.extra_data = dict(self.extra_data)


class UserAchievement(Base):
    """精简的用户成就模型"""
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True, comment="用户ID")
    achievement_type = Column(String(100), nullable=False, comment="成就类型")
    achievement_name = Column(String(255), nullable=False, comment="成就名称")

    # 成就数据（精简）
    points = Column(Integer, default=0, comment="获得积分")

    # 关联数据（精简）
    related_id = Column(Integer, nullable=True, comment="关联ID（教程/章节等）")

    # 扩展数据
    extra_data = Column(JSON, nullable=True, comment="扩展数据：描述、图标等")

    # 时间戳
    earned_at = Column(DateTime, default=datetime.utcnow, comment="获得时间")

    def __repr__(self):
        return f"<UserAchievement(user_id='{self.user_id}', name='{self.achievement_name}')>"
