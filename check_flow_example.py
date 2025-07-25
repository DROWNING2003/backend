#!/usr/bin/env python3
"""
关卡检查流程使用示例

这个示例展示了如何使用 check_flow 来检查用户提交的代码是否满足关卡要求。
"""

import tempfile
from agentflow.flow import check_flow


def example_user_file_tree():
    """
    模拟用户提交的文件树结构
    这通常来自前端IDE的文件树数据
    """
    return {
        "type": "directory",
        "uri": "file:///project",
        "children": [
            {
                "type": "file",
                "uri": "file:///project/main.py",
                "content": """# 用户提交的代码示例
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
"""
            },
            {
                "type": "file", 
                "uri": "file:///project/utils.py",
                "content": """# 工具函数
def add_numbers(a, b):
    return a + b

def multiply_numbers(a, b):
    return a * b
"""
            }
        ]
    }


def run_check_example():
    """运行检查流程示例"""
    
    # 准备共享数据
    shared = {
        # 关卡和课程信息
        "level_id": 90,
        "course_id": 21,
        
        # 用户提交的文件树
        "user_file_tree": example_user_file_tree(),
        
        # 配置选项
        "language": "chinese",
        "use_cache": True
    }
    
    try:
        print("开始执行关卡检查流程...")
        
        # 创建并运行检查流程
        flow = check_flow()
        flow.run(shared)
        
        # 获取检查结果
        result = shared.get("judgment_result")
        
        if result:
            print("\n=== 检查结果 ===")
            print(f"是否通过: {'✅ 通过' if result['passed'] else '❌ 未通过'}")
            print(f"反馈: {result['feedback']}")
            
            if result.get('suggestions'):
                print("\n改进建议:")
                for i, suggestion in enumerate(result['suggestions'], 1):
                    print(f"  {i}. {suggestion}")
            
            if result.get('praise'):
                print(f"\n鼓励: {result['praise']}")
            
            if result.get('detailed_analysis'):
                print("\n详细分析:")
                analysis = result['detailed_analysis']
                for key, value in analysis.items():
                    print(f"  {key}: {value}")
        else:
            print("❌ 未获取到检查结果")
            
    except Exception as e:
        print(f"❌ 检查流程执行失败: {str(e)}")
        
        # 打印调试信息
        print("\n调试信息:")
        for key, value in shared.items():
            if key != "user_file_tree":  # 文件树太长，不打印
                print(f"  {key}: {type(value)} - {str(value)[:100]}...")


def run_simple_check():
    """运行简化的检查示例（不依赖数据库）"""
    
    print("运行简化检查示例...")
    
    # 模拟关卡信息（通常从数据库获取）
    mock_level_info = {
        "id": 1,
        "title": "Python基础 - Hello World",
        "description": "学习Python的基本语法，编写第一个程序",
        "requirements": "创建一个输出'Hello, World!'的Python程序",
        "order_number": 1
    }
    
    mock_course_info = {
        "id": 1,
        "title": "Python入门课程",
        "git_url": "https://github.com/example/python-basics.git"
    }
    
    # 模拟标准答案代码
    mock_standard_code = {
        "main.py": """print("Hello, World!")""",
        "README.md": """# Python Hello World
这是一个简单的Python Hello World程序。
"""
    }
    
    # 用户提交的代码
    user_code = {
        "main.py": """# 我的第一个Python程序
def hello():
    print("Hello, World!")

hello()
""",
        "test.py": """# 测试文件
import main
"""
    }
    
    # 直接使用CompareAndJudgeNode进行对比
    from agentflow.nodes import CompareAndJudgeNode
    
    judge_node = CompareAndJudgeNode()
    
    shared = {
        "level_info": mock_level_info,
        "standard_code": mock_standard_code,
        "user_code": user_code,
        "use_cache": True,
        "language": "chinese"
    }
    
    try:
        # 准备数据
        prep_res = judge_node.prep(shared)
        
        # 执行判断
        result = judge_node.exec(prep_res)
        
        print("\n=== 简化检查结果 ===")
        print(f"是否通过: {'✅ 通过' if result['passed'] else '❌ 未通过'}")
        print(f"反馈: {result['feedback']}")
        
        if result.get('suggestions'):
            print("\n改进建议:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"  {i}. {suggestion}")
        
    except Exception as e:
        print(f"❌ 简化检查失败: {str(e)}")


def test_flow_creation():
    """测试流程创建"""
    
    print("测试流程创建...")
    
    try:
        # 创建流程
        flow = check_flow()
        print(f"✅ 流程创建成功: {type(flow)}")
        
        # 检查起始节点
        start_node = flow.start
        print(f"✅ 起始节点: {type(start_node).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ 流程创建失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("关卡检查流程示例")
    print("=" * 50)
    
    # 首先测试流程创建
    if not test_flow_creation():
        print("流程创建失败，退出")
        exit(1)
    
    # 选择运行哪个示例
    print("\n选择运行模式:")
    print("1. 完整流程（需要数据库和Git仓库）")
    print("2. 简化检查（仅测试AI判断功能）")
    
    choice = input("请选择 (1 或 2，默认2): ").strip()
    
    if choice == "1":
        print("\n=== 运行完整流程 ===")
        run_check_example()
    else:
        print("\n=== 运行简化检查 ===")
        run_simple_check()