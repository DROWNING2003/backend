"""
数据库初始化脚本
"""

import logging
from app.database.connection import check_database_connection, create_tables, engine
from app.models import Course, Level

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("🚀 开始初始化数据库...")
    
    try:
        # 检查数据库连接
        if not check_database_connection():
            logger.error("❌ 数据库连接失败")
            return False
        
        logger.info("✅ 数据库连接成功")
        
        # 创建数据表
        if create_tables():
            logger.info("✅ 数据表创建成功")
            
            # 显示实际的表结构信息
            logger.info("📋 数据表结构:")

            # 显示courses表结构
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("DESCRIBE courses"))
                courses_columns = result.fetchall()
                logger.info("  - courses: 课程表")
                for col in courses_columns:
                    comment = ""
                    if col[0] == "id":
                        comment = " (主键)"
                    elif col[0] == "title":
                        comment = " (课程标题)"
                    elif col[0] == "tag":
                        comment = " (课程标签)"
                    elif col[0] == "description":
                        comment = " (课程描述)"
                    elif col[0] == "git_url":
                        comment = " (Git仓库链接)"
                    elif col[0] == "image_url":
                        comment = " (课程图片URL)"
                    elif col[0] == "is_completed":
                        comment = " (创作者是否完成课程创作)"
                    elif col[0] in ["created_at", "updated_at"]:
                        comment = " (时间戳)"
                    logger.info(f"    * {col[0]} ({col[1]}){comment}")

                # 显示levels表结构
                result = conn.execute(text("DESCRIBE levels"))
                levels_columns = result.fetchall()
                logger.info("  - levels: 关卡表")
                for col in levels_columns:
                    comment = ""
                    if col[0] == "id":
                        comment = " (主键)"
                    elif col[0] == "course_id":
                        comment = " (外键，关联courses.id)"
                    elif col[0] == "title":
                        comment = " (关卡标题)"
                    elif col[0] == "description":
                        comment = " (关卡描述)"
                    elif col[0] == "requirements":
                        comment = " (通过要求)"
                    elif col[0] == "order_number":
                        comment = " (关卡顺序号)"
                    elif col[0] == "content":
                        comment = " (关卡具体内容，JSON格式)"
                    elif col[0] in ["created_at", "updated_at"]:
                        comment = " (时间戳)"
                    logger.info(f"    * {col[0]} ({col[1]}){comment}")
            
            logger.info("🎉 数据库初始化完成！")
            return True
        else:
            logger.error("❌ 数据表创建失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 数据库初始化异常: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
