import os
import tempfile
from dotenv import load_dotenv
from flow import create_flow
from utils.crawl_github_files import clone_repository, filter_and_read_files, get_exclude_patterns, get_file_patterns, reset_to_commit
# Load environment variables from .env file
load_dotenv()

def main():
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test3_call"
    
    # 通用调用方式示例
    print("=== 通用调用方式示例 ===")
    
    # 方式1: 使用预定义模式
    print("\n1. 使用预定义模式 - 只获取Python文件:")
    tmpdirname = tempfile.mkdtemp()
    repo = clone_repository(repo_url, tmpdirname)
    reset_to_commit(repo, 3)
    result = filter_and_read_files(
            tmpdirname,
            max_file_size=1 * 1024 * 1024,
            include_patterns=get_file_patterns("code"),  # 预定义Python模式
            exclude_patterns=get_exclude_patterns("common")  # 排除常见无用文件
    )
    # 显示文件列表
    files = result["files"]
    print("文件列表:")
    print(type(files))
    for file_path in sorted(files.keys())[:10]:  # 只显示前10个
        file_content = files[file_path]
        print(f"  {file_path}")
        # 显示文件内容（前200字符 + 省略号）
        preview = file_content[:200].replace('\n', ' ')  # 去除换行便于显示
        if len(file_content) > 200:
            preview += " [...]"
        print(f"内容预览: {preview}")
    if len(files) > 10:
        print(f"  ... 还有 {len(files) - 10} 个文件")
    shared = {
        "files": files,
        "language":"中文",
        "use_cache":True,
        "max_abstraction_num":5,
        "project_name": repo_url, 
    }
    
    
    flow = create_flow()
    flow.run(shared)
    
    # # Results are in shared["analysis"]
    
if __name__ == "__main__":
    main()
