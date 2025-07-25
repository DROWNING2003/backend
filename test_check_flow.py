#!/usr/bin/env python3
"""
测试关卡检查流程

这个文件用于测试新创建的检查流程是否正常工作
"""

import sys
import os
import tempfile
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple_check():
    """测试简化的检查流程（不依赖数据库）"""
    
    print("🧪 测试简化检查流程...")
    
    try:
        from agentflow.nodes import CompareAndJudgeNode
        
        # 模拟数据
        mock_level_info = {
            "id": 1,
            "title": "Python基础 - 变量和数据类型",
            "description": "学习Python中的基本数据类型和变量声明",
            "requirements": "创建不同类型的变量并进行基本操作",
            "order_number": 1
        }
        
        mock_standard_code = {
            "main.py": """# 标准答案
name = "Python"
age = 25
height = 1.75
is_student = True

print(f"姓名: {name}")
print(f"年龄: {age}")
print(f"身高: {height}")
print(f"是否学生: {is_student}")
""",
            "README.md": """# Python变量示例
这个程序演示了Python中的基本数据类型。
"""
        }
        
        # 用户提交的代码（稍有不同但功能相同）
        user_code = {
            "main.py": """# 我的答案
student_name = "小明"
student_age = 20
student_height = 1.68
is_learning = True

print("学生信息:")
print("姓名:", student_name)
print("年龄:", student_age)
print("身高:", student_height)
print("正在学习:", is_learning)
""",
            "notes.txt": """学习笔记：
- Python有四种基本数据类型：字符串、整数、浮点数、布尔值
- 可以使用print函数输出变量值
"""
        }
        
        # 创建判断节点
        judge_node = CompareAndJudgeNode()
        
        shared = {
            "level_info": mock_level_info,
            "standard_code": mock_standard_code,
            "user_code": user_code,
            "use_cache": True,
            "language": "chinese"
        }
        
        # 执行判断
        prep_res = judge_node.prep(shared)
        result = judge_node.exec(prep_res)
        
        # 输出结果
        print("\n📊 检查结果:")
        print(f"✅ 是否通过: {'是' if result['passed'] else '否'}")
        print(f"💬 反馈: {result['feedback']}")
        
        if result.get('suggestions'):
            print("\n💡 改进建议:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
        if result.get('praise'):
            print(f"\n🎉 鼓励: {result['praise']}")
        
        if result.get('detailed_analysis'):
            print("\n🔍 详细分析:")
            analysis = result['detailed_analysis']
            for key, value in analysis.items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_file_tree_parsing():
    """测试文件树解析功能"""
    
    print("\n🧪 测试文件树解析...")
    
    try:
        from agentflow.nodes import AnalyzeUserCodeNode
        
        # 模拟用户文件树
        mock_file_tree = {
            "type": "directory",
            "uri": "file:///project",
            "children": [
                {
                    "type": "file",
                    "uri": "file:///project/main.py",
                    "content": """def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
"""
                },
                {
                    "type": "file",
                    "uri": "file:///project/utils.py",
                    "content": """def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
                },
                {
                    "type": "directory",
                    "uri": "file:///project/tests",
                    "children": [
                        {
                            "type": "file",
                            "uri": "file:///project/tests/test_main.py",
                            "content": """import unittest
from main import hello

class TestMain(unittest.TestCase):
    def test_hello(self):
        # 这里应该测试hello函数
        pass
"""
                        }
                    ]
                }
            ]
        }
        
        # 创建分析节点
        analyze_node = AnalyzeUserCodeNode()
        
        shared = {"user_file_tree": mock_file_tree}
        
        # 执行分析
        prep_res = analyze_node.prep(shared)
        result = analyze_node.exec(prep_res)
        
        print("\n📁 解析的文件:")
        for file_path, content in result.items():
            print(f"  📄 {file_path} ({len(content)} 字符)")
            # 显示内容预览
            preview = content[:100].replace('\n', ' ')
            if len(content) > 100:
                preview += "..."
            print(f"     内容预览: {preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ 文件树解析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_request_format():
    """测试API请求格式"""
    
    print("\n🧪 测试API请求格式...")
    
    # 模拟API请求数据
    api_request = {
        "level_id": 1,
        "course_id": 1,
        "user_file_tree": {
            "type": "directory",
            "uri": "file:///project",
            "children": [
                {
                    "type": "file",
                    "uri": "file:///project/solution.py",
                    "content": """# 用户的解决方案
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# 测试
for i in range(10):
    print(f"fibonacci({i}) = {fibonacci(i)}")
"""
                }
            ]
        }
    }
    
    print("📤 API请求格式:")
    print(json.dumps(api_request, indent=2, ensure_ascii=False))
    
    # 验证请求格式
    required_fields = ["level_id", "course_id", "user_file_tree"]
    missing_fields = [field for field in required_fields if field not in api_request]
    
    if missing_fields:
        print(f"❌ 缺少必要字段: {missing_fields}")
        return False
    else:
        print("✅ API请求格式正确")
        return True


def main():
    """运行所有测试"""
    
    print("🚀 开始测试关卡检查流程")
    print("=" * 60)
    
    tests = [
        ("简化检查流程", test_simple_check),
        ("文件树解析", test_file_tree_parsing),
        ("API请求格式", test_api_request_format)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 运行测试: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📋 测试总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！检查流程已准备就绪。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)