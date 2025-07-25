"""
关卡管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database.connection import get_db
from app.schemas.level import (
    LevelGetRequest, LevelResponse, LevelCheckRequest, LevelCheckResponse,
    GenerateLevelsRequest, GeneratedLevelsResponse
)
from app.services.level_service import LevelService
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter()
level_service = LevelService()
ai_service = AIService()


@router.post("/get", response_model=LevelResponse, summary="获取指定关卡详细内容")
async def get_level(
    request: LevelGetRequest,
    db: Session = Depends(get_db)
):
    """
    获取指定关卡的详细内容
    
    参数：
    - level_id: 关卡ID
    
    返回：
    - 关卡的完整信息（标题、描述、通过要求、顺序号、所属课程信息等）
    """
    try:
        logger.info(f"获取关卡详情请求: {request.level_id}")
        
        result = level_service.get_level_by_id(db, request.level_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"关卡 {request.level_id} 不存在"
            )
        
        logger.info(f"成功获取关卡详情: {request.level_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关卡详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取关卡详情失败: {str(e)}"
        )


@router.post("/check-completion", response_model=LevelCheckResponse, summary="检查关卡完成状态")
async def check_level_completion(
    request: LevelCheckRequest,
    db: Session = Depends(get_db)
):
    """
    检查关卡完成状态
    
    功能：
    - AI审查用户提交的内容
    - 直接返回是否通过（无需在数据库中存储完成标记）
    - 提供详细的反馈和改进建议
    
    参数：
    - level_id: 关卡ID
    - user_answer: 用户提交的答案/代码
    
    返回：
    - passed: 是否通过
    - feedback: 反馈信息
    - score: 得分(0-100)
    - suggestions: 改进建议
    """
    try:
        logger.info(f"检查关卡完成状态请求: {request.level_id}")
        
        # 验证用户答案不能为空
        if not request.user_answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户答案不能为空"
            )
        
        result = level_service.check_level_completion(
            db, request.level_id, request.user_answer
        )
        
        logger.info(f"关卡 {request.level_id} 检查完成，结果: {'通过' if result.passed else '未通过'}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查关卡完成状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查关卡完成状态失败: {str(e)}"
        )


@router.post("/generate-from-git", response_model=GeneratedLevelsResponse, summary="基于Git仓库生成关卡")
async def generate_levels_from_git(request: GenerateLevelsRequest):
    """
    基于Git仓库生成关卡
    
    功能：
    - 调用agentflow中的AI服务
    - 自动分析Git仓库内容
    - 生成适合的关卡内容和要求
    
    参数：
    - git_url: Git仓库URL
    - project_name: 项目名称（可选）
    - language: 输出语言（默认中文）
    - max_levels: 最大关卡数量（1-20）
    
    返回：
    - success: 是否成功
    - levels: 生成的关卡列表
    - message: 处理消息
    - total_levels: 生成的关卡总数
    """
    try:
        logger.info(f"生成关卡请求: {request.git_url}")
        
        # 验证Git URL格式
        if not request.git_url.startswith(('http://', 'https://')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Git URL格式不正确，必须以http://或https://开头"
            )
        
        result = ai_service.generate_levels_from_git(
            git_url=request.git_url,
            project_name=request.project_name,
            max_levels=request.max_levels
        )
        
        logger.info(f"关卡生成完成: {result.total_levels} 个关卡")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成关卡失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成关卡失败: {str(e)}"
        )


@router.post("/get-generated", response_model=dict, summary="获取AI生成的关卡结果")
async def get_generated_levels():
    """
    获取AI生成的关卡结果
    
    返回：
    - 树形结构的关卡数据（对象数组格式）
    - 每个关卡的详细描述
    - AI服务状态信息
    """
    try:
        logger.info("获取AI生成关卡结果请求")
        
        # 获取AI服务状态
        ai_status = await ai_service.get_generated_levels_status()
        
        result = {
            "ai_service_status": ai_status,
            "message": "AI关卡生成服务就绪",
            "available_features": [
                "基于Git仓库分析生成关卡",
                "智能代码审查和反馈",
                "自适应难度调整"
            ]
        }
        
        logger.info("成功获取AI生成关卡结果")
        return result
        
    except Exception as e:
        logger.error(f"获取AI生成关卡结果失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取AI生成关卡结果失败: {str(e)}"
        )
