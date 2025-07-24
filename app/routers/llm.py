"""
LLM对话相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
import uuid
from datetime import datetime
import os

from app.schemas.llm import ChatRequest, ChatResponse, ConversationHistory
from app.utils.llm_client import LLMClient

logger = logging.getLogger(__name__)
router = APIRouter()

# 初始化LLM客户端
llm_client = LLMClient()

# 内存中存储对话历史（生产环境应使用数据库）
conversation_store: Dict[str, Dict[str, Any]] = {}


@router.post("/llm/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    """
    与LLM进行对话
    """
    try:
        # 生成或使用现有的对话ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # 获取对话历史
        conversation = conversation_store.get(conversation_id, {
            "messages": [],
            "created_at": datetime.now()
        })
        
        # 添加用户消息到历史
        user_message = {
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now()
        }
        conversation["messages"].append(user_message)
        
        # 准备发送给LLM的消息
        messages_for_llm = [
            {"role": msg["role"], "content": msg["content"]} 
            for msg in conversation["messages"][-10:]  # 只保留最近10条消息
        ]
        
        # 添加系统提示
        system_prompt = """你是一个专业的GitHub仓库学习助手，帮助用户理解和学习代码。
请用中文回答，保持友好和专业的语气。如果用户询问代码相关问题，请提供清晰的解释和示例。"""
        
        messages_for_llm.insert(0, {"role": "system", "content": system_prompt})
        
        # 调用LLM
        llm_response = await llm_client.chat_completion(
            messages=messages_for_llm,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        # 添加AI回复到历史
        ai_message = {
            "role": "assistant",
            "content": llm_response["message"],
            "timestamp": datetime.now()
        }
        conversation["messages"].append(ai_message)
        conversation["updated_at"] = datetime.now()
        
        # 保存对话历史
        conversation_store[conversation_id] = conversation
        
        response = ChatResponse(
            message=llm_response["message"],
            conversation_id=conversation_id,
            model=request.model,
            usage=llm_response.get("usage"),
            timestamp=datetime.now()
        )
        
        logger.info(f"LLM对话成功，对话ID: {conversation_id}")
        return response
    
    except Exception as e:
        logger.error(f"LLM对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LLM对话失败: {str(e)}")


@router.post("/llm/conversations/history", response_model=ConversationHistory)
async def get_conversation_history(request: Dict[str, Any]):
    """
    获取对话历史
    """
    try:
        conversation_id = request.get("conversation_id")
        if not conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id参数必需")

        conversation = conversation_store.get(conversation_id)
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        response = ConversationHistory(
            conversation_id=conversation_id,
            messages=conversation["messages"],
            created_at=conversation["created_at"],
            updated_at=conversation.get("updated_at", conversation["created_at"])
        )
        
        logger.info(f"成功获取对话历史: {conversation_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取对话历史失败")


@router.post("/llm/conversations/delete")
async def delete_conversation(request: Dict[str, Any]):
    """
    删除对话历史
    """
    try:
        conversation_id = request.get("conversation_id")
        if not conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id参数必需")

        if conversation_id not in conversation_store:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        del conversation_store[conversation_id]
        
        logger.info(f"成功删除对话: {conversation_id}")
        return {"message": "对话已删除", "conversation_id": conversation_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除对话失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除对话失败")


@router.post("/llm/status")
async def get_llm_status(request: Dict[str, Any] = {}):
    """
    获取LLM服务状态
    """
    try:
        status = await llm_client.check_status()
        return {
            "status": "healthy" if status else "unhealthy",
            "available_models": llm_client.get_available_models(),
            "active_conversations": len(conversation_store)
        }
    
    except Exception as e:
        logger.error(f"获取LLM状态失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "active_conversations": len(conversation_store)
        }
