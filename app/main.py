"""
FastAPI主应用文件
GitHub仓库学习平台后端API
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from contextlib import asynccontextmanager

# 导入路由
from app.routers import levels, courses, llm, tts, github
from app.database.connection import engine, Base
from app.database.init_db import init_database, check_database_connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    try:
        logger.info("正在初始化数据库...")
        if check_database_connection():
            if init_database():
                logger.info("数据库初始化完成")
            else:
                logger.warning("数据库初始化失败，但连接正常")
        else:
            logger.warning("数据库连接失败，将以无数据库模式运行")
    except Exception as e:
        logger.warning(f"数据库初始化异常，将以无数据库模式运行: {str(e)}")
    yield
    # 关闭时的清理工作
    logger.info("应用正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title="GitHub仓库学习平台API",
    description="一个帮助用户学习GitHub仓库的教育平台后端API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
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
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "内部服务器错误", "status_code": 500}
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "GitHub仓库学习平台API运行正常"}


# 根路径
@app.get("/")
async def root():
    """根路径欢迎信息"""
    return {
        "message": "欢迎使用GitHub仓库学习平台API",
        "docs": "/docs",
        "health": "/health"
    }


# 注册路由
app.include_router(github.router, prefix="/api", tags=["GitHub仓库"])
app.include_router(levels.router, prefix="/api", tags=["等级管理"])
app.include_router(courses.router, prefix="/api", tags=["课程管理"])
app.include_router(llm.router, prefix="/api", tags=["AI对话"])
app.include_router(tts.router, prefix="/api", tags=["文本转语音"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
