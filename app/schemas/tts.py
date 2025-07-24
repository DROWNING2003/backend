"""
文本转语音相关Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TTSRequest(BaseModel):
    """TTS请求Schema"""
    text: str = Field(..., min_length=1, max_length=5000, description="要转换的文本")
    voice: Optional[str] = Field("zh-CN-XiaoxiaoNeural", description="语音类型")
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0, description="语速(0.5-2.0)")
    pitch: Optional[float] = Field(1.0, ge=0.5, le=2.0, description="音调(0.5-2.0)")
    volume: Optional[float] = Field(1.0, ge=0.1, le=1.0, description="音量(0.1-1.0)")
    format: Optional[str] = Field("mp3", description="音频格式(mp3/wav)")


class TTSResponse(BaseModel):
    """TTS响应Schema"""
    audio_url: str = Field(..., description="音频文件URL")
    duration: Optional[float] = Field(None, description="音频时长(秒)")
    file_size: Optional[int] = Field(None, description="文件大小(字节)")
    format: str = Field(..., description="音频格式")
    created_at: datetime = Field(..., description="创建时间")


class TTSStatus(BaseModel):
    """TTS状态Schema"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态(pending/processing/completed/failed)")
    progress: Optional[int] = Field(None, ge=0, le=100, description="处理进度(0-100)")
    result: Optional[TTSResponse] = Field(None, description="处理结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
