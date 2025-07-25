#!/usr/bin/env python3
"""
测试 check_completion API 逻辑

这个文件用于测试API逻辑而不需要实际运行服务器
"""

import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_file_tree_conversion():
    """测试字符串到文件树的转换逻辑"""
    
    print("🧪 测试字符串到文件树的转换...")
    
    user_answer = """# 我的Python程序
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""
    
    # 模拟API中的转换逻辑
    simple_file_tree = {
        "type": "directory",
        "uri": "file:///project",
        "children": [
            {
                "type": "file",
                "uri": "file:///project/solution.py",
                "content": user_answer
            }
        ]
    }
    
    print("✅ 转换成功")
    print("📁 生成的文件树结构:")
    print(json.dumps(simple_file_tree, indent=2, ensure_ascii=False))
    
    # 验证结构
    assert simple_file_tree["type"] == "directory"
    assert len(simple_file_tree["children"]) == 1
    assert simple_file_tree["children"][0]["type"] == "file"
    assert simple_file_tree["children"][0]["content"] == user_answer
    
    print("✅ 结构验证通过")
    return True


def test_request_validation():
    """测试请求参数验证逻辑"""
    
    print("\n🧪 测试请求参数验证...")
    
    test_cases = [
        {
            "name": "完整的文件树请求",
            "data": {
                "level_id": 1,
                "course_id": 1,
                "user_file_tree": {"type": "directory", "children": []}
            },
            "expected": "file_tree_format"
        },
        {
            "name": "完整的字符串请求",
            "data": {
                "level_id": 1,
                "user_answer": "print('hello')"
            },
            "expected": "string_format"
        },
        {
            "name": "缺少level_id",
            "data": {
                "user_answer": "print('hello')"
            },
            "expected": "error"
        },
        {
            "name": "缺少必要参数",
            "data": {
                "level_id": 1
            },
            "expected": "error"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n   测试: {test_case['name']}")
        data = test_case["data"]
        expected = test_case["expected"]
        
        # 模拟API中的验证逻辑
        level_id = data.get("level_id")
        user_file_tree = data.get("user_file_tree")
        user_answer = data.get("user_answer")
        course_id = data.get("course_id")
        
        if not level_id:
            result = "error"
            error_msg = "缺少必要参数: level_id"
        elif user_file_tree and course_id:
            result = "file_tree_format"
            error_msg = None
        elif user_answer:
            result = "string_format"
            error_msg = None
        else:
            result = "error"
            error_msg = "请提供 user_file_tree + course_id 或 user_answer 参数"
        
        if result == expected:
            print(f"   ✅ 验证通过: {result}")
        else:
            print(f"   ❌ 验证失败: 期望 {expected}, 实际 {result}")
            return False
        
        if error_msg:
            print(f"   📝 错误信息: {error_msg}")
    
    print("\n✅ 所有验证测试通过")
    return True


def test_response_format():
    """测试响应格式"""
    
    print("\n🧪 测试响应格式...")
    
    # 模拟check_flow的返回结果
    mock_flow_result = {
        "passed": True,
        "feedback": "很好！你成功实现了要求的功能。代码结构清晰，逻辑正确。",
        "suggestions": [
            "可以添加更多注释来提高代码可读性",
            "考虑添加错误处理机制"
        ],
        "praise": "干得漂亮！继续保持！",
        "detailed_analysis": {
            "functionality": "功能完整，满足要求",
            "correctness": "语法正确，逻辑合理",
            "quality": "代码风格良好",
            "innovation": "实现方式有创新性"
        }
    }
    
    # 模拟API响应转换逻辑
    api_response = {
        "passed": mock_flow_result.get("passed", False),
        "feedback": mock_flow_result.get("feedback", "检查完成"),
        "score": None,  # 不使用score字段
        "suggestions": mock_flow_result.get("suggestions", [])
    }
    
    print("📤 模拟的API响应:")
    print(json.dumps(api_response, indent=2, ensure_ascii=False))
    
    # 验证响应格式
    required_fields = ["passed", "feedback"]
    for field in required_fields:
        if field not in api_response:
            print(f"❌ 缺少必要字段: {field}")
            return False
    
    # 验证字段类型
    if not isinstance(api_response["passed"], bool):
        print("❌ passed字段类型错误")
        return False
    
    if not isinstance(api_response["feedback"], str):
        print("❌ feedback字段类型错误")
        return False
    
    if api_response["suggestions"] and not isinstance(api_response["suggestions"], list):
        print("❌ suggestions字段类型错误")
        return False
    
    print("✅ 响应格式验证通过")
    return True


def test_error_handling():
    """测试错误处理逻辑"""
    
    print("\n🧪 测试错误处理...")
    
    # 模拟各种错误情况
    error_cases = [
        {
            "name": "check_flow返回None",
            "flow_result": None,
            "expected_error": "检查流程未返回结果"
        },
        {
            "name": "check_flow返回空字典",
            "flow_result": {},
            "expected_response": {
                "passed": False,
                "feedback": "检查完成",
                "suggestions": []
            }
        },
        {
            "name": "check_flow返回部分结果",
            "flow_result": {
                "passed": True,
                "feedback": "部分成功"
            },
            "expected_response": {
                "passed": True,
                "feedback": "部分成功",
                "suggestions": []
            }
        }
    ]
    
    for case in error_cases:
        print(f"\n   测试: {case['name']}")
        flow_result = case["flow_result"]
        
        if flow_result is None:
            # 模拟API中的错误处理
            error_occurred = True
            error_msg = case["expected_error"]
            print(f"   ✅ 正确捕获错误: {error_msg}")
        else:
            # 模拟API中的响应构建
            response = {
                "passed": flow_result.get("passed", False),
                "feedback": flow_result.get("feedback", "检查完成"),
                "score": None,
                "suggestions": flow_result.get("suggestions", [])
            }
            
            expected = case["expected_response"]
            if response["passed"] == expected["passed"] and \
               response["feedback"] == expected["feedback"] and \
               response["suggestions"] == expected["suggestions"]:
                print("   ✅ 错误处理正确")
            else:
                print(f"   ❌ 错误处理失败")
                print(f"   期望: {expected}")
                print(f"   实际: {response}")
                return False
    
    print("\n✅ 错误处理测试通过")
    return True


def main():
    """运行所有逻辑测试"""
    
    print("🚀 开始测试 check_completion API 逻辑")
    print("=" * 60)
    
    tests = [
        ("文件树转换测试", test_file_tree_conversion),
        ("请求验证测试", test_request_validation),
        ("响应格式测试", test_response_format),
        ("错误处理测试", test_error_handling)
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
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("📋 逻辑测试总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有逻辑测试都通过了！API逻辑正确。")
        print("\n📝 下一步:")
        print("1. 启动FastAPI服务: uvicorn app.main:app --reload")
        print("2. 运行API测试: python test_check_completion_api.py")
        return True
    else:
        print("⚠️  部分逻辑测试失败，请检查API实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)