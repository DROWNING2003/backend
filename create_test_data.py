#!/usr/bin/env python3
"""
创建测试数据

这个脚本用于在数据库中创建测试用的课程和关卡数据
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_test_data():
    """创建测试数据"""
    
    print("🚀 开始创建测试数据...")
    
    try:
        from app.database.connection import SessionLocal
        from app.models.course import Course
        from app.models.level import Level
        
        db = SessionLocal()
        
        try:
            # 检查是否已存在测试数据
            existing_course = db.query(Course).filter(Course.id == 1).first()
            if existing_course:
                print("✅ 测试课程已存在，跳过创建")
            else:
                # 创建测试课程
                test_course = Course(
                    id=1,
                    title="Python基础编程",
                    tag="编程语言",
                    description="学习Python编程的基础知识",
                    git_url="https://github.com/octocat/Hello-World.git",  # 使用GitHub官方示例仓库
                    is_completed=True
                )
                
                db.add(test_course)
                db.commit()
                print("✅ 创建测试课程成功")
            
            # 检查是否已存在测试关卡
            existing_level = db.query(Level).filter(Level.id == 1).first()
            if existing_level:
                print("✅ 测试关卡已存在，跳过创建")
            else:
                # 创建测试关卡
                test_level = Level(
                    id=1,
                    course_id=1,
                    title="Hello World",
                    description="编写你的第一个Python程序",
                    requirements="创建一个输出'Hello, World!'的Python程序",
                    order_number=1
                )
                
                db.add(test_level)
                db.commit()
                print("✅ 创建测试关卡成功")
            
            # 验证数据
            course = db.query(Course).filter(Course.id == 1).first()
            level = db.query(Level).filter(Level.id == 1).first()
            
            if course and level:
                print("\n📊 测试数据验证:")
                print(f"   课程: {course.title} (ID: {course.id})")
                print(f"   关卡: {level.title} (ID: {level.id})")
                print(f"   Git URL: {course.git_url}")
                print("✅ 测试数据创建完成")
                return True
            else:
                print("❌ 测试数据验证失败")
                return False
                
        except Exception as e:
            db.rollback()
            print(f"❌ 创建测试数据失败: {str(e)}")
            return False
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("\n💡 解决方案:")
        print("1. 确保数据库服务正在运行")
        print("2. 检查数据库连接配置")
        print("3. 确保数据表已创建")
        return False


def test_api_with_real_data():
    """使用真实数据测试API"""
    
    print("\n🧪 使用真实数据测试API...")
    
    try:
        import requests
        import json
        
        # API配置
        BASE_URL = "http://localhost:8002"
        API_ENDPOINT = f"{BASE_URL}/api/levels/check-completion"
        
        # 测试数据
        test_data = {
            "level_id": 1,
            "course_id": 1,
            "user_file_tree": {
                "type": "directory",
                "uri": "file:///project",
                "children": [
                    {
                        "type": "file",
                        "uri": "file:///project/main.py",
                        "content": "print('Hello, World!')"
                    }
                ]
            }
        }
        
        print("📤 发送测试请求...")
        response = requests.post(
            API_ENDPOINT,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API测试成功!")
            print("\n📊 检查结果:")
            print(f"   是否通过: {'✅ 通过' if result.get('passed') else '❌ 未通过'}")
            print(f"   反馈: {result.get('feedback', 'N/A')}")
            
            if result.get('suggestions'):
                print("\n💡 改进建议:")
                for i, suggestion in enumerate(result['suggestions'], 1):
                    print(f"     {i}. {suggestion}")
            
            return True
        else:
            print(f"❌ API测试失败: {response.status_code}")
            try:
                error_info = response.json()
                print(f"错误信息: {error_info}")
            except:
                print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务")
        print("请确保FastAPI服务正在运行: uvicorn app.main:app --host 0.0.0.0 --port 8002")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {str(e)}")
        return False


def main():
    """主函数"""
    
    print("🎯 /check-completion API 测试数据创建和验证")
    print("=" * 60)
    
    # 步骤1: 创建测试数据
    if not create_test_data():
        print("\n❌ 测试数据创建失败，无法继续")
        return False
    
    # 步骤2: 测试API
    if not test_api_with_real_data():
        print("\n⚠️  API测试失败，但测试数据已创建")
        print("你可以手动启动服务后再次测试:")
        print("1. 启动服务: uvicorn app.main:app --host 0.0.0.0 --port 8002")
        print("2. 运行测试: python test_check_completion_api.py")
        return False
    
    print("\n🎉 所有测试都成功!")
    print("✅ 测试数据已创建")
    print("✅ API功能正常")
    print("✅ /check-completion API 已准备就绪")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)