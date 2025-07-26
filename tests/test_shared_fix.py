#!/usr/bin/env python3
"""
测试共享目录修复是否有效
"""

from agentflow.utils.crawl_github_files import (
    get_or_clone_repository,
    get_temp_directory_info,
    cleanup_temp_directories,
    get_repo_hash
)

def test_shared_directory_fix():
    """测试共享目录修复"""
    
    # 测试不同的仓库
    repos = [
        "https://github.com/zengyi-thinking/auto_mate_test2.git",
        "https://github.com/zengyi-thinking/auto_mate_test3_call.git",
        "https://github.com/zengyi-thinking/auto_mate_test4_complex.git"
    ]
    
    print("=== 测试共享目录修复 ===")
    
    # 清理旧目录
    cleanup_temp_directories(max_age_hours=0)
    
    for i, repo_url in enumerate(repos, 1):
        print(f"\n{i}. 测试仓库: {repo_url}")
        repo_hash = get_repo_hash(repo_url)
        print(f"   预期共享目录: shared_repo_{repo_hash}")
        
        # 第一次调用
        print("   第一次调用...")
        try:
            repo1 = get_or_clone_repository(repo_url)
            print(f"   ✅ 成功，工作目录: {repo1.working_dir}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            continue
        
        # 第二次调用（应该复用）
        print("   第二次调用...")
        try:
            repo2 = get_or_clone_repository(repo_url)
            print(f"   ✅ 成功，工作目录: {repo2.working_dir}")
            
            # 验证是否使用了相同目录
            if repo1.working_dir == repo2.working_dir:
                print("   ✅ 确认使用了相同的共享目录")
            else:
                print("   ❌ 警告：使用了不同的目录")
                
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    # 显示最终目录状态
    print(f"\n4. 最终目录状态:")
    info = get_temp_directory_info()
    print(f"   目录数量: {info['total_directories']}")
    print(f"   总大小: {info['total_size_mb']} MB")
    
    if info['directories']:
        print("\n   目录列表:")
        for dir_info in info['directories']:
            if 'error' not in dir_info:
                is_shared = dir_info['name'].startswith('shared_repo_')
                status = "✅ 共享目录" if is_shared else "❌ 非共享目录"
                print(f"   - {dir_info['name']}: {dir_info['size_mb']} MB ({status})")
    
    print(f"\n=== 测试完成 ===")

if __name__ == "__main__":
    test_shared_directory_fix()