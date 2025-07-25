#!/usr/bin/env python3
"""
测试CourseService的数据库连接
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_course_service():
    """测试CourseService的数据库连接"""
    try:
        from app.services.course_service import CourseService
        
        print("=== CourseService数据库连接测试 ===")
        
        # 创建CourseService实例
        course_service = CourseService()
        
        # 测试数据库连接
        print("\n1. 测试数据库连接...")
        if course_service.test_database_connection():
            print("✅ 数据库连接成功")
        else:
            print("❌ 数据库连接失败")
            return False
        
        # 检查SessionLocal是否已配置
        print("\n2. 检查SessionLocal配置...")
        if course_service.SessionLocal:
            print("✅ SessionLocal已配置")
        else:
            print("❌ SessionLocal未配置")
            return False
        
        # 测试创建异步数据库会话
        print("\n3. 测试创建异步数据库会话...")
        async_session = course_service._create_async_db_session()
        if async_session:
            print("✅ 异步数据库会话创建成功")
            async_session.close()
        else:
            print("❌ 异步数据库会话创建失败")
            return False
        
        print("\n🎉 所有测试通过！CourseService可以正常使用异步关卡生成功能")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_import():
    """测试数据库模块导入"""
    print("\n=== 数据库模块导入测试 ===")
    
    try:
        from app.database.connection import engine, SessionLocal
        print("✅ 成功导入 engine 和 SessionLocal")
        
        # 测试engine连接
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ engine连接测试成功")
        
        # 测试SessionLocal
        session = SessionLocal()
        session.execute(text("SELECT 1"))
        session.close()
        print("✅ SessionLocal测试成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试CourseService数据库连接...")
    
    # 先测试数据库模块导入
    if not test_database_import():
        print("\n❌ 数据库模块导入测试失败，请检查数据库配置")
        sys.exit(1)
    
    # 再测试CourseService
    if test_course_service():
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败，请检查配置")
        sys.exit(1)