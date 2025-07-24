"""
等级管理相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.connection import get_db
from app.models.level import Level
from app.schemas.level import (
    LevelResponse, LevelCreate, LevelUpdate, 
    LevelCheckRequest, LevelCheckResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/levels", response_model=List[LevelResponse])
async def get_levels(
    request: dict = {},
    db: Session = Depends(get_db)
):
    """
    获取学习等级列表
    """
    try:
        # 从请求体中获取参数
        skip = request.get("skip", 0)
        limit = request.get("limit", 100)
        is_active = request.get("is_active", None)

        query = db.query(Level)

        if is_active is not None:
            query = query.filter(Level.is_active == is_active)

        levels = query.order_by(Level.difficulty.asc()).offset(skip).limit(limit).all()
        
        logger.info(f"成功获取等级列表，共{len(levels)}条记录")
        return levels
    
    except Exception as e:
        logger.error(f"获取等级列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取等级列表失败")


@router.post("/levels/detail", response_model=LevelResponse)
async def get_level(request: dict, db: Session = Depends(get_db)):
    """
    根据ID获取特定等级信息
    """
    try:
        level_id = request.get("level_id")
        if not level_id:
            raise HTTPException(status_code=400, detail="level_id参数必需")

        level = db.query(Level).filter(Level.id == level_id).first()
        
        if not level:
            raise HTTPException(status_code=404, detail="等级不存在")
        
        logger.info(f"成功获取等级信息: {level.name}")
        return level
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取等级信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取等级信息失败")


@router.post("/levels/check", response_model=LevelCheckResponse)
async def check_level(
    request: LevelCheckRequest,
    db: Session = Depends(get_db)
):
    """
    检查用户等级，判断是否可以升级
    """
    try:
        # 获取当前等级信息
        current_level = None
        if request.current_level_id:
            current_level = db.query(Level).filter(
                Level.id == request.current_level_id
            ).first()
        
        # 查找用户可以达到的最高等级
        available_levels = db.query(Level).filter(
            Level.is_active == True,
            Level.required_score <= request.user_score
        ).order_by(Level.required_score.desc()).all()
        
        # 查找下一个等级
        next_level = db.query(Level).filter(
            Level.is_active == True,
            Level.required_score > request.user_score
        ).order_by(Level.required_score.asc()).first()
        
        # 判断是否可以升级
        can_upgrade = False
        if available_levels:
            highest_available = available_levels[0]
            if not current_level or highest_available.id != current_level.id:
                can_upgrade = True
                current_level = highest_available
        
        # 计算升级所需积分
        score_needed = 0
        if next_level:
            score_needed = next_level.required_score - request.user_score
        
        response = LevelCheckResponse(
            can_upgrade=can_upgrade,
            next_level=next_level,
            current_level=current_level,
            score_needed=score_needed
        )
        
        logger.info(f"等级检查完成，用户积分: {request.user_score}, 可升级: {can_upgrade}")
        return response
    
    except Exception as e:
        logger.error(f"等级检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail="等级检查失败")


@router.post("/levels/create", response_model=LevelResponse)
async def create_level(level: LevelCreate, db: Session = Depends(get_db)):
    """
    创建新等级（管理员功能）
    """
    try:
        # 检查等级名称是否已存在
        existing_level = db.query(Level).filter(Level.name == level.name).first()
        if existing_level:
            raise HTTPException(status_code=400, detail="等级名称已存在")
        
        db_level = Level(**level.dict())
        db.add(db_level)
        db.commit()
        db.refresh(db_level)
        
        logger.info(f"成功创建等级: {db_level.name}")
        return db_level
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建等级失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建等级失败")
