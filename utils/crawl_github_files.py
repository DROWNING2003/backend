# 导入必要的库
import os        # 用于操作系统相关功能
import tempfile  # 用于创建临时文件和目录
import git       # 用于Git仓库操作
import fnmatch   # 用于文件名模式匹配
from typing import Union, Set, Dict  # 类型提示

def crawl_github_files(
    repo_url: str,
    max_file_size: int = 1 * 1024 * 1024,  # 1 MB
    use_relative_paths: bool = False,
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None
) -> Dict:
    """
    通过本地克隆从Git仓库爬取文件（支持GitHub等平台的SSH/HTTPS URL）

    参数:
        repo_url (str): Git仓库URL (SSH或HTTPS格式)
                        (例如: 'git@github.com:microsoft/autogen.git'
                        或 'https://github.com/microsoft/autogen.git')
        max_file_size (int, 可选): 下载文件的最大大小(字节，默认1MB)
        use_relative_paths (bool, 可选): 如果为True，文件路径将相对于仓库根目录
        include_patterns (str或str集合, 可选): 包含文件的模式(如"*.py", {"*.md", "*.txt"})
                                              如果为None，则包含所有文件
        exclude_patterns (str或str集合, 可选): 排除文件的模式
                                              如果为None，则不排除任何文件

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

    # 通过Git克隆仓库到临时目录
    with tempfile.TemporaryDirectory() as tmpdirname:
        print(f"克隆仓库 {repo_url} 到临时目录 {tmpdirname} ...")
        try:
            repo = git.Repo.clone_from(repo_url, tmpdirname)
        except Exception as e:
            print(f"克隆仓库出错: {e}")
            # 如果是SSH失败，尝试转换为HTTPS URL
            if "git@github.com:" in repo_url and ("Connection closed" in str(e) or "exit code(128)" in str(e)):
                https_url = repo_url.replace("git@github.com:", "https://github.com/")
                if not https_url.endswith('.git'):
                    https_url += '.git'
                print(f"SSH连接失败，尝试使用HTTPS: {https_url}")
                try:
                    repo = git.Repo.clone_from(https_url, tmpdirname)
                    print("HTTPS克隆成功！")
                except Exception as e2:
                    print(f"HTTPS克隆也失败: {e2}")
                    return {"files": {}, "stats": {"error": str(e2), "downloaded_count": 0, "skipped_count": 0}}
            else:
                return {"files": {}, "stats": {"error": str(e), "downloaded_count": 0, "skipped_count": 0}}

        # 遍历目录
        files = {}
        skipped_files = []

        for root, dirs, filenames in os.walk(tmpdirname):
            for filename in filenames:
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, tmpdirname)

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
                "base_path": None,
                "include_patterns": include_patterns,
                "exclude_patterns": exclude_patterns,
                "source": "git_clone"
            }
        }

# 示例用法
if __name__ == "__main__":
    # 使用SSH格式的仓库URL
    repo_url = "git@github.com:pydantic/pydantic.git"
    # 或者使用HTTPS格式:
    # repo_url = "https://github.com/pydantic/pydantic.git"
    
    # 示例: 获取Python和Markdown文件，但排除测试文件
    result = crawl_github_files(
        repo_url,
        max_file_size=1 * 1024 * 1024,  # 1 MB 字节
        use_relative_paths=True,  # 启用相对路径
        include_patterns={"*.py", "*.md"},  # 包含Python和Markdown文件
    )
    
    files = result["files"]
    stats = result["stats"]
    
    # 检查是否有错误
    if "error" in stats:
        print(f"\n错误: {stats['error']}")
        print(f"已下载 {stats['downloaded_count']} 个文件。")
        exit()
    
    print(f"\n已下载 {stats['downloaded_count']} 个文件。")
    print(f"跳过 {stats['skipped_count']} 个文件(由于大小限制或模式)。")
    print(f"包含模式: {stats['include_patterns']}")
    print(f"排除模式: {stats['exclude_patterns']}")
    
    # 显示字典中的所有文件路径
    print("\n字典中的文件:")
    for file_path in sorted(files.keys()):
        print(f"  {file_path}")
    
    # 示例: 访问特定文件的内容
    if files:
        sample_file = next(iter(files))
        print(f"\n示例文件: {sample_file}")
        print(f"内容预览: {files[sample_file][:200]}...")