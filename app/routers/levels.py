"""
关卡管理API路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import tempfile
import shutil

from app.database.connection import get_db
from app.schemas.level import (
    LevelGetRequest, LevelResponse, LevelCheckRequest, LevelCheckResponse,
    GenerateLevelsRequest, GeneratedLevelsResponse
)
from app.services.level_service import LevelService
from app.services.ai_service import AIService
from app.models.course import Course

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
    获取指定关卡的详细内容，包含对应提交的文件树结构
    
    参数：
    - course_id: 课程ID
    - level_id: 关卡ID
    
    返回：
    - 关卡的完整信息（标题、描述、通过要求、顺序号、所属课程信息等）
    - 对应提交的项目文件树结构
    """
    import tempfile
    from agentflow.utils.crawl_github_files import (
        clone_repository, reset_to_commit, filter_and_read_files, 
        get_file_patterns, get_exclude_patterns
    )
    from app.utils.file_tree_builder import build_file_tree_from_files, sort_file_tree
    from app.models.course import Course
    
    try:
        logger.info(f"获取关卡详情请求: 课程ID={request.course_id}, 关卡ID={request.level_id}")
        
        # 1. 获取关卡基本信息
        level_result = level_service.get_level_by_id(db, request.level_id)
        
        if not level_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"关卡 {request.level_id} 不存在"
            )
        
        # 2. 验证关卡是否属于指定课程
        if level_result.course_id != request.course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"关卡 {request.level_id} 不属于课程 {request.course_id}"
            )
        
        # 3. 获取课程信息
        course = db.query(Course).filter(Course.id == request.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"课程 {request.course_id} 不存在"
            )
        
        if not course.git_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"课程 {request.course_id} 没有配置Git仓库URL"
            )
        
        # 4. 获取对应提交的文件
        tmpdirname = None
        file_tree = None
        
        try:
            # 创建临时目录
            tmpdirname = tempfile.mkdtemp()
            
            # 克隆仓库
            repo = clone_repository(course.git_url, tmpdirname)
            
            # 计算提交索引（关卡顺序号 + 1，因为从第2个提交开始）
            current_index = level_result.order_number + 1
            
            # 重置到指定提交
            commits = list(repo.iter_commits(reverse=True))
            if current_index > len(commits):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"关卡对应的提交索引 {current_index} 超出仓库提交范围 (1-{len(commits)})"
                )
            
            reset_to_commit(repo, commits, current_index)
            
            # 获取文件
            result = filter_and_read_files(
                tmpdirname,
                max_file_size=1 * 1024 * 1024,
                include_patterns=get_file_patterns("code"),  # 预定义代码模式
                exclude_patterns=get_exclude_patterns("common")  # 排除常见无用文件
            )
            
            # 构建文件树
            if result["files"]:
                # 构建项目名称作为根URI
                project_name = course.git_url.split('/')[-1].replace('.git', '')
                base_uri = f"file:///github/{project_name}"
                
                file_tree = build_file_tree_from_files(result["files"], base_uri)
                file_tree = sort_file_tree(file_tree)
                
                logger.info(f"成功构建文件树，包含 {len(result['files'])} 个文件")
            else:
                logger.warning(f"未找到符合条件的文件")
        
        except Exception as git_error:
            logger.error(f"获取Git文件失败: {git_error}")
            # 不中断主流程，只是没有文件树
            file_tree = None
        
        finally:
            # 清理临时目录
            if tmpdirname:
                try:
                    import shutil
                    shutil.rmtree(tmpdirname)
                except Exception as cleanup_error:
                    logger.warning(f"清理临时目录失败: {cleanup_error}")
        
        # 5. 构建响应
        response_data = level_result.model_dump()
        if file_tree:
            response_data["file_tree"] = file_tree.model_dump()
        
        logger.info(f"成功获取关卡详情: 课程ID={request.course_id}, 关卡ID={request.level_id}")
        return LevelResponse(**response_data)
        
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
    request: dict,
    db: Session = Depends(get_db)
):
    """
    检查关卡完成状态
    
    功能：
    - 使用AgentFlow进行智能代码检查
    - 支持两种输入格式：字符串代码或文件树结构
    - 提供详细的反馈和改进建议
    
    参数格式1（兼容旧版）：
    - level_id: 关卡ID
    - user_answer: 用户提交的答案/代码（字符串）
    
    参数格式2（推荐）：
    - level_id: 关卡ID
    - course_id: 课程ID
    - user_file_tree: 用户提交的文件树结构
    
    返回：
    - passed: 是否通过
    - feedback: 反馈信息
    - suggestions: 改进建议
    """
    try:
        level_id = request.get("level_id")
        if not level_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必要参数: level_id"
            )
        
        logger.info(f"检查关卡完成状态请求: 关卡ID={level_id}")
        
        # 检查输入格式：文件树格式（推荐）或字符串格式（兼容）
        user_file_tree = request.get("user_file_tree")
        user_answer = request.get("user_answer")
        course_id = request.get("course_id")
        
        if user_file_tree and course_id:
            # 格式2：使用文件树和check_flow
            logger.info("使用文件树格式和check_flow进行检查")
            
            # 准备共享数据
            shared = {
                "level_id": level_id,
                "course_id": course_id,
                "user_file_tree": user_file_tree,
                "language": "chinese",
                "use_cache": True
            }
            
            # 导入并运行检查流程
            from agentflow.flow import check_flow
            
            flow = check_flow()
            flow.run(shared)
            
            # 获取检查结果
            result = shared.get("judgment_result")
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="检查流程未返回结果"
                )
            
            # 转换为API响应格式
            response = LevelCheckResponse(
                passed=result.get("passed", False),
                feedback=result.get("feedback", "检查完成"),
                score=None,  # 不使用score字段
                suggestions=result.get("suggestions", [])
            )
            
        elif user_answer:
            # 格式1：兼容旧版字符串格式
            logger.info("使用字符串格式进行检查（兼容模式）")
            
            # 验证用户答案不能为空
            if not user_answer.strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户答案不能为空"
                )
            
            # 将字符串转换为简单的文件树格式
            simple_file_tree = {
                "type": "directory",
                "uri": "file:///project",
                "children": [
                    {
                        "type": "file",
                        "uri": "file:///project/solution.py",
                        "content": user_answer
                    }
                ]
            }
            
            # 获取课程ID（从数据库查询关卡信息）
            try:
                level_result = level_service.get_level_by_id(db, level_id)
                if not level_result:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"关卡 {level_id} 不存在"
                    )
                course_id = level_result.course_id
            except Exception as e:
                logger.error(f"获取关卡信息失败: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="无法获取关卡信息"
                )
            
            # 使用check_flow进行检查
            shared = {
                "level_id": level_id,
                "course_id": course_id,
                "user_file_tree": simple_file_tree,
                "language": "chinese",
                "use_cache": True
            }
            
            from agentflow.flow import check_flow
            
            flow = check_flow()
            flow.run(shared)
            
            result = shared.get("judgment_result")
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="检查流程未返回结果"
                )
            
            response = LevelCheckResponse(
                passed=result.get("passed", False),
                feedback=result.get("feedback", "检查完成"),
                score=None,
                suggestions=result.get("suggestions", [])
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请提供 user_file_tree + course_id 或 user_answer 参数"
            )
        
        logger.info(f"关卡 {level_id} 检查完成，结果: {'通过' if response.passed else '未通过'}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"检查关卡完成状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查关卡完成状态失败: {str(e)}"
        )


@router.post("/check-with-flow", response_model=LevelCheckResponse, summary="使用Flow检查关卡完成状态")
async def check_level_with_flow(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    使用AgentFlow检查关卡完成状态
    
    功能：
    - 使用完整的检查流程（包括克隆仓库、获取标准答案等）
    - 对比用户提交的文件树和标准实现
    - 提供更准确的AI评判结果
    
    参数：
    - level_id: 关卡ID
    - course_id: 课程ID
    - user_file_tree: 用户提交的文件树结构
    
    返回：
    - passed: 是否通过
    - feedback: 反馈信息
    - score: 得分(0-100)
    - suggestions: 改进建议
    """
    try:
        # 验证请求参数
        level_id = request.get("level_id")
        course_id = request.get("course_id")
        user_file_tree = request.get("user_file_tree")
        
        if not all([level_id, course_id, user_file_tree]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必要参数: level_id, course_id, user_file_tree"
            )
        
        logger.info(f"使用Flow检查关卡: 课程ID={course_id}, 关卡ID={level_id}")
        
        # 准备共享数据
        shared = {
            "level_id": level_id,
            "course_id": course_id,
            "user_file_tree": user_file_tree,
            "language": "chinese",
            "use_cache": True
        }
        
        # 导入并运行检查流程
        from agentflow.flow import check_flow
        
        flow = check_flow()
        flow.run(shared)
        
        # 获取检查结果
        result = shared.get("judgment_result")
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="检查流程未返回结果"
            )
        
        # 转换为API响应格式
        response = LevelCheckResponse(
            passed=result.get("passed", False),
            feedback=result.get("feedback", "检查完成"),
            score=None,  # 不使用score字段
            suggestions=result.get("suggestions", [])
        )
        
        logger.info(f"Flow检查完成: 关卡{level_id}, 结果={'通过' if response.passed else '未通过'}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"使用Flow检查关卡失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"使用Flow检查关卡失败: {str(e)}"
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
