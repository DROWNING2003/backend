"""
数据库连接配置
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Zhuqing5201314@localhost:3306/auto_mate")
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"

# 创建数据库引擎
try:
    engine = create_engine(
        DATABASE_URL,
        echo=DATABASE_ECHO,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=10,
        max_overflow=20
    )
    logger.info("数据库引擎创建成功")
except Exception as e:
    logger.error(f"数据库引擎创建失败: {e}")
    raise

# 创建基础模型类
Base = declarative_base()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 元数据
metadata = MetaData()


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    检查数据库连接是否正常
    """
    try:
        from sqlalchemy import text
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("数据库连接检查成功")
        return True
    except SQLAlchemyError as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
    except Exception as e:
        logger.error(f"数据库连接检查异常: {e}")
        return False


def create_tables():
    """
    创建所有数据表
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据表创建成功")
        return True
    except Exception as e:
        logger.error(f"数据表创建失败: {e}")
        return False
