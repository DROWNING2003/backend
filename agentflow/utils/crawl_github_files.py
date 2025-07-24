# 导入必要的库
import os        # 用于操作系统相关功能
import tempfile  # 用于创建临时文件和目录
import git       # 用于Git仓库操作
import fnmatch   # 用于文件名模式匹配
from typing import Union, Set, Dict  # 类型提示

def clone_repository(repo_url: str, target_dir: str) -> git.Repo:
    """
    克隆Git仓库到指定目录
    
    参数:
        repo_url (str): Git仓库URL (SSH或HTTPS格式)
        target_dir (str): 目标目录路径
        
    返回:
        git.Repo: Git仓库对象
        
    异常:
        Exception: 克隆失败时抛出异常
    """
    print(f"克隆仓库 {repo_url} 到目录 {target_dir} ...")
    try:
        repo = git.Repo.clone_from(repo_url, target_dir)
        print("克隆成功！")
        return repo
    except Exception as e:
        print(f"克隆仓库出错: {e}")
        # 如果是SSH失败，尝试转换为HTTPS URL
        if "git@github.com:" in repo_url and ("Connection closed" in str(e) or "exit code(128)" in str(e)):
            https_url = repo_url.replace("git@github.com:", "https://github.com/")
            if not https_url.endswith('.git'):
                https_url += '.git'
            print(f"SSH连接失败，尝试使用HTTPS: {https_url}")
            try:
                repo = git.Repo.clone_from(https_url, target_dir)
                print("HTTPS克隆成功！")
                return repo
            except Exception as e2:
                print(f"HTTPS克隆也失败: {e2}")
                raise e2
        else:
            raise e

def reset_to_commit(repo: git.Repo, commit_index: int = None):
    """
    将仓库重置到指定的历史提交
    
    参数:
        repo (git.Repo): Git仓库对象
        commit_index (int, 可选): 提交索引，1表示最早的提交，2表示第二早的提交，以此类推
                                 如果为None，则保持当前状态
    """
    if commit_index is None:
        print("未指定提交索引，保持当前状态")
        return
        
    try:
        # 获取所有提交，按时间顺序排列（最早的在前）
        commits = list(repo.iter_commits(reverse=True))
        
        if commit_index < 1 or commit_index > len(commits):
            print(f"提交索引 {commit_index} 超出范围 (1-{len(commits)})")
            return
            
        target_commit = commits[commit_index - 1]
        print(f"重置到第 {commit_index} 个提交: {target_commit.hexsha[:8]} - {target_commit.message.strip()}")
        
        # 重置到指定提交
        repo.git.reset('--hard', target_commit.hexsha)
        print("重置成功！")
        
    except Exception as e:
        print(f"重置到提交失败: {e}")
        raise e

