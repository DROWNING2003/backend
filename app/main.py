"""
课程学习平台后端API主应用
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.database.connection import check_database_connection, create_tables
from app.routers import courses_router, levels_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("🚀 课程学习平台后端API启动中...")
    
    try:
        # 检查数据库连接
        if check_database_connection():
            logger.info("✅ 数据库连接正常")
            
            # 创建数据表
            if create_tables():
                logger.info("✅ 数据表初始化完成")
            else:
                logger.warning("⚠️ 数据表初始化失败")
        else:
            logger.error("❌ 数据库连接失败")
            
    except Exception as e:
        logger.error(f"❌ 应用初始化失败: {e}")
    
    logger.info("🎉 课程学习平台后端API启动完成")
    
    yield
    
    # 关闭时的清理
    logger.info("👋 课程学习平台后端API正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title="课程学习平台后端API",
    description="基于FastAPI的课程学习平台后端系统，支持课程管理、关卡生成和AI智能评估",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "服务器内部错误",
            "status_code": 500
        }
    )


# 注册路由
app.include_router(courses_router, prefix="/api/courses", tags=["课程管理"])
app.include_router(levels_router, prefix="/api/levels", tags=["关卡管理"])


# 根路径
@app.get("/", summary="API根路径")
async def root():
    """API根路径，返回基本信息"""
    return {
        "message": "课程学习平台后端API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# 健康检查
@app.get("/health", summary="健康检查")
async def health_check():
    """健康检查接口"""
    try:
        db_status = check_database_connection()
        
        return {
            "status": "healthy" if db_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": "2024-01-01T12:00:00Z"
        }


# API信息
@app.get("/api/info", summary="API信息")
async def api_info():
    """获取API详细信息"""
    return {
        "name": "课程学习平台后端API",
        "version": "1.0.0",
        "description": "基于FastAPI的课程学习平台后端系统",
        "features": [
            "课程管理（创建、列表、详情）",
            "关卡管理（获取、完成检查）",
            "AI关卡生成（基于Git仓库）",
            "智能代码审查和反馈"
        ],
        "endpoints": {
            "courses": {
                "list": "POST /api/courses/list",
                "create": "POST /api/courses/create",
                "get": "POST /api/courses/get/{course_id}"
            },
            "levels": {
                "get": "POST /api/levels/get",
                "check": "POST /api/levels/check-completion",
                "generate": "POST /api/levels/generate-from-git",
                "get_generated": "POST /api/levels/get-generated"
            }
        },
        "database": "MySQL (auto_mate)",
        "ai_integration": "agentflow"
    }


if __name__ == "__main__":
    # 开发环境运行
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
