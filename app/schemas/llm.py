"""
LLM对话相关Pydantic Schema
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息Schema"""
    role: str = Field(..., description="消息角色(user/assistant/system)")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(None, description="消息时间戳")


class ChatRequest(BaseModel):
    """聊天请求Schema"""
    message: str = Field(..., min_length=1, description="用户消息")
    conversation_id: Optional[str] = Field(None, description="对话ID")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    model: Optional[str] = Field("gpt-3.5-turbo", description="使用的模型")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="最大token数")


class ChatResponse(BaseModel):
    """聊天响应Schema"""
    message: str = Field(..., description="AI回复消息")
    conversation_id: str = Field(..., description="对话ID")
    model: str = Field(..., description="使用的模型")
    usage: Optional[Dict[str, int]] = Field(None, description="token使用情况")
    timestamp: datetime = Field(..., description="响应时间戳")


class ConversationHistory(BaseModel):
    """对话历史Schema"""
    conversation_id: str = Field(..., description="对话ID")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