def filter_and_read_files(
    repo_dir: str,
    max_file_size: int = 1 * 1024 * 1024,  # 1 MB
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
) -> Dict:
    """
    根据模式过滤并读取文件
    
    参数:
        repo_dir (str): 仓库目录路径
        max_file_size (int, 可选): 下载文件的最大大小(字节，默认1MB)
        include_patterns (str或str集合, 可选): 包含文件的模式(如"*.py", {"*.md", "*.txt"})
        exclude_patterns (str或str集合, 可选): 排除文件的模式
        
    返回:
        dict: 包含文件和统计信息的字典
    """
    # 将单个模式转换为集合
    if include_patterns and isinstance(include_patterns, str):
        include_patterns = {include_patterns}
    if exclude_patterns and isinstance(exclude_patterns, str):
        exclude_patterns = {exclude_patterns}

    def should_include_file(file_path: str, file_name: str) -> bool:
        """根据模式判断是否应包含文件"""
        # 如果没有指定包含模式，则包含所有文件
        if not include_patterns:
            include_file = True
        else:
            # 检查文件是否匹配任何包含模式
            include_file = any(fnmatch.fnmatch(file_name, pattern) for pattern in include_patterns)

        # 如果指定了排除模式，检查是否应排除文件
        if exclude_patterns and include_file:
            # 如果文件匹配任何排除模式，则排除
            exclude_file = any(fnmatch.fnmatch(file_path, pattern) for pattern in exclude_patterns)
            return not exclude_file

        return include_file

    # 遍历目录
    files = {}
    skipped_files = []

    for root, dirs, filenames in os.walk(repo_dir):
        for filename in filenames:
            abs_path = os.path.join(root, filename)
            rel_path = os.path.relpath(abs_path, repo_dir)

            # 检查文件大小
            try:
                file_size = os.path.getsize(abs_path)
            except OSError:
                continue

            if file_size > max_file_size:
                skipped_files.append((rel_path, file_size))
                print(f"跳过 {rel_path}: 大小 {file_size} 超过限制 {max_file_size}")
                continue

            # 检查包含/排除模式
            if not should_include_file(rel_path, filename):
                print(f"跳过 {rel_path}: 不匹配包含/排除模式")
                continue

            # 读取内容
            try:
                with open(abs_path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
                files[rel_path] = content
                print(f"添加 {rel_path} ({file_size} 字节)")
            except Exception as e:
                print(f"读取 {rel_path} 失败: {e}")

    return {
        "files": files,
        "stats": {
            "downloaded_count": len(files),
            "skipped_count": len(skipped_files),
            "skipped_files": skipped_files,
            "include_patterns": include_patterns,
            "exclude_patterns": exclude_patterns,
            "source": "git_clone"
        }
    }

def crawl_github_files(
    repo_url: str,
    commit_index: int = None,
    max_file_size: int = 1 * 1024 * 1024,  # 1 MB
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
) -> Dict:
    """
    通过本地克隆从Git仓库爬取文件（支持GitHub等平台的SSH/HTTPS URL）

    参数:
        repo_url (str): Git仓库URL (SSH或HTTPS格式)
        commit_index (int, 可选): 提交索引，1表示最早的提交，2表示第二早的提交，以此类推
        max_file_size (int, 可选): 下载文件的最大大小(字节，默认1MB)
        include_patterns (str或str集合, 可选): 包含文件的模式(如"*.py", {"*.md", "*.txt"})
        exclude_patterns (str或str集合, 可选): 排除文件的模式

    返回:
        dict: 包含文件和统计信息的字典
    """
    # 通过Git克隆仓库到临时目录
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            # 方法1: 克隆仓库
            repo = clone_repository(repo_url, tmpdirname)
            
            # 方法2: 根据传参回到指定的commit
            reset_to_commit(repo, commit_index)
            
            # 方法3: 过滤并读取文件
            result = filter_and_read_files(
                tmpdirname,
                max_file_size=max_file_size,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns
            )
            
            return result
            
        except Exception as e:
            return {
                "files": {}, 
                "stats": {
                    "error": str(e), 
                    "downloaded_count": 0, 
                    "skipped_count": 0
                }
            }

# 示例用法
if __name__ == "__main__":
    # 使用HTTPS格式的仓库URL
    repo_url = "https://github.com/DROWNING2003/Roo-Code"
    
    # 示例1: 获取最新版本的Python和Markdown文件
    print("=== 示例1: 获取最新版本 ===")
    result = crawl_github_files(
        repo_url,
        commit_index=None,  # 不指定commit，使用最新版本
        max_file_size=1 * 1024 * 1024,  # 1 MB 字节
        include_patterns={"*.py", "*.md"},  # 包含Python和Markdown文件
    )
    
    files = result["files"]
    stats = result["stats"]
    
    # 检查是否有错误
    if "error" in stats:
        print(f"\n错误: {stats['error']}")
        print(f"已下载 {stats['downloaded_count']} 个文件。")
    else:
        print(f"\n已下载 {stats['downloaded_count']} 个文件。")
        print(f"跳过 {stats['skipped_count']} 个文件(由于大小限制或模式)。")
        print(f"包含模式: {stats['include_patterns']}")
        print(f"排除模式: {stats['exclude_patterns']}")
        
        # 显示字典中的所有文件路径
        print("\n字典中的文件:")
        for file_path in sorted(files.keys()):
            print(f"  {file_path}")
    
    # 示例2: 获取第一个commit的文件
    print("\n=== 示例2: 获取第一个commit ===")
    result2 = crawl_github_files(
        repo_url,
        commit_index=1,  # 回到最早的第一个commit
        max_file_size=1 * 1024 * 1024,
        include_patterns={"*.py", "*.md"},
    )
    
    files2 = result2["files"]
    stats2 = result2["stats"]
    
    if "error" in stats2:
        print(f"错误: {stats2['error']}")
    else:
        print(f"第一个commit包含 {stats2['downloaded_count']} 个文件")
        print("文件列表:")
        for file_path in sorted(files2.keys()):
            print(f"  {file_path}")
    
    # 示例: 访问特定文件的内容
    if files:
        sample_file = next(iter(files))
        print(f"\n示例文件: {sample_file}")
        print(f"内容预览: {files[sample_file][:200]}...")