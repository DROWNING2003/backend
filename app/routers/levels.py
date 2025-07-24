"""
任务进度管理相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.database.connection import get_db
from app.models import UserProgress, Tutorial, UserAchievement

logger = logging.getLogger(__name__)
router = APIRouter()


# 请求Schema
class GetProgressRequest(BaseModel):
    """获取进度请求"""
    user_id: str = Field(..., description="用户ID")
    tutorial_id: Optional[int] = Field(None, description="教程ID，不传则获取所有")


class UpdateProgressRequest(BaseModel):
    """更新进度请求"""
    user_id: str = Field(..., description="用户ID")
    tutorial_id: int = Field(..., description="教程ID")
    chapter_id: Optional[int] = Field(None, description="章节ID")
    progress_data: Dict[str, Any] = Field(..., description="进度数据")


class CreateProgressRequest(BaseModel):
    """创建进度请求"""
    user_id: str = Field(..., description="用户ID")
    tutorial_id: int = Field(..., description="教程ID")
    initial_data: Optional[Dict[str, Any]] = Field({}, description="初始数据")


@router.post("/progress/get")
async def get_user_progress(
    request: GetProgressRequest,
    db: Session = Depends(get_db)
):
    """
    获取用户学习进度
    """
    try:
        query = db.query(UserProgress).filter(UserProgress.user_id == request.user_id)

        if request.tutorial_id:
            query = query.filter(UserProgress.tutorial_id == request.tutorial_id)

        progresses = query.all()

        result = []
        for progress in progresses:
            # 获取教程信息
            tutorial = db.query(Tutorial).filter(Tutorial.id == progress.tutorial_id).first()

            # 从extra_data中获取章节进度
            chapter_progresses = []
            if progress.extra_data and 'chapters' in progress.extra_data:
                for chapter_id, chapter_data in progress.extra_data['chapters'].items():
                    chapter_progresses.append({
                        "chapter_id": int(chapter_id),
                        "status": chapter_data.get('status', 'not_started'),
                        "score": chapter_data.get('score', 0.0),
                        "time_spent": chapter_data.get('time_spent', 0),
                        "attempts": chapter_data.get('attempts', 0),
                        "started_at": chapter_data.get('started_at'),
                        "completed_at": chapter_data.get('completed_at'),
                        "updated_at": chapter_data.get('updated_at')
                    })

            result.append({
                "id": progress.id,
                "user_id": progress.user_id,
                "tutorial_id": progress.tutorial_id,
                "tutorial_title": tutorial.title if tutorial else "未知教程",
                "status": progress.status,
                "progress_percentage": progress.progress_percentage,
                "current_step": progress.current_step,
                "total_time_spent": progress.total_time_spent,
                "score": progress.score,
                "started_at": progress.started_at,
                "last_accessed_at": progress.last_accessed_at,
                "completed_at": progress.completed_at,
                "created_at": progress.created_at,
                "updated_at": progress.updated_at,
                "chapter_progresses": chapter_progresses,
                "extra_data": progress.extra_data
            })

        return {
            "success": True,
            "user_id": request.user_id,
            "total": len(result),
            "progresses": result
        }

    except Exception as e:
        logger.error(f"获取用户进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress/create")
async def create_user_progress(
    request: CreateProgressRequest,
    db: Session = Depends(get_db)
):
    """
    创建用户学习进度
    """
    try:
        # 检查教程是否存在
        tutorial = db.query(Tutorial).filter(Tutorial.id == request.tutorial_id).first()
        if not tutorial:
            raise HTTPException(status_code=404, detail="教程不存在")

        # 检查是否已存在进度
        existing_progress = db.query(UserProgress).filter(
            UserProgress.user_id == request.user_id,
            UserProgress.tutorial_id == request.tutorial_id
        ).first()

        if existing_progress:
            return {
                "success": True,
                "message": "进度已存在",
                "progress_id": existing_progress.id,
                "status": existing_progress.status
            }

        # 创建新进度
        progress = UserProgress(
            user_id=request.user_id,
            tutorial_id=request.tutorial_id,
            status="not_started",
            progress_percentage=0.0,
            current_step=None,
            total_time_spent=0,
            score=0.0,
            extra_data={"created_from": "api", "initial_data": request.initial_data},
            started_at=datetime.utcnow()
        )

        db.add(progress)
        db.commit()
        db.refresh(progress)

        return {
            "success": True,
            "message": "进度创建成功",
            "progress_id": progress.id,
            "tutorial_title": tutorial.title
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建用户进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress/update")
async def update_user_progress(
    request: UpdateProgressRequest,
    db: Session = Depends(get_db)
):
    """
    更新用户学习进度
    """
    try:
        # 获取用户进度
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == request.user_id,
            UserProgress.tutorial_id == request.tutorial_id
        ).first()

        if not progress:
            raise HTTPException(status_code=404, detail="用户进度不存在")

        # 更新进度数据
        progress_data = request.progress_data

        if "status" in progress_data:
            progress.status = progress_data["status"]
        if "progress_percentage" in progress_data:
            progress.progress_percentage = progress_data["progress_percentage"]
        if "current_step" in progress_data:
            progress.current_step = progress_data["current_step"]
        if "total_time_spent" in progress_data:
            progress.total_time_spent = progress_data["total_time_spent"]
        if "score" in progress_data:
            progress.score = progress_data["score"]

        # 更新章节进度（如果提供）
        if request.chapter_id and "chapter_progress" in progress_data:
            chapter_data = progress_data["chapter_progress"]
            progress.update_chapter_progress(request.chapter_id, chapter_data)

        # 更新扩展数据
        if "extra_data" in progress_data:
            if not progress.extra_data:
                progress.extra_data = {}
            progress.extra_data.update(progress_data["extra_data"])
            # 标记为已修改
            progress.extra_data = dict(progress.extra_data)

        progress.last_accessed_at = datetime.utcnow()

        # 如果是完成状态，设置完成时间
        if progress.status == "completed" and not progress.completed_at:
            progress.completed_at = datetime.utcnow()

        db.commit()

        return {
            "success": True,
            "message": "进度更新成功",
            "progress_id": progress.id,
            "status": progress.status,
            "progress_percentage": progress.progress_percentage
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/progress/delete")
async def delete_user_progress(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    删除用户学习进度
    """
    try:
        user_id = request.get("user_id")
        tutorial_id = request.get("tutorial_id")

        if not user_id or not tutorial_id:
            raise HTTPException(status_code=400, detail="user_id和tutorial_id参数必需")

        # 获取用户进度
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.tutorial_id == tutorial_id
        ).first()

        if not progress:
            raise HTTPException(status_code=404, detail="用户进度不存在")

        # 在新的精简结构中，章节进度存储在metadata中，无需单独删除
        # 直接删除用户进度
        db.delete(progress)
        db.commit()

        return {
            "success": True,
            "message": "进度删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除用户进度失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
