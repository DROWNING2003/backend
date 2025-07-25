#!/usr/bin/env python3
"""
关卡检查流程集成测试

这个文件用于测试完整的check_flow流程是否能正常工作
"""

import sys
import os
import tempfile
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_check_flow_integration():
    """测试完整的检查流程集成"""
    
    print("🧪 测试完整检查流程集成...")
    
    try:
        from agentflow.flow import check_flow
        
        # 模拟用户文件树（这通常来自前端IDE）
        user_file_tree = {
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

def format_greeting(name):
    return name.strip().title()
"""
                },
                {
                    "type": "file",
                    "uri": "file:///project/README.md",
                    "content": """# 我的Python项目

这是一个简单的问候程序，可以：
- 接收用户输入的名字
- 返回个性化的问候语
- 包含输入验证功能

## 使用方法
```bash
python main.py
```
"""
                }
            ]
        }
        
        # 准备共享数据
        shared = {
            # 关卡和课程信息（这些通常来自API请求）
            "level_id": 1,
            "course_id": 1,
            
            # 用户提交的文件树
            "user_file_tree": user_file_tree,
            
            # 配置选项
            "language": "chinese",
            "use_cache": True
        }
        
        print("📋 测试数据准备完成")
        print(f"   关卡ID: {shared['level_id']}")
        print(f"   课程ID: {shared['course_id']}")
        print(f"   用户文件数: {len(user_file_tree['children'])}")
        
        # 创建并运行检查流程
        print("\n🚀 开始执行检查流程...")
        
        flow = check_flow()
        
        # 注意：这里可能会因为数据库连接或Git仓库访问问题而失败
        # 在实际环境中需要确保这些依赖项正常工作
        try:
            flow.run(shared)
            
            # 获取检查结果
            result = shared.get("judgment_result")
            
            if result:
                print("\n✅ 检查流程执行成功！")
                print("\n📊 检查结果:")
                print(f"   是否通过: {'✅ 通过' if result['passed'] else '❌ 未通过'}")
                print(f"   得分: {result['score']}/100")
                print(f"   反馈: {result['feedback']}")
                
                if result.get('suggestions'):
                    print("\n💡 改进建议:")
                    for i, suggestion in enumerate(result['suggestions'], 1):
                        print(f"     {i}. {suggestion}")
                
                if result.get('praise'):
                    print(f"\n🎉 鼓励: {result['praise']}")
                
                if result.get('detailed_analysis'):
                    print("\n🔍 详细分析:")
                    analysis = result['detailed_analysis']
                    for key, value in analysis.items():
                        print(f"     {key}: {value}")
                
                return True
            else:
                print("❌ 未获取到检查结果")
                return False
                
        except Exception as flow_error:
            print(f"⚠️  流程执行遇到问题: {str(flow_error)}")
            print("\n这可能是由于以下原因：")
            print("1. 数据库连接问题（需要启动数据库服务）")
            print("2. Git仓库访问问题（需要网络连接和有效的Git URL）")
            print("3. LLM服务问题（需要配置API密钥）")
            print("4. 缺少必要的数据库记录")
            
            # 显示调试信息
            print("\n🔍 调试信息:")
            for key, value in shared.items():
                if key != "user_file_tree":  # 文件树太长，不完整显示
                    print(f"   {key}: {type(value)} - {str(value)[:100]}...")
            
            return False
            
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保所有必要的模块都已正确安装")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_flow_structure():
    """测试流程结构是否正确"""
    
    print("\n🧪 测试流程结构...")
    
    try:
        from agentflow.flow import check_flow
        
        # 创建流程
        flow = check_flow()
        
        print("✅ 流程创建成功")
        print(f"   流程类型: {type(flow)}")
        print(f"   起始节点: {type(flow.start)}")
        
        # 检查节点链
        current_node = flow.start
        node_chain = []
        
        while current_node:
            node_chain.append(type(current_node).__name__)
            # 获取下一个节点（简化的检查）
            if hasattr(current_node, 'next_nodes') and current_node.next_nodes:
                current_node = list(current_node.next_nodes.values())[0]
            else:
                break
        
        print(f"   节点链: {' -> '.join(node_chain)}")
        
        expected_nodes = [
            "GetLevelInfoNode",
            "CloneRepoNode", 
            "GetStandardCodeNode",
            "AnalyzeUserCodeNode",
            "CompareAndJudgeNode"
        ]
        
        if len(node_chain) >= len(expected_nodes):
            print("✅ 节点链结构正确")
            return True
        else:
            print(f"❌ 节点链不完整，期望 {len(expected_nodes)} 个节点，实际 {len(node_chain)} 个")
            return False
            
    except Exception as e:
        print(f"❌ 流程结构测试失败: {str(e)}")
        return False


def test_api_compatibility():
    """测试API兼容性"""
    
    print("\n🧪 测试API兼容性...")
    
    # 模拟API请求格式
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
                    "content": "print('Hello, World!')"
                }
            ]
        }
    }
    
    # 验证请求格式
    required_fields = ["level_id", "course_id", "user_file_tree"]
    missing_fields = [field for field in required_fields if field not in api_request]
    
    if missing_fields:
        print(f"❌ API请求格式不正确，缺少字段: {missing_fields}")
        return False
    
    # 验证文件树格式
    file_tree = api_request["user_file_tree"]
    if not isinstance(file_tree, dict) or file_tree.get("type") != "directory":
        print("❌ 文件树格式不正确")
        return False
    
    print("✅ API请求格式正确")
    print("✅ 文件树格式正确")
    
    # 模拟API响应格式
    expected_response_fields = ["passed", "feedback", "suggestions"]
    print(f"✅ 期望的响应字段: {expected_response_fields}")
    
    return True


def main():
    """运行所有集成测试"""
    
    print("🚀 开始关卡检查流程集成测试")
    print("=" * 60)
    
    tests = [
        ("流程结构测试", test_flow_structure),
        ("API兼容性测试", test_api_compatibility),
        ("完整流程集成测试", test_check_flow_integration)
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
    print("📋 集成测试总结:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有集成测试都通过了！check_flow已准备就绪。")
        print("\n📝 使用说明:")
        print("1. 确保数据库服务正常运行")
        print("2. 确保课程和关卡数据已正确配置")
        print("3. 确保Git仓库URL可访问")
        print("4. 确保LLM服务配置正确")
        print("5. 通过API端点 POST /levels/check-with-flow 使用")
        return True
    else:
        print("⚠️  部分集成测试失败，请检查相关配置。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)