#!/usr/bin/env python3
"""
测试共享目录功能
"""

import threading
import time
from agentflow.utils.crawl_github_files import (
    crawl_github_files,
    get_repository_commits,
    get_temp_directory_info,
    cleanup_temp_directories,
    get_repo_hash
)

def test_shared_directory(repo_url: str, thread_id: int, operation: str):
    """测试共享目录功能"""
    print(f"线程 {thread_id} 开始执行 {operation}...")
    
    try:
        if operation == "crawl":
            result = crawl_github_files(
                repo_url=repo_url,
                commit_index=1,
                include_patterns={"*.py", "*.md"},
                max_file_size=500 * 1024
            )
            files_count = len(result.get("files", {}))
            print(f"线程 {thread_id} ({operation}) 完成，获取了 {files_count} 个文件")
            
        elif operation == "commits":
            result = get_repository_commits(repo_url, max_commits=5)
            commits_count = len(result.get("commits", []))
            print(f"线程 {thread_id} ({operation}) 完成，获取了 {commits_count} 个提交")
            
        if result.get("error") or result.get("stats", {}).get("error"):
            error = result.get("error") or result.get("stats", {}).get("error")
            print(f"线程 {thread_id} ({operation}) 出错: {error}")
            
    except Exception as e:
        print(f"线程 {thread_id} ({operation}) 异常: {e}")

def main():
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test2.git"
    repo_hash = get_repo_hash(repo_url)
    
    print("=== 共享目录功能测试 ===")
    print(f"仓库URL: {repo_url}")
    print(f"仓库哈希: {repo_hash}")
    print(f"预期共享目录名: shared_repo_{repo_hash}")
    
    # 清理旧的临时目录
    print("\n1. 清理旧的临时目录...")
    cleanup_temp_directories(max_age_hours=0)
    
    # 显示初始状态
    print("\n2. 初始临时目录状态:")
    info = get_temp_directory_info()
    print(f"   基础目录: {info['base_dir']}")
    print(f"   目录数量: {info['total_directories']}")
    
    # 第一轮测试：多个线程执行相同操作
    print("\n3. 第一轮测试：3个线程同时爬取文件...")
    threads = []
    start_time = time.time()
    
    for i in range(3):
        thread = threading.Thread(target=test_shared_directory, args=(repo_url, i+1, "crawl"))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    first_round_time = time.time() - start_time
    print(f"第一轮完成，耗时: {first_round_time:.2f} 秒")
    
    # 检查目录状态
    print("\n4. 第一轮后临时目录状态:")
    info = get_temp_directory_info()
    print(f"   目录数量: {info['total_directories']}")
    print(f"   总大小: {info['total_size_mb']} MB")
    
    if info['directories']:
        for dir_info in info['directories']:
            if 'error' not in dir_info:
                print(f"   - {dir_info['name']}: {dir_info['size_mb']} MB")
    
    # 第二轮测试：混合操作
    print("\n5. 第二轮测试：混合操作（2个爬取 + 2个获取提交）...")
    threads = []
    start_time = time.time()
    
    # 2个爬取线程
    for i in range(2):
        thread = threading.Thread(target=test_shared_directory, args=(repo_url, i+1, "crawl"))
        threads.append(thread)
        thread.start()
    
    # 2个获取提交线程
    for i in range(2):
        thread = threading.Thread(target=test_shared_directory, args=(repo_url, i+3, "commits"))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    second_round_time = time.time() - start_time
    print(f"第二轮完成，耗时: {second_round_time:.2f} 秒")
    
    # 最终状态
    print("\n6. 最终临时目录状态:")
    info = get_temp_directory_info()
    print(f"   目录数量: {info['total_directories']}")
    print(f"   总大小: {info['total_size_mb']} MB")
    
    if info['directories']:
        print("\n   详细目录信息:")
        for dir_info in info['directories']:
            if 'error' not in dir_info:
                print(f"   - {dir_info['name']}: {dir_info['size_mb']} MB, {dir_info['age_hours']:.2f} 小时前")
    
    # 验证是否使用了共享目录
    shared_dir_found = False
    if info['directories']:
        for dir_info in info['directories']:
            if dir_info['name'] == f"shared_repo_{repo_hash}":
                shared_dir_found = True
                print(f"\n✅ 找到共享目录: {dir_info['name']} ({dir_info['size_mb']} MB)")
                break
    
    if not shared_dir_found:
        print(f"\n❌ 未找到预期的共享目录: shared_repo_{repo_hash}")
    
    print(f"\n7. 性能对比:")
    print(f"   第一轮（首次克隆）: {first_round_time:.2f} 秒")
    print(f"   第二轮（复用目录）: {second_round_time:.2f} 秒")
    if first_round_time > 0:
        improvement = ((first_round_time - second_round_time) / first_round_time) * 100
        print(f"   性能提升: {improvement:.1f}%")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()