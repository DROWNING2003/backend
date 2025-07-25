#!/usr/bin/env python3
"""
并发安全的Git操作示例
"""

from agentflow.utils.crawl_github_files import (
    crawl_github_files,
    get_repository_commits,
    get_repository_commit_changes,
    cleanup_temp_directories,
    get_temp_directory_info
)

def main():
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test2.git"
    
    print("=== 并发安全的Git操作示例 ===\n")
    
    # 1. 获取仓库提交列表
    print("1. 获取仓库提交列表...")
    commits_result = get_repository_commits(repo_url, max_commits=5)
    
    if commits_result.get("error"):
        print(f"   错误: {commits_result['error']}")
        return
    
    print(f"   找到 {commits_result['total_commits']} 个提交，显示前 {commits_result['showing']} 个:")
    for commit in commits_result["commits"]:
        print(f"   - {commit['index']}: {commit['short_hash']} - {commit['message']}")
    
    # 2. 获取特定提交的文件
    print(f"\n2. 获取第1个提交的文件...")
    files_result = crawl_github_files(
        repo_url=repo_url,
        commit_index=1,
        include_patterns={"*.py", "*.md", "*.txt"},
        max_file_size=100 * 1024  # 100KB
    )
    
    if files_result.get("stats", {}).get("error"):
        print(f"   错误: {files_result['stats']['error']}")
    else:
        files = files_result.get("files", {})
        print(f"   获取了 {len(files)} 个文件:")
        for file_path in sorted(files.keys()):
            content_size = len(files[file_path])
            print(f"   - {file_path} ({content_size} 字节)")
    
    # 3. 获取提交变化详情
    if commits_result["total_commits"] > 1:
        print(f"\n3. 获取第2个提交的变化详情...")
        changes_result = get_repository_commit_changes(repo_url, 2, include_diff_content=False)
        
        if changes_result.get("error"):
            print(f"   错误: {changes_result['error']}")
        else:
            commit_info = changes_result["commit_info"]
            summary = changes_result["summary"]
            print(f"   提交: {commit_info['hash'][:8]} - {commit_info['message']}")
            print(f"   变化统计:")
            print(f"   - 新增文件: {summary['files_added']}")
            print(f"   - 修改文件: {summary['files_modified']}")
            print(f"   - 删除文件: {summary['files_deleted']}")
            print(f"   - 新增行数: {summary['total_lines_added']}")
            print(f"   - 删除行数: {summary['total_lines_deleted']}")
    
    # 4. 显示临时目录使用情况
    print(f"\n4. 临时目录使用情况:")
    temp_info = get_temp_directory_info()
    print(f"   基础目录: {temp_info['base_dir']}")
    print(f"   目录数量: {temp_info['total_directories']}")
    print(f"   总大小: {temp_info['total_size_mb']} MB")
    
    # 5. 清理临时文件
    print(f"\n5. 清理临时文件...")
    cleanup_temp_directories(max_age_hours=0)  # 清理所有
    
    # 显示清理后状态
    temp_info_after = get_temp_directory_info()
    print(f"   清理后目录数量: {temp_info_after['total_directories']}")
    
    print(f"\n=== 示例完成 ===")

if __name__ == "__main__":
    main()