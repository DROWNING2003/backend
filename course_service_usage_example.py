#!/usr/bin/env python3
"""
CourseService使用示例
演示如何使用改进后的课程服务，包括事务管理和异步关卡生成
"""

import sys
import os
import time
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def example_create_course():
    """示例：创建课程并异步生成关卡"""
    try:
        from app.services.course_service import CourseService
        from app.schemas.course import CourseCreate
        from app.database.connection import SessionLocal
        
        print("=== 课程创建和异步关卡生成示例 ===")
        
        # 创建CourseService实例
        course_service = CourseService()
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 准备课程数据
            course_data = CourseCreate(
                title="Python基础编程示例",
                tag="编程语言",
                description="这是一个测试课程，用于演示异步关卡生成功能",
                git_url="https://github.com/zengyi-thinking/auto_mate_test2.git"
            )
            
            print(f"\n1. 创建课程: {course_data.title}")
            print(f"   Git URL: {course_data.git_url}")
            
            # 创建课程（会自动启动异步关卡生成）
            course_response = course_service.create_course(db, course_data)
            
            print(f"\n✅ 课程创建成功！")
            print(f"   课程ID: {course_response.id}")
            print(f"   状态消息: {course_response.message}")
            print(f"   生成状态: {course_response.generation_status}")
            
            # 轮询检查生成状态
            print(f"\n2. 监控关卡生成进度...")
            course_id = course_response.id
            
            for i in range(10):  # 最多检查10次
                time.sleep(3)  # 等待3秒
                
                status = course_service.get_course_generation_status(db, course_id)
                print(f"   检查 {i+1}: {status['message']}")
                
                if status['status'] == 'completed':
                    print(f"   🎉 关卡生成完成！共生成 {status['level_count']} 个关卡")
                    break
                elif status['status'] == 'failed':
                    print(f"   ❌ 关卡生成失败")
                    break
                elif i == 9:
                    print(f"   ⏰ 生成仍在进行中，请稍后手动检查")
            
            # 获取最终的课程信息
            print(f"\n3. 获取最终课程信息...")
            final_course = course_service.get_course_by_id(db, course_id)
            if final_course:
                print(f"   课程标题: {final_course.title}")
                print(f"   完成状态: {'已完成' if final_course.is_completed else '未完成'}")
                print(f"   关卡数量: {final_course.total_levels}")
                
                if final_course.levels:
                    print(f"   关卡列表:")
                    for level in final_course.levels[:3]:  # 只显示前3个
                        print(f"     - {level.title}")
                    if len(final_course.levels) > 3:
                        print(f"     ... 还有 {len(final_course.levels) - 3} 个关卡")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def example_check_existing_course():
    """示例：检查现有课程的状态"""
    try:
        from app.services.course_service import CourseService
        from app.database.connection import SessionLocal
        
        print("\n=== 检查现有课程状态示例 ===")
        
        course_service = CourseService()
        db = SessionLocal()
        
        try:
            # 获取所有课程
            courses_response = course_service.get_all_courses(db)
            
            print(f"找到 {courses_response.total} 个课程:")
            
            for course in courses_response.courses:
                print(f"\n课程ID: {course.id}")
                print(f"标题: {course.title}")
                print(f"完成状态: {'已完成' if course.is_completed else '未完成'}")
                print(f"关卡数量: {course.total_levels}")
                
                # 检查生成状态
                status = course_service.get_course_generation_status(db, course.id)
                print(f"生成状态: {status['status']} - {status['message']}")
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 检查现有课程失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("CourseService使用示例")
    print("=" * 50)
    
    # 示例1：创建新课程
    print("\n选择操作:")
    print("1. 创建新课程并演示异步关卡生成")
    print("2. 检查现有课程状态")
    print("3. 退出")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            example_create_course()
        elif choice == "2":
            example_check_existing_course()
        elif choice == "3":
            print("退出程序")
        else:
            print("无效选择")
            
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()