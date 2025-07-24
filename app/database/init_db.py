"""
数据库初始化脚本
"""

import logging
from sqlalchemy import text
from app.database.connection import engine, Base, SessionLocal
from app.models import Course, Repository, RepositoryFile, CrawlTask, LLMCache, UserProgress, Tutorial, UserAchievement

logger = logging.getLogger(__name__)


def create_database_if_not_exists():
    """
    创建数据库（如果不存在）
    """
    try:
        # 从连接URL中提取数据库名
        database_url = str(engine.url)
        if "auto_mate" in database_url:
            database_name = "auto_mate"
        else:
            database_name = "github_learning_platform"
        
        # 创建不包含数据库名的连接URL
        base_url = database_url.replace(f"/{database_name}", "")
        
        # 连接到MySQL服务器（不指定数据库）
        from sqlalchemy import create_engine
        temp_engine = create_engine(base_url)
        
        with temp_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(
                text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'")
            )
            
            if not result.fetchone():
                # 创建数据库
                conn.execute(text(f"CREATE DATABASE {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                logger.info(f"数据库 {database_name} 创建成功")
            else:
                logger.info(f"数据库 {database_name} 已存在")
        
        temp_engine.dispose()
        
    except Exception as e:
        logger.warning(f"创建数据库失败（可能数据库已存在）: {e}")


def create_tables():
    """
    创建所有数据表
    """
    try:
        logger.info("开始创建数据表...")
        Base.metadata.create_all(bind=engine)
        logger.info("数据表创建成功")
        return True
    except Exception as e:
        logger.error(f"创建数据表失败: {e}")
        return False


def init_sample_data():
    """
    初始化示例数据（精简版）
    """
    try:
        db = SessionLocal()

        # 检查是否已有数据
        if db.query(Tutorial).count() > 0:
            logger.info("数据库已有数据，跳过初始化")
            db.close()
            return

        # 创建示例教程数据（替代原来的等级系统）
        tutorials = [
            Tutorial(
                title="Python基础入门",
                description="从零开始学习Python编程语言",
                difficulty="beginner",
                estimated_time=120,
                is_active=True,
                extra_data={
                    "tags": ["python", "programming", "beginner"],
                    "chapters": [
                        {
                            "id": 1,
                            "title": "Python环境搭建",
                            "description": "学习如何安装和配置Python开发环境",
                            "estimated_time": 30,
                            "order_index": 1
                        },
                        {
                            "id": 2,
                            "title": "基础语法",
                            "description": "掌握Python的基本语法和数据类型",
                            "estimated_time": 45,
                            "order_index": 2
                        },
                        {
                            "id": 3,
                            "title": "控制流程",
                            "description": "学习条件语句和循环结构",
                            "estimated_time": 45,
                            "order_index": 3
                        }
                    ]
                }
            ),
            Tutorial(
                title="FastAPI实战项目",
                description="使用FastAPI构建现代Web API",
                difficulty="intermediate",
                estimated_time=240,
                is_active=True,
                extra_data={
                    "tags": ["fastapi", "web", "api", "intermediate"],
                    "chapters": [
                        {
                            "id": 1,
                            "title": "FastAPI简介",
                            "description": "了解FastAPI框架的特点和优势",
                            "estimated_time": 60,
                            "order_index": 1
                        },
                        {
                            "id": 2,
                            "title": "路由和请求处理",
                            "description": "学习如何定义路由和处理HTTP请求",
                            "estimated_time": 90,
                            "order_index": 2
                        },
                        {
                            "id": 3,
                            "title": "数据库集成",
                            "description": "集成数据库并实现CRUD操作",
                            "estimated_time": 90,
                            "order_index": 3
                        }
                    ]
                }
            )
        ]

        for tutorial in tutorials:
            db.add(tutorial)

        db.commit()
        
        # 创建示例课程数据（精简版，移除level_id依赖）
        courses = [
            Course(
                title="Python基础教程",
                description="从零开始学习Python编程语言",
                github_url="https://github.com/example/python-basics",
                difficulty=1,
                estimated_time=120,
                is_published=True
            ),
            Course(
                title="FastAPI实战项目",
                description="使用FastAPI构建现代Web API",
                github_url="https://github.com/example/fastapi-tutorial",
                difficulty=3,
                estimated_time=240,
                is_published=True
            ),
            Course(
                title="微服务架构设计",
                description="学习微服务架构的设计和实现",
                github_url="https://github.com/example/microservices",
                difficulty=5,
                estimated_time=480,
                is_published=True
            )
        ]

        for course in courses:
            db.add(course)

        db.commit()
        db.close()
        
        logger.info("示例数据初始化成功")
        
    except Exception as e:
        logger.error(f"初始化示例数据失败: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()


def init_database():
    """
    完整的数据库初始化流程
    """
    logger.info("开始数据库初始化...")
    
    try:
        # 1. 创建数据库（如果不存在）
        create_database_if_not_exists()
        
        # 2. 创建数据表
        if not create_tables():
            return False
        
        # 3. 初始化示例数据
        init_sample_data()
        
        logger.info("数据库初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False


def check_database_connection():
    """
    检查数据库连接
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                logger.info("数据库连接正常")
                return True
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False


def get_database_info():
    """
    获取数据库信息
    """
    try:
        db = SessionLocal()
        
        info = {
            "tutorials_count": db.query(Tutorial).count(),
            "user_progress_count": db.query(UserProgress).count(),
            "user_achievements_count": db.query(UserAchievement).count(),
            "courses_count": db.query(Course).count(),
            "repositories_count": db.query(Repository).count(),
            "files_count": db.query(RepositoryFile).count(),
            "crawl_tasks_count": db.query(CrawlTask).count(),
            "llm_cache_count": db.query(LLMCache).count()
        }
        
        db.close()
        return info
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 初始化数据库
    if init_database():
        print("数据库初始化成功！")
        
        # 显示数据库信息
        info = get_database_info()
        print("数据库信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print("数据库初始化失败！")
