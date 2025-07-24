"""
GitHub仓库相关数据模型
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class Repository(Base):
    """GitHub仓库模型"""
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True, comment="仓库ID")
    name = Column(String(200), nullable=False, comment="仓库名称")
    url = Column(String(500), nullable=False, unique=True, comment="仓库URL")
    description = Column(Text, comment="仓库描述")
    branch = Column(String(100), default="main", comment="分支名称")
    
    # 仓库统计信息
    file_count = Column(Integer, default=0, comment="文件数量")
    total_size = Column(Integer, default=0, comment="总大小(字节)")
    
    # 仓库元信息
    latest_commit_hash = Column(String(40), comment="最新提交哈希")
    latest_commit_message = Column(Text, comment="最新提交信息")
    latest_commit_author = Column(String(200), comment="最新提交作者")
    latest_commit_date = Column(DateTime(timezone=True), comment="最新提交时间")
    
    # 爬取状态
    crawl_status = Column(String(50), default="pending", comment="爬取状态")
    crawl_error = Column(Text, comment="爬取错误信息")
    last_crawled_at = Column(DateTime(timezone=True), comment="最后爬取时间")
    
    # 分析状态
    analysis_status = Column(String(50), default="pending", comment="分析状态")
    analysis_result = Column(JSON, comment="分析结果")
    last_analyzed_at = Column(DateTime(timezone=True), comment="最后分析时间")
    
    # 系统字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联关系
    files = relationship("RepositoryFile", back_populates="repository", cascade="all, delete-orphan")
    crawl_tasks = relationship("CrawlTask", back_populates="repository")

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.name}', url='{self.url}')>"


class RepositoryFile(Base):
    """仓库文件模型"""
    __tablename__ = "repository_files"

    id = Column(Integer, primary_key=True, index=True, comment="文件ID")
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, comment="仓库ID")
    file_path = Column(String(1000), nullable=False, comment="文件路径")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_extension = Column(String(50), comment="文件扩展名")
    file_size = Column(Integer, default=0, comment="文件大小(字节)")
    content = Column(Text, comment="文件内容")
    content_hash = Column(String(64), comment="内容哈希")
    
    # 系统字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    # 关联关系
    repository = relationship("Repository", back_populates="files")

    def __repr__(self):
        return f"<RepositoryFile(id={self.id}, path='{self.file_path}')>"


class CrawlTask(Base):
    """爬取任务模型"""
    __tablename__ = "crawl_tasks"

    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    task_id = Column(String(36), unique=True, nullable=False, comment="任务UUID")
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, comment="仓库ID")
    
    # 任务配置
    max_file_size = Column(Integer, default=1048576, comment="最大文件大小")
    include_patterns = Column(JSON, comment="包含模式")
    exclude_patterns = Column(JSON, comment="排除模式")
    branch = Column(String(100), default="main", comment="分支名称")
    
    # 任务状态
    status = Column(String(50), default="pending", comment="任务状态")
    progress = Column(Integer, default=0, comment="进度百分比")
    error_message = Column(Text, comment="错误信息")
    
    # 任务结果
    files_downloaded = Column(Integer, default=0, comment="下载文件数")
    files_skipped = Column(Integer, default=0, comment="跳过文件数")
    total_size = Column(Integer, default=0, comment="总大小")
    
    # 系统字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    completed_at = Column(DateTime(timezone=True), comment="完成时间")

    # 关联关系
    repository = relationship("Repository", back_populates="crawl_tasks")

    def __repr__(self):
        return f"<CrawlTask(id={self.id}, task_id='{self.task_id}', status='{self.status}')>"


class LLMCache(Base):
    """LLM缓存模型"""
    __tablename__ = "llm_cache"

    id = Column(Integer, primary_key=True, index=True, comment="缓存ID")
    cache_key = Column(String(64), unique=True, nullable=False, comment="缓存键(MD5)")
    prompt = Column(Text, nullable=False, comment="输入提示")
    model = Column(String(100), nullable=False, comment="使用的模型")
    response = Column(Text, nullable=False, comment="LLM响应")
    
    # 统计信息
    hit_count = Column(Integer, default=1, comment="命中次数")
    last_hit_at = Column(DateTime(timezone=True), server_default=func.now(), comment="最后命中时间")
    
    # 系统字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<LLMCache(id={self.id}, model='{self.model}', hit_count={self.hit_count})>"
