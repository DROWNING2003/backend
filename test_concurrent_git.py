#!/usr/bin/env python3
"""
测试git操作的并发安全性
"""

import threading
import time
from agentflow.utils.crawl_github_files import (
    crawl_github_files,
    get_repository_commits,
    cleanup_temp_directories,
    get_temp_directory_info
)

def test_concurrent_clone(repo_url: str, thread_id: int):
    """测试并发克隆"""
    print(f"线程 {thread_id} 开始克隆仓库...")
    try:
        result = crawl_github_files(
            repo_url=repo_url,
            commit_index=1,
            include_patterns={"*.py", "*.md"},
            max_file_size=500 * 1024  # 500KB
        )
        
        files_count = len(result.get("files", {}))
        print(f"线程 {thread_id} 完成，获取了 {files_count} 个文件")
        
        if result.get("stats", {}).get("error"):
            print(f"线程 {thread_id} 出错: {result['stats']['error']}")
        
    except Exception as e:
        print(f"线程 {thread_id} 异常: {e}")

def test_concurrent_commits(repo_url: str, thread_id: int):
    """测试并发获取提交列表"""
    print(f"线程 {thread_id} 开始获取提交列表...")
    try:
        result = get_repository_commits(repo_url, max_commits=10)
        
        commits_count = len(result.get("commits", []))
        print(f"线程 {thread_id} 完成，获取了 {commits_count} 个提交")
        
        if result.get("error"):
            print(f"线程 {thread_id} 出错: {result['error']}")
            
    except Exception as e:
        print(f"线程 {thread_id} 异常: {e}")

def main():
    # 测试仓库URL
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test2.git"
    
    print("=== 并发安全测试 ===")
    
    # 清理旧的临时目录
    print("\n1. 清理旧的临时目录...")
    cleanup_temp_directories(max_age_hours=0)  # 清理所有
    
    # 显示初始状态
    print("\n2. 初始临时目录状态:")
    info = get_temp_directory_info()
    print(f"   基础目录: {info['base_dir']}")
    print(f"   目录数量: {info['total_directories']}")
    print(f"   总大小: {info['total_size_mb']} MB")
    
    # 测试并发克隆
    print("\n3. 测试并发克隆 (5个线程)...")
    threads = []
    start_time = time.time()
    
    for i in range(5):
        thread = threading.Thread(target=test_concurrent_clone, args=(repo_url, i+1))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    clone_time = time.time() - start_time
    print(f"并发克隆完成，耗时: {clone_time:.2f} 秒")
    
    # 显示中间状态
    print("\n4. 克隆后临时目录状态:")
    info = get_temp_directory_info()
    print(f"   目录数量: {info['total_directories']}")
    print(f"   总大小: {info['total_size_mb']} MB")
    
    # 测试并发获取提交
    print("\n5. 测试并发获取提交列表 (3个线程)...")
    threads = []
    start_time = time.time()
    
    for i in range(3):
        thread = threading.Thread(target=test_concurrent_commits, args=(repo_url, i+1))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    commits_time = time.time() - start_time
    print(f"并发获取提交完成，耗时: {commits_time:.2f} 秒")
    
    # 显示最终状态
    print("\n6. 最终临时目录状态:")
    info = get_temp_directory_info()
    print(f"   目录数量: {info['total_directories']}")
    print(f"   总大小: {info['total_size_mb']} MB")
    
    # 显示详细信息
    if info['directories']:
        print("\n   详细目录信息:")
        for dir_info in info['directories']:
            if 'error' not in dir_info:
                print(f"   - {dir_info['name']}: {dir_info['size_mb']} MB, {dir_info['age_hours']:.2f} 小时前")
            else:
                print(f"   - {dir_info['name']}: 错误 - {dir_info['error']}")
    
    # 清理测试产生的临时文件
    print("\n7. 清理测试临时文件...")
    cleanup_temp_directories(max_age_hours=0)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()