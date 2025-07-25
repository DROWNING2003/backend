"""
课程管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database.connection import get_db
from app.schemas.course import CourseCreate, CourseResponse, CourseListResponse
from app.services.course_service import CourseService

logger = logging.getLogger(__name__)
router = APIRouter()
course_service = CourseService()


@router.post("/list", response_model=CourseListResponse, summary="获取所有课程列表")
async def list_courses(db: Session = Depends(get_db)):
    """
    获取所有课程列表
    
    返回所有课程的基本信息，包括：
    - 课程ID、标题、标签、描述
    - 默认图片URL
    - 该课程包含的关卡列表（关卡ID、标题、顺序号）
    """
    try:
        logger.info("获取课程列表请求")
        
        result = course_service.get_all_courses(db)
        
        logger.info(f"成功获取 {result.total} 个课程")
        return result
        
    except Exception as e:
        logger.error(f"获取课程列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取课程列表失败: {str(e)}"
        )


@router.post("/create", response_model=CourseResponse, summary="创建新课程")
async def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db)
):
    """
    创建新课程
    
    功能：
    - 创建课程记录并自动生成唯一ID
    - 生成默认图片URL
    - 调用AI服务自动生成关卡并与课程建立外键关联
    
    参数：
    - title: 课程标题
    - tag: 课程标签/范畴
    - description: 课程描述
    - git_url: Git仓库URL
    """
    # try:
    logger.info(f"创建课程请求: {course_data.git_url}")
        

        
    result = course_service.create_course(db, course_data)
        
        # logger.info(f"成功创建课程: {result.id} - {result.title}")
    return result
        
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     logger.error(f"创建课程失败: {e}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"创建课程失败: {str(e)}"
    #     )


@router.post("/get/{course_id}", response_model=CourseResponse, summary="获取指定课程详情")
async def get_course(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    获取指定课程的详细信息
    
    参数：
    - course_id: 课程ID
    
    返回：
    - 课程的完整信息，包括关卡列表
    """
    try:
        logger.info(f"获取课程详情请求: {course_id}")
        
        result = course_service.get_course_by_id(db, course_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"课程 {course_id} 不存在"
            )
        
        logger.info(f"成功获取课程详情: {course_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取课程详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取课程详情失败: {str(e)}"
        )
