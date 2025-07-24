# 导入必要的库
import os        # 用于操作系统相关功能
import tempfile  # 用于创建临时文件和目录
import git       # 用于Git仓库操作
import fnmatch   # 用于文件名模式匹配
import shutil    # 用于文件操作
import stat      # 用于文件权限操作
from typing import Union, Set, Dict  # 类型提示

# 预定义的文件模式配置
FILE_PATTERNS = {
    "code": {"*.py", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h", "*.cs", "*.go", "*.rs", "*.php"},
    "web": {"*.html", "*.css", "*.js", "*.ts", "*.jsx", "*.tsx", "*.vue", "*.scss", "*.sass", "*.less"},
    "docs": {"*.md", "*.txt", "*.rst", "*.doc", "*.docx", "*.pdf"},
    "config": {"*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg", "*.conf"},
    "python": {"*.py", "*.pyx", "*.pyi"},
    "javascript": {"*.js", "*.ts", "*.jsx", "*.tsx", "*.mjs"},
    "data": {"*.csv", "*.json", "*.xml", "*.xlsx", "*.xls"},
    "all": {"*"},  # 所有文件
}

# 预定义的排除模式
EXCLUDE_PATTERNS = {
    "common": {"*/node_modules/*", "*/.git/*", "*/venv/*", "*/__pycache__/*", "*.pyc", "*/dist/*", "*/build/*"},
    "test": {"*/test/*", "*/tests/*", "*_test.py", "*_test.js", "test_*.py"},
    "cache": {"*/.cache/*", "*/tmp/*", "*/temp/*", "*/.DS_Store"},
}

def get_file_patterns(pattern_key: str = None, custom_patterns: Union[str, Set[str]] = None) -> Set[str]:
    """
    获取文件模式配置
    
    参数:
        pattern_key (str): 预定义模式键名 ("code", "web", "docs", "config", "python", "javascript", "data", "all")
        custom_patterns (str或set): 自定义模式
        
    返回:
        set: 文件模式集合
    """
    if custom_patterns:
        if isinstance(custom_patterns, str):
            return {custom_patterns}
        return custom_patterns
    
    if pattern_key and pattern_key in FILE_PATTERNS:
        return FILE_PATTERNS[pattern_key]
    
    return None  # 默认包含所有文件

def get_exclude_patterns(exclude_key: str = None, custom_excludes: Union[str, Set[str]] = None) -> Set[str]:
    """
    获取排除模式配置
    
    参数:
        exclude_key (str): 预定义排除键名 ("common", "test", "cache")
        custom_excludes (str或set): 自定义排除模式
        
    返回:
        set: 排除模式集合
    """
    patterns = set()
    
    if exclude_key and exclude_key in EXCLUDE_PATTERNS:
        patterns.update(EXCLUDE_PATTERNS[exclude_key])
    
    if custom_excludes:
        if isinstance(custom_excludes, str):
            patterns.add(custom_excludes)
        else:
            patterns.update(custom_excludes)
    
    return patterns if patterns else None

def remove_readonly(func, path, _):
    """
    Windows下删除只读文件的错误处理函数
    """
    os.chmod(path, stat.S_IWRITE)
    func(path)

def safe_rmtree(path):
    """
    安全删除目录树，处理Windows下的只读文件问题
    """
    if os.path.exists(path):
        shutil.rmtree(path, onerror=remove_readonly)

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
    exclude_patterns: Union[str, Set[str]] = None,
    **kwargs
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
    # 创建临时目录并手动管理清理
    tmpdirname = tempfile.mkdtemp()
    try:
        # # 方法1: 克隆仓库
        # repo = clone_repository(repo_url, tmpdirname)
        
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
    finally:
        # 手动清理临时目录，处理Windows权限问题
        try:
            safe_rmtree(tmpdirname)
        except Exception as cleanup_error:
            print(f"清理临时目录时出错: {cleanup_error}")

# 示例用法
if __name__ == "__main__":
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test2.git"
    
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
        
       
    
    # 方式2: 使用自定义模式
    # print("\n2. 使用自定义模式 - 获取特定文件:")
    # tmpdirname = tempfile.mkdtemp()
    # try:
    #     repo = clone_repository(repo_url, tmpdirname)
    #     reset_to_commit(repo, 1)
    #     result = filter_and_read_files(
    #         tmpdirname,
    #         max_file_size=1 * 1024 * 1024,
    #         include_patterns=get_file_patterns(custom_patterns={"*.py", "*.md", "*.json"}),
    #         exclude_patterns=get_exclude_patterns("test", {"*/examples/*"})  # 排除测试和示例
    #     )
    #     print(f"获取到 {result['stats']['downloaded_count']} 个文件")
    # finally:
    #     safe_rmtree(tmpdirname)
    
    # # 方式3: 获取所有代码文件
    # print("\n3. 获取所有代码文件:")
    # tmpdirname = tempfile.mkdtemp()
    # try:
    #     repo = clone_repository(repo_url, tmpdirname)
    #     reset_to_commit(repo, 1)
    #     result = filter_and_read_files(
    #         tmpdirname,
    #         max_file_size=1 * 1024 * 1024,
    #         include_patterns=get_file_patterns("code"),  # 所有代码文件
    #         exclude_patterns=get_exclude_patterns("common")
    #     )
    #     print(f"获取到 {result['stats']['downloaded_count']} 个代码文件")
        
    #     # 显示文件列表
    #     files = result["files"]
    #     print("文件列表:")
    #     for file_path in sorted(files.keys())[:10]:  # 只显示前10个
    #         print(f"  {file_path}")
    #     if len(files) > 10:
    #         print(f"  ... 还有 {len(files) - 10} 个文件")
            
    # finally:
    #     safe_rmtree(tmpdirname)
    
    # # 方式4: 最简单的调用 - 获取所有文件
    # print("\n4. 最简单调用 - 获取所有文件:")
    # result = crawl_github_files(
    #     repo_url,
    #     commit_index=1,
    #     max_file_size=1 * 1024 * 1024,
    #     include_patterns=get_file_patterns("all"),  # 所有文件
    #     exclude_patterns=get_exclude_patterns("common")  # 排除常见无用文件
    # )
    
    # if "error" not in result["stats"]:
    #     print(f"获取到 {result['stats']['downloaded_count']} 个文件")
    # else:
    #     print(f"错误: {result['stats']['error']}")
    
    # print("\n=== 可用的预定义模式 ===")
    # print("文件类型模式:")
    # for key, patterns in FILE_PATTERNS.items():
    #     print(f"  {key}: {patterns}")
    
    # print("\n排除模式:")
    # for key, patterns in EXCLUDE_PATTERNS.items():
    #     print(f"  {key}: {patterns}")