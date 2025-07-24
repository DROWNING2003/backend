"""
文本转语音相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any
import logging
import uuid
from datetime import datetime
import os

from app.schemas.tts import TTSRequest, TTSResponse, TTSStatus
from app.utils.tts_client import TTSClient

logger = logging.getLogger(__name__)
router = APIRouter()

# 初始化TTS客户端
tts_client = TTSClient()

# 内存中存储TTS任务状态（生产环境应使用数据库）
tts_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/tts/generate", response_model=TTSResponse)
async def generate_speech(
    request: TTSRequest,
    background_tasks: BackgroundTasks
):
    """
    生成语音文件（同步方式）
    """
    try:
        # 验证文本长度
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="文本长度不能超过5000字符")
        
        # 生成语音
        result = await tts_client.text_to_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            format=request.format
        )
        
        response = TTSResponse(
            audio_url=result["audio_url"],
            duration=result.get("duration"),
            file_size=result.get("file_size"),
            format=request.format,
            created_at=datetime.now()
        )
        
        logger.info(f"TTS生成成功，文件: {result['audio_url']}")
        return response
    
    except Exception as e:
        logger.error(f"TTS生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TTS生成失败: {str(e)}")


@router.post("/tts/generate-async", response_model=TTSStatus)
async def generate_speech_async(
    request: TTSRequest,
    background_tasks: BackgroundTasks
):
    """
    生成语音文件（异步方式）
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务状态
        task_status = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "result": None,
            "error_message": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        tts_tasks[task_id] = task_status
        
        # 添加后台任务
        background_tasks.add_task(
            process_tts_async,
            task_id,
            request
        )
        
        response = TTSStatus(**task_status)
        
        logger.info(f"TTS异步任务创建成功，任务ID: {task_id}")
        return response
    
    except Exception as e:
        logger.error(f"创建TTS异步任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建TTS异步任务失败")


async def process_tts_async(task_id: str, request: TTSRequest):
    """
    异步处理TTS任务
    """
    try:
        # 更新任务状态为处理中
        tts_tasks[task_id]["status"] = "processing"
        tts_tasks[task_id]["progress"] = 10
        tts_tasks[task_id]["updated_at"] = datetime.now()
        
        # 生成语音
        result = await tts_client.text_to_speech(
            text=request.text,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            format=request.format
        )
        
        # 更新任务状态为完成
        tts_response = TTSResponse(
            audio_url=result["audio_url"],
            duration=result.get("duration"),
            file_size=result.get("file_size"),
            format=request.format,
            created_at=datetime.now()
        )
        
        tts_tasks[task_id]["status"] = "completed"
        tts_tasks[task_id]["progress"] = 100
        tts_tasks[task_id]["result"] = tts_response.dict()
        tts_tasks[task_id]["updated_at"] = datetime.now()
        
        logger.info(f"TTS异步任务完成，任务ID: {task_id}")
    
    except Exception as e:
        # 更新任务状态为失败
        tts_tasks[task_id]["status"] = "failed"
        tts_tasks[task_id]["error_message"] = str(e)
        tts_tasks[task_id]["updated_at"] = datetime.now()
        
        logger.error(f"TTS异步任务失败，任务ID: {task_id}, 错误: {str(e)}")


@router.post("/tts/status", response_model=TTSStatus)
async def get_tts_status(request: Dict[str, Any]):
    """
    获取TTS任务状态
    """
    try:
        task_id = request.get("task_id")
        if not task_id:
            raise HTTPException(status_code=400, detail="task_id参数必需")

        task_status = tts_tasks.get(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        response = TTSStatus(**task_status)
        
        logger.info(f"获取TTS任务状态成功，任务ID: {task_id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取TTS任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取TTS任务状态失败")


@router.post("/tts/voices")
async def get_available_voices(request: Dict[str, Any] = {}):
    """
    获取可用的语音列表
    """
    try:
        voices = tts_client.get_available_voices()
        return {"voices": voices}
    
    except Exception as e:
        logger.error(f"获取语音列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取语音列表失败")


@router.post("/tts/health")
async def get_tts_health(request: Dict[str, Any] = {}):
    """
    获取TTS服务健康状态
    """
    try:
        status = await tts_client.check_health()
        return {
            "status": "healthy" if status else "unhealthy",
            "active_tasks": len([t for t in tts_tasks.values() if t["status"] in ["pending", "processing"]])
        }
    
    except Exception as e:
        logger.error(f"获取TTS健康状态失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "active_tasks": len([t for t in tts_tasks.values() if t["status"] in ["pending", "processing"]])
        }
