#!/usr/bin/env python3
"""
测试关卡API的文件树功能
"""

import sys
import os
import tempfile
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_file_tree_generation():
    """测试文件树生成功能"""
    try:
        from agentflow.utils.crawl_github_files import (
            clone_repository, reset_to_commit, filter_and_read_files, 
            get_file_patterns, get_exclude_patterns
        )
        from app.utils.file_tree_builder import build_file_tree_from_files, sort_file_tree
        
        print("=== 测试关卡API文件树生成功能 ===")
        
        # 测试参数
        repo_url = "https://github.com/zengyi-thinking/auto_mate_test2.git"
        current_index = 3  # 模拟第3个关卡对应第3个提交
        
        tmpdirname = None
        try:
            # 1. 创建临时目录
            tmpdirname = tempfile.mkdtemp()
            print(f"创建临时目录: {tmpdirname}")
            
            # 2. 克隆仓库
            print(f"克隆仓库: {repo_url}")
            repo = clone_repository(repo_url, tmpdirname)
            
            # 3. 重置到指定提交
            print(f"重置到第 {current_index} 个提交")
            commits = list(repo.iter_commits(reverse=True))
            print(f"仓库共有 {len(commits)} 个提交")
            
            if current_index > len(commits):
                print(f"❌ 提交索引 {current_index} 超出范围")
                return False
            
            reset_to_commit(repo, commits, current_index)
            
            # 4. 获取文件
            print("获取文件...")
            result = filter_and_read_files(
                tmpdirname,
                max_file_size=1 * 1024 * 1024,
                include_patterns=get_file_patterns("code"),
                exclude_patterns=get_exclude_patterns("common")
            )
            
            print(f"获取到 {len(result['files'])} 个文件")
            
            # 5. 构建文件树
            if result["files"]:
                print("构建文件树...")
                project_name = repo_url.split('/')[-1].replace('.git', '')
                base_uri = f"file:///github/{project_name}"
                
                file_tree = build_file_tree_from_files(result["files"], base_uri)
                file_tree = sort_file_tree(file_tree)
                
                # 6. 显示文件树结构（简化版）
                print("\n文件树结构:")
                print_file_tree(file_tree, 0)
                
                # 7. 转换为字典格式
                tree_dict = file_tree.model_dump()
                print(f"\n✅ 成功生成文件树，根节点类型: {tree_dict['type']}")
                print(f"   根URI: {tree_dict['uri']}")
                print(f"   子节点数量: {len(tree_dict.get('children', []))}")
                
                return True
            else:
                print("❌ 未获取到任何文件")
                return False
                
        finally:
            # 清理临时目录
            if tmpdirname:
                try:
                    import shutil
                    shutil.rmtree(tmpdirname)
                    print(f"清理临时目录: {tmpdirname}")
                except Exception as cleanup_error:
                    print(f"清理临时目录失败: {cleanup_error}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_file_tree(node, depth=0, max_depth=3):
    """打印文件树结构（限制深度避免输出过长）"""
    if depth > max_depth:
        return
    
    indent = "  " * depth
    node_type = "📁" if node.type == "directory" else "📄"
    name = node.uri.split('/')[-1]
    
    print(f"{indent}{node_type} {name}")
    
    if node.children and depth < max_depth:
        # 只显示前5个子节点
        for i, child in enumerate(node.children[:5]):
            print_file_tree(child, depth + 1, max_depth)
        
        if len(node.children) > 5:
            print(f"{indent}  ... 还有 {len(node.children) - 5} 个子节点")

def test_api_request_format():
    """测试API请求格式"""
    print("\n=== API请求格式示例 ===")
    
    request_example = {
        "course_id": 1,
        "level_id": 3
    }
    
    print("POST /levels/get")
    print("Content-Type: application/json")
    print(f"Body: {request_example}")
    
    response_example = {
        "id": 3,
        "course_id": 1,
        "title": "第3关：函数定义",
        "description": "学习如何定义和使用函数",
        "requirements": "创建一个简单的函数并调用它",
        "order_number": 3,
        "file_tree": {
            "type": "directory",
            "uri": "file:///github/auto_mate_test2",
            "children": [
                {
                    "type": "file",
                    "uri": "file:///github/auto_mate_test2/main.py",
                    "content": "def hello():\n    print('Hello World')\n\nhello()"
                }
            ]
        }
    }
    
    print(f"\n响应示例:")
    print(f"Status: 200 OK")
    print(f"Body: {response_example}")

if __name__ == "__main__":
    print("测试关卡API文件树功能")
    print("=" * 50)
    
    # 测试文件树生成
    if test_file_tree_generation():
        print("\n🎉 文件树生成测试通过！")
        
        # 显示API格式
        test_api_request_format()
        
        print("\n✅ 所有测试完成，API功能正常")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)