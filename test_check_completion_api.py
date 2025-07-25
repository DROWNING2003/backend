#!/usr/bin/env python3
"""
测试 /check-completion API

这个文件用于测试修改后的check_level_completion API是否正常工作
"""

import json
import requests
import sys

# API基础URL（根据实际部署调整）
BASE_URL = "http://localhost:8002"
API_ENDPOINT = f"{BASE_URL}/api/levels/check-completion"

def test_file_tree_format():
    """测试文件树格式的API调用"""
    
    print("🧪 测试文件树格式API调用...")
    
    # 文件树格式的请求数据
    request_data = {
        "level_id": 92,
        "course_id": 21,
        "user_file_tree": {
            "type": "directory",
            "uri": "file:///project",
            "children": [
                {
                    "type": "file",
                    "uri": "file:///project/main.py",
                    "content": """# 用户提交的Python代码
def greet(name):
    return f"Hello, {name}!"

def main():
    user_name = input("请输入你的名字: ")
    message = greet(user_name)
    print(message)

if __name__ == "__main__":
    main()
"""
                },
                {
                    "type": "file",
                    "uri": "file:///project/utils.py",
                    "content": """# 工具函数
def validate_name(name):
    if not name or not name.strip():
        return False
    return True
"""
                }
            ]
        }
    }
    
    print("📤 发送请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print("\n📊 检查结果:")
            print(f"   是否通过: {'✅ 通过' if result.get('passed') else '❌ 未通过'}")
            print(f"   反馈: {result.get('feedback', 'N/A')}")
            
            if result.get('suggestions'):
                print("\n💡 改进建议:")
                for i, suggestion in enumerate(result['suggestions'], 1):
                    print(f"     {i}. {suggestion}")
            
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 处理响应失败: {str(e)}")
        return False


def main():
    """运行所有测试"""
    
    print("🚀 开始测试 /check-completion API")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        health_response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if health_response.status_code != 200:
            print("❌ 服务未运行或无法访问")
            print("请确保FastAPI服务正在运行在 http://localhost:8000")
            return False
    except Exception:
        print("❌ 无法连接到服务")
        print("请确保FastAPI服务正在运行在 http://localhost:8000")
        print("启动命令: uvicorn app.main:app --reload")
        return False
    
    tests = [
        ("文件树格式测试", test_file_tree_format)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 运行测试: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
                
        except Exception as e:
            print(f"❌ {test_name} 异常: {str(e)}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📋 测试总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！API已准备就绪。")
        return True
    else:
        print("⚠️  部分测试失败，请检查API实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)