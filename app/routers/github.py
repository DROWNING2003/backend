"""
GitHub仓库相关API路由
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from app.utils.github_crawler import GitHubCrawler
from app.utils.enhanced_llm import EnhancedLLMClient

logger = logging.getLogger(__name__)
router = APIRouter()

# 初始化工具
github_crawler = GitHubCrawler()
enhanced_llm = EnhancedLLMClient()

# 内存中存储爬取任务状态（生产环境应使用数据库）
crawl_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/github/crawl")
async def crawl_repository(request: Dict[str, Any]):
    """
    爬取GitHub仓库
    """
    try:
        repo_url = request.get("repo_url")
        if not repo_url:
            raise HTTPException(status_code=400, detail="repo_url参数必需")
        
        # 可选参数
        max_file_size = request.get("max_file_size", 1024 * 1024)  # 1MB
        include_patterns = request.get("include_patterns")
        exclude_patterns = request.get("exclude_patterns")
        branch = request.get("branch", "main")
        
        logger.info(f"开始爬取仓库: {repo_url}")
        
        # 执行爬取
        result = await github_crawler.crawl_repository(
            repo_url=repo_url,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch
        )
        
        # 添加文件摘要
        if result["files"]:
            result["summary"] = github_crawler.get_file_summary(result["files"])
        
        logger.info(f"仓库爬取完成: {repo_url}")
        return result
    
    except Exception as e:
        logger.error(f"爬取仓库失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取仓库失败: {str(e)}")


@router.post("/github/crawl-async")
async def crawl_repository_async(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    异步爬取GitHub仓库
    """
    try:
        repo_url = request.get("repo_url")
        if not repo_url:
            raise HTTPException(status_code=400, detail="repo_url参数必需")
        
        # 生成任务ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # 创建任务状态
        task_status = {
            "task_id": task_id,
            "status": "pending",
            "repo_url": repo_url,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error": None
        }
        
        crawl_tasks[task_id] = task_status
        
        # 添加后台任务
        background_tasks.add_task(
            process_crawl_async,
            task_id,
            request
        )
        
        logger.info(f"异步爬取任务创建: {task_id} - {repo_url}")
        return {"task_id": task_id, "status": "pending"}
    
    except Exception as e:
        logger.error(f"创建异步爬取任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建异步爬取任务失败")


async def process_crawl_async(task_id: str, request: Dict[str, Any]):
    """
    异步处理爬取任务
    """
    try:
        # 更新任务状态
        crawl_tasks[task_id]["status"] = "processing"
        crawl_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        # 执行爬取
        repo_url = request.get("repo_url")
        max_file_size = request.get("max_file_size", 1024 * 1024)
        include_patterns = request.get("include_patterns")
        exclude_patterns = request.get("exclude_patterns")
        branch = request.get("branch", "main")
        
        result = await github_crawler.crawl_repository(
            repo_url=repo_url,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            branch=branch
        )
        
        # 添加文件摘要
        if result["files"]:
            result["summary"] = github_crawler.get_file_summary(result["files"])
        
        # 更新任务状态为完成
        crawl_tasks[task_id]["status"] = "completed"
        crawl_tasks[task_id]["result"] = result
        crawl_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"异步爬取任务完成: {task_id}")
    
    except Exception as e:
        # 更新任务状态为失败
        crawl_tasks[task_id]["status"] = "failed"
        crawl_tasks[task_id]["error"] = str(e)
        crawl_tasks[task_id]["updated_at"] = datetime.now().isoformat()
        
        logger.error(f"异步爬取任务失败: {task_id} - {str(e)}")


@router.post("/github/task-status")
async def get_crawl_task_status(request: Dict[str, Any]):
    """
    获取爬取任务状态
    """
    try:
        task_id = request.get("task_id")
        if not task_id:
            raise HTTPException(status_code=400, detail="task_id参数必需")
        
        task_status = crawl_tasks.get(task_id)
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return task_status
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


@router.post("/github/analyze")
async def analyze_repository(request: Dict[str, Any]):
    """
    使用LLM分析仓库代码
    """
    try:
        files = request.get("files", {})
        analysis_type = request.get("analysis_type", "overview")
        
        if not files:
            raise HTTPException(status_code=400, detail="files参数必需")
        
        # 构建分析提示
        prompt = _build_analysis_prompt(files, analysis_type)
        
        # 调用LLM进行分析
        analysis_result = await enhanced_llm.call_llm(
            prompt=prompt,
            model="moonshot-v1-8k",
            use_cache=True
        )
        
        logger.info(f"仓库分析完成，类型: {analysis_type}")
        
        return {
            "analysis_type": analysis_type,
            "result": analysis_result,
            "file_count": len(files),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"仓库分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"仓库分析失败: {str(e)}")


@router.post("/github/llm-status")
async def get_llm_status(request: Dict[str, Any] = {}):
    """
    获取LLM服务状态
    """
    try:
        cache_stats = enhanced_llm.get_cache_stats()
        
        return {
            "status": "healthy",
            "cache_stats": cache_stats,
            "available_models": [
                "moonshot-v1-8k",
                "moonshot-v1-32k",
                "moonshot-v1-128k",
                "deepseek-ai/DeepSeek-R1"
            ]
        }
    
    except Exception as e:
        logger.error(f"获取LLM状态失败: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/github/clear-cache")
async def clear_llm_cache(request: Dict[str, Any] = {}):
    """
    清空LLM缓存
    """
    try:
        enhanced_llm.clear_cache()
        return {"message": "缓存已清空"}
    
    except Exception as e:
        logger.error(f"清空缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail="清空缓存失败")


def _build_analysis_prompt(files: Dict[str, str], analysis_type: str) -> str:
    """
    构建分析提示
    """
    file_list = "\n".join([f"- {path}" for path in files.keys()])
    
    if analysis_type == "overview":
        prompt = f"""
请分析以下GitHub仓库的代码结构和功能：

文件列表：
{file_list}

请提供：
1. 项目的主要功能和用途
2. 技术栈和架构分析
3. 代码结构和组织方式
4. 主要模块和组件
5. 项目的特点和亮点

请用中文回答，保持简洁明了。
"""
    elif analysis_type == "structure":
        prompt = f"""
请分析以下GitHub仓库的代码结构：

文件列表：
{file_list}

请提供：
1. 目录结构分析
2. 文件组织方式
3. 模块划分
4. 依赖关系
5. 架构模式

请用中文回答。
"""
    elif analysis_type == "summary":
        # 包含部分文件内容进行分析
        content_sample = ""
        for i, (path, content) in enumerate(files.items()):
            if i >= 5:  # 只分析前5个文件
                break
            content_sample += f"\n\n=== {path} ===\n{content[:1000]}..."
        
        prompt = f"""
请分析以下GitHub仓库的代码：

文件列表：
{file_list}

部分文件内容：
{content_sample}

请提供项目的详细分析和总结。
"""
    else:
        prompt = f"""
请分析以下GitHub仓库：

文件列表：
{file_list}

请提供详细的分析报告。
"""
    
    return prompt
