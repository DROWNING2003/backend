#!/usr/bin/env python3
"""
关卡API使用示例
展示如何使用修改后的关卡API获取文件树
"""

import json
import requests
from typing import Dict, Any

def example_api_call():
    """示例API调用"""
    
    # API端点
    base_url = "http://localhost:8000"  # 替换为你的实际API地址
    endpoint = f"{base_url}/levels/get"
    
    # 请求数据
    request_data = {
        "course_id": 1,
        "level_id": 3
    }
    
    print("=== 关卡API调用示例 ===")
    print(f"请求URL: {endpoint}")
    print(f"请求方法: POST")
    print(f"请求数据: {json.dumps(request_data, indent=2)}")
    
    try:
        # 发送请求
        response = requests.post(
            endpoint,
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 请求成功！")
            
            # 显示关卡基本信息
            print(f"\n关卡信息:")
            print(f"  ID: {data.get('id')}")
            print(f"  标题: {data.get('title')}")
            print(f"  描述: {data.get('description')}")
            print(f"  要求: {data.get('requirements')}")
            print(f"  顺序: {data.get('order_number')}")
            
            # 显示文件树信息
            file_tree = data.get('file_tree')
            if file_tree:
                print(f"\n文件树信息:")
                print(f"  根目录: {file_tree.get('uri')}")
                print(f"  类型: {file_tree.get('type')}")
                
                children = file_tree.get('children', [])
                print(f"  文件数量: {len(children)}")
                
                print(f"\n文件列表:")
                for i, child in enumerate(children[:5]):  # 只显示前5个
                    print(f"    {i+1}. {child.get('uri').split('/')[-1]} ({child.get('type')})")
                    if child.get('content') and len(child.get('content', '')) < 200:
                        print(f"       内容预览: {child.get('content')[:100]}...")
                
                if len(children) > 5:
                    print(f"    ... 还有 {len(children) - 5} 个文件")
            else:
                print("\n⚠️ 未获取到文件树信息")
                
        else:
            print("❌ 请求失败")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保API服务器正在运行")
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def print_file_tree_structure(node: Dict[str, Any], depth: int = 0, max_depth: int = 3):
    """打印文件树结构"""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    node_type = "📁" if node.get('type') == 'directory' else "📄"
    name = node.get('uri', '').split('/')[-1]
    
    print(f"{indent}{node_type} {name}")
    
    children = node.get('children', [])
    if children and depth < max_depth:
        for child in children[:10]:  # 限制显示数量
            print_file_tree_structure(child, depth + 1, max_depth)
        
        if len(children) > 10:
            print(f"{indent}  ... 还有 {len(children) - 10} 个子项")

def example_response_processing():
    """示例响应处理"""
    
    # 模拟API响应数据
    mock_response = {
        "id": 3,
        "course_id": 1,
        "title": "函数定义与调用",
        "description": "学习如何在Python中定义和调用函数",
        "requirements": "创建一个简单的函数并调用它，输出Hello World",
        "order_number": 3,
        "content": None,
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00",
        "course": {
            "id": 1,
            "title": "Python基础编程",
            "tag": "编程语言"
        },
        "file_tree": {
            "type": "directory",
            "uri": "file:///github/auto_mate_test2",
            "children": [
                {
                    "type": "file",
                    "uri": "file:///github/auto_mate_test2/hello_world.py",
                    "content": "# Python基础入门\n# 第一个Python程序\n\nprint(\"Hello, World!\")\nprint(\"欢迎来到Python编程世界！\")\n\n# 变量的使用\nname = \"Python\"\nversion = 3.9\n\nprint(f\"我正在学习 {name} {version}\")\n\n# 简单的计算\na = 10\nb = 20\nresult = a + b\n\nprint(f\"{a} + {b} = {result}\")"
                }
            ]
        }
    }
    
    print("\n=== 响应数据处理示例 ===")
    
    # 处理关卡信息
    print(f"关卡: {mock_response['title']}")
    print(f"课程: {mock_response['course']['title']}")
    print(f"要求: {mock_response['requirements']}")
    
    # 处理文件树
    file_tree = mock_response.get('file_tree')
    if file_tree:
        print(f"\n项目结构:")
        print_file_tree_structure(file_tree)
        
        # 提取文件内容
        def extract_files(node, files_dict=None):
            if files_dict is None:
                files_dict = {}
            
            if node.get('type') == 'file' and node.get('content'):
                file_path = node.get('uri', '').replace('file:///', '')
                files_dict[file_path] = node.get('content')
            
            for child in node.get('children', []):
                extract_files(child, files_dict)
            
            return files_dict
        
        files = extract_files(file_tree)
        print(f"\n提取的文件内容:")
        for file_path, content in files.items():
            print(f"\n文件: {file_path}")
            print("=" * 50)
            print(content)
            print("=" * 50)

def main():
    """主函数"""
    print("关卡API使用示例")
    print("=" * 50)
    
    print("\n选择操作:")
    print("1. 发送真实API请求（需要API服务器运行）")
    print("2. 演示响应数据处理")
    print("3. 退出")
    
    try:
        choice = input("\n请输入选择 (1-3): ").strip()
        
        if choice == "1":
            example_api_call()
        elif choice == "2":
            example_response_processing()
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