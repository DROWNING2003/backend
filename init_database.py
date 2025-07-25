"""
数据库初始化脚本
"""

import logging
from app.database.connection import check_database_connection, create_tables
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
            
            # 显示表结构信息
            logger.info("📋 数据表结构:")
            logger.info("  - courses: 课程表")
            logger.info("    * id (主键)")
            logger.info("    * title (课程标题)")
            logger.info("    * tag (课程标签)")
            logger.info("    * description (课程描述)")
            logger.info("    * git_url (Git仓库链接)")
            logger.info("    * image_url (课程图片URL)")
            logger.info("    * created_at, updated_at (时间戳)")
            
            logger.info("  - levels: 关卡表")
            logger.info("    * id (主键)")
            logger.info("    * course_id (外键)")
            logger.info("    * title (关卡标题)")
            logger.info("    * description (关卡描述)")
            logger.info("    * requirements (通过要求)")
            logger.info("    * order_number (关卡顺序号)")
            logger.info("    * content (关卡具体内容)")
            logger.info("    * created_at, updated_at (时间戳)")
            
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
