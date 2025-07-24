"""
GitHub仓库相关Pydantic Schema
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime


class RepositoryBase(BaseModel):
    """仓库基础Schema"""
    name: str = Field(..., min_length=1, max_length=200, description="仓库名称")
    url: str = Field(..., description="仓库URL")
    description: Optional[str] = Field(None, description="仓库描述")
    branch: str = Field("main", description="分支名称")


class RepositoryCreate(RepositoryBase):
    """创建仓库Schema"""
    pass


class RepositoryUpdate(BaseModel):
    """更新仓库Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="仓库名称")
    description: Optional[str] = Field(None, description="仓库描述")
    branch: Optional[str] = Field(None, description="分支名称")
    crawl_status: Optional[str] = Field(None, description="爬取状态")
    analysis_status: Optional[str] = Field(None, description="分析状态")


class RepositoryFileResponse(BaseModel):
    """仓库文件响应Schema"""
    id: int = Field(..., description="文件ID")
    file_path: str = Field(..., description="文件路径")
    file_name: str = Field(..., description="文件名")
    file_extension: Optional[str] = Field(None, description="文件扩展名")
    file_size: int = Field(..., description="文件大小")
    content: Optional[str] = Field(None, description="文件内容")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class RepositoryResponse(RepositoryBase):
    """仓库响应Schema"""
    id: int = Field(..., description="仓库ID")
    file_count: int = Field(0, description="文件数量")
    total_size: int = Field(0, description="总大小")
    latest_commit_hash: Optional[str] = Field(None, description="最新提交哈希")
    latest_commit_message: Optional[str] = Field(None, description="最新提交信息")
    latest_commit_author: Optional[str] = Field(None, description="最新提交作者")
    latest_commit_date: Optional[datetime] = Field(None, description="最新提交时间")
    crawl_status: str = Field("pending", description="爬取状态")
    analysis_status: str = Field("pending", description="分析状态")
    analysis_result: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    last_crawled_at: Optional[datetime] = Field(None, description="最后爬取时间")
    last_analyzed_at: Optional[datetime] = Field(None, description="最后分析时间")
    is_active: bool = Field(True, description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class CrawlTaskRequest(BaseModel):
    """爬取任务请求Schema"""
    repo_url: str = Field(..., description="仓库URL")
    max_file_size: Optional[int] = Field(1048576, description="最大文件大小")
    include_patterns: Optional[List[str]] = Field(None, description="包含模式")
    exclude_patterns: Optional[List[str]] = Field(None, description="排除模式")
    branch: str = Field("main", description="分支名称")


class CrawlTaskResponse(BaseModel):
    """爬取任务响应Schema"""
    id: int = Field(..., description="任务ID")
    task_id: str = Field(..., description="任务UUID")
    repository_id: int = Field(..., description="仓库ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(0, description="进度百分比")
    files_downloaded: int = Field(0, description="下载文件数")
    files_skipped: int = Field(0, description="跳过文件数")
    total_size: int = Field(0, description="总大小")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        from_attributes = True


class RepositoryAnalysisRequest(BaseModel):
    """仓库分析请求Schema"""
    repository_id: int = Field(..., description="仓库ID")
    analysis_type: str = Field("overview", description="分析类型")
    model: str = Field("moonshot-v1-8k", description="使用的模型")
    use_cache: bool = Field(True, description="是否使用缓存")


class RepositoryAnalysisResponse(BaseModel):
    """仓库分析响应Schema"""
    repository_id: int = Field(..., description="仓库ID")
    analysis_type: str = Field(..., description="分析类型")
    result: str = Field(..., description="分析结果")
    model: str = Field(..., description="使用的模型")
    timestamp: datetime = Field(..., description="分析时间")


class RepositoryListResponse(BaseModel):
    """仓库列表响应Schema"""
    repositories: List[RepositoryResponse] = Field(..., description="仓库列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")


class LLMCacheResponse(BaseModel):
    """LLM缓存响应Schema"""
    id: int = Field(..., description="缓存ID")
    cache_key: str = Field(..., description="缓存键")
    model: str = Field(..., description="使用的模型")
    hit_count: int = Field(..., description="命中次数")
    last_hit_at: datetime = Field(..., description="最后命中时间")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class CrawlStatsResponse(BaseModel):
    """爬取统计响应Schema"""
    total_repositories: int = Field(..., description="总仓库数")
    total_files: int = Field(..., description="总文件数")
    total_size: int = Field(..., description="总大小")
    active_tasks: int = Field(..., description="活跃任务数")
    completed_tasks: int = Field(..., description="完成任务数")
    failed_tasks: int = Field(..., description="失败任务数")
