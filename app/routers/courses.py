"""
课程管理相关API路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.connection import get_db
from app.models.course import Course
from app.models.level import Level
from app.schemas.course import (
    CourseResponse, CourseCreate, CourseUpdate, CourseListResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/courses", response_model=CourseListResponse)
async def get_courses(
    request: dict = {},
    db: Session = Depends(get_db)
):
    """
    获取课程列表
    """
    try:
        # 从请求体中获取参数
        skip = request.get("skip", 0)
        limit = request.get("limit", 100)
        level_id = request.get("level_id", None)
        is_published = request.get("is_published", None)
        search = request.get("search", None)

        query = db.query(Course)

        # 筛选条件
        if level_id is not None:
            query = query.filter(Course.level_id == level_id)

        if is_published is not None:
            query = query.filter(Course.is_published == is_published)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                Course.title.like(search_pattern) |
                Course.description.like(search_pattern)
            )
        
        # 获取总数
        total = query.count()
        
        # 获取课程列表
        courses = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
        
        response = CourseListResponse(
            courses=courses,
            total=total,
            page=skip // limit + 1,
            size=limit
        )
        
        logger.info(f"成功获取课程列表，共{len(courses)}条记录")
        return response
    
    except Exception as e:
        logger.error(f"获取课程列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程列表失败")


@router.post("/courses/detail", response_model=CourseResponse)
async def get_course(request: dict, db: Session = Depends(get_db)):
    """
    根据ID获取特定课程信息
    """
    try:
        course_id = request.get("course_id")
        if not course_id:
            raise HTTPException(status_code=400, detail="course_id参数必需")

        course = db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")
        
        logger.info(f"成功获取课程信息: {course.title}")
        return course
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取课程信息失败")


@router.post("/courses/create", response_model=CourseResponse)
async def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    """
    创建新课程（管理员功能）
    """
    try:
        # 验证等级是否存在
        if course.level_id:
            level = db.query(Level).filter(Level.id == course.level_id).first()
            if not level:
                raise HTTPException(status_code=400, detail="指定的等级不存在")
        
        # 检查课程标题是否已存在
        existing_course = db.query(Course).filter(Course.title == course.title).first()
        if existing_course:
            raise HTTPException(status_code=400, detail="课程标题已存在")
        
        db_course = Course(**course.dict())
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        
        logger.info(f"成功创建课程: {db_course.title}")
        return db_course
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建课程失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建课程失败")


@router.post("/courses/update", response_model=CourseResponse)
async def update_course(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    更新课程信息（管理员功能）
    """
    try:
        course_id = request.get("course_id")
        if not course_id:
            raise HTTPException(status_code=400, detail="course_id参数必需")

        course_update_data = request.get("course_update", {})

        course = db.query(Course).filter(Course.id == course_id).first()

        if not course:
            raise HTTPException(status_code=404, detail="课程不存在")

        # 验证等级是否存在
        if course_update_data.get("level_id"):
            level = db.query(Level).filter(Level.id == course_update_data["level_id"]).first()
            if not level:
                raise HTTPException(status_code=400, detail="指定的等级不存在")

        # 更新课程信息
        for field, value in course_update_data.items():
            if hasattr(course, field):
                setattr(course, field, value)
        
        db.commit()
        db.refresh(course)
        
        logger.info(f"成功更新课程: {course.title}")
        return course
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新课程失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新课程失败")
