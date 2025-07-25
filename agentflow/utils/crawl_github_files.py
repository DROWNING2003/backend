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
    "code": {"*.py","*.sol",".md","*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg", "*.conf",".env", "*.js", "*.ts", "*.java", "*.cpp", "*.c", "*.h", "*.cs", "*.go", "*.rs", "*.php"},
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

def reset_to_commit(repo: git.Repo,fullcommits: list[git.Commit], commit_index: int = None):
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
        # commits = list(repo.iter_commits(reverse=True))
        
        if commit_index < 1 or commit_index > len(fullcommits):
            print(f"提交索引 {commit_index} 超出范围 (1-{len(fullcommits)})")
            return
            
        target_commit = fullcommits[commit_index - 1]
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
    target_files: Set[str] = None,
    **kwargs
) -> Dict:
    """
    根据模式过滤并读取文件
    
    参数:
        repo_dir (str): 仓库目录路径
        max_file_size (int, 可选): 下载文件的最大大小(字节，默认1MB)
        include_patterns (str或str集合, 可选): 包含文件的模式(如"*.py", {"*.md", "*.txt"})
        exclude_patterns (str或str集合, 可选): 排除文件的模式
        target_files (set, 可选): 指定要读取的文件列表，如果提供则只读取这些文件
        
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

            # 如果指定了目标文件列表，只处理列表中的文件
            if target_files is not None and rel_path not in target_files:
                print(f"跳过 {rel_path}: 不在目标文件列表中")
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


def get_commit_list(repo: git.Repo, max_commits: int = 20) -> Dict:
    """
    获取仓库的提交列表
    
    参数:
        repo (git.Repo): Git仓库对象
        max_commits (int): 最大返回提交数量，默认20
        
    返回:
        dict: 包含提交列表的字典
    """
    try:
        # 获取所有提交，按时间顺序排列（最早的在前）
        commits = list(repo.iter_commits(reverse=True))
        
        commit_list = []
        for i, commit in enumerate(commits[:max_commits], 1):
            commit_list.append({
                "index": i,
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat()
            })
        
        return {
            "commits": commit_list,
            "total_commits": len(commits),
            "showing": min(max_commits, len(commits))
        }
        
    except Exception as e:
        return {"error": f"获取提交列表失败: {e}"}

def get_commit_changes_detailed(repo: git.Repo, commit_index: int, include_diff_content: bool = True) -> Dict:
    """
    获取指定提交相对于前一个提交的详细增量变化，包括具体的代码diff
    
    参数:
        repo (git.Repo): Git仓库对象
        commit_index (int): 提交索引，1表示最早的提交，2表示第二早的提交，以此类推
        include_diff_content (bool): 是否包含具体的diff内容，默认True
        
    返回:
        dict: 包含详细变化信息的字典
    """
    try:
        # 获取所有提交，按时间顺序排列（最早的在前）
        commits = list(repo.iter_commits(reverse=True))
        
        if commit_index < 1 or commit_index > len(commits):
            return {"error": f"提交索引 {commit_index} 超出范围 (1-{len(commits)})"}
            
        current_commit = commits[commit_index - 1]
        
        # 如果是第一个提交，返回所有文件
        if commit_index == 1:
            print(f"获取第 {commit_index} 个提交的所有文件: {current_commit.hexsha[:8]}")
            
            # 获取初始提交的所有文件
            initial_files = []
            for item in current_commit.tree.traverse():
                if item.type == 'blob':  # 只处理文件，不处理目录
                    try:
                        content = item.data_stream.read().decode('utf-8')
                        initial_files.append({
                            "path": item.path,
                            "type": "added",
                            "content": content,
                            "lines_added": len(content.splitlines()),
                            "lines_deleted": 0,
                            "size": len(content)
                        })
                    except UnicodeDecodeError:
                        # 跳过二进制文件
                        initial_files.append({
                            "path": item.path,
                            "type": "added",
                            "content": "[Binary file]",
                            "lines_added": 0,
                            "lines_deleted": 0,
                            "size": item.size
                        })
            
            return {
                "commit_info": {
                    "index": commit_index,
                    "hash": current_commit.hexsha,
                    "message": current_commit.message.strip(),
                    "author": str(current_commit.author),
                    "date": current_commit.committed_datetime.isoformat()
                },
                "file_changes": initial_files,
                "summary": {
                    "files_added": len(initial_files),
                    "files_modified": 0,
                    "files_deleted": 0,
                    "total_lines_added": sum(f["lines_added"] for f in initial_files),
                    "total_lines_deleted": 0
                },
                "is_initial": True
            }
        
        # 获取前一个提交
        previous_commit = commits[commit_index - 2]
        
        print(f"获取第 {commit_index} 个提交的增量变化: {current_commit.hexsha[:8]} vs {previous_commit.hexsha[:8]}")
        
        # 获取两个提交之间的差异
        diff = previous_commit.diff(current_commit, create_patch=include_diff_content)
        
        file_changes = []
        total_lines_added = 0
        total_lines_deleted = 0
        files_added = 0
        files_modified = 0
        files_deleted = 0
        
        for item in diff:
            file_info = {
                "path": item.a_path or item.b_path,
                "lines_added": 0,
                "lines_deleted": 0,
                "diff_content": "",
                "old_content": "",
                "new_content": ""
            }
            
            if item.new_file:
                file_info["type"] = "added"
                files_added += 1
                if item.b_blob:
                    try:
                        content = item.b_blob.data_stream.read().decode('utf-8')
                        file_info["new_content"] = content
                        file_info["lines_added"] = len(content.splitlines())
                        total_lines_added += file_info["lines_added"]
                    except UnicodeDecodeError:
                        file_info["new_content"] = "[Binary file]"
                        
            elif item.deleted_file:
                file_info["type"] = "deleted"
                files_deleted += 1
                if item.a_blob:
                    try:
                        content = item.a_blob.data_stream.read().decode('utf-8')
                        file_info["old_content"] = content
                        file_info["lines_deleted"] = len(content.splitlines())
                        total_lines_deleted += file_info["lines_deleted"]
                    except UnicodeDecodeError:
                        file_info["old_content"] = "[Binary file]"
                        
            elif item.renamed_file:
                file_info["type"] = "renamed"
                file_info["old_path"] = item.a_path
                file_info["new_path"] = item.b_path
                files_modified += 1
                
            else:
                file_info["type"] = "modified"
                files_modified += 1
                
                # 获取修改前后的内容
                if item.a_blob and item.b_blob:
                    try:
                        old_content = item.a_blob.data_stream.read().decode('utf-8')
                        new_content = item.b_blob.data_stream.read().decode('utf-8')
                        file_info["old_content"] = old_content
                        file_info["new_content"] = new_content
                        
                        # 计算行数变化
                        old_lines = old_content.splitlines()
                        new_lines = new_content.splitlines()
                        
                        # 简单的行数统计（实际的diff会更复杂）
                        if len(new_lines) > len(old_lines):
                            file_info["lines_added"] = len(new_lines) - len(old_lines)
                        elif len(old_lines) > len(new_lines):
                            file_info["lines_deleted"] = len(old_lines) - len(new_lines)
                            
                        total_lines_added += file_info["lines_added"]
                        total_lines_deleted += file_info["lines_deleted"]
                        
                    except UnicodeDecodeError:
                        file_info["old_content"] = "[Binary file]"
                        file_info["new_content"] = "[Binary file]"
            
            # 获取diff内容
            if include_diff_content and hasattr(item, 'diff') and item.diff:
                try:
                    file_info["diff_content"] = item.diff.decode('utf-8')
                except UnicodeDecodeError:
                    file_info["diff_content"] = "[Binary file diff]"
            
            file_changes.append(file_info)
        print(file_changes)
        return {
            "commit_info": {
                "index": commit_index,
                "hash": current_commit.hexsha,
                "message": current_commit.message.strip(),
                "author": str(current_commit.author),
                "date": current_commit.committed_datetime.isoformat()
            },
            "file_changes": file_changes,
            "summary": {
                "files_added": files_added,
                "files_modified": files_modified,
                "files_deleted": files_deleted,
                "total_lines_added": total_lines_added,
                "total_lines_deleted": total_lines_deleted
            },
            "is_initial": False
        }
        
    except Exception as e:
        print(e)
        return {"error": f"获取提交变化失败: {e}"}

def get_commit_changes(repo: git.Repo, commit_index: int) -> Dict:
    """
    获取指定提交相对于前一个提交的增量变化（简化版本，保持向后兼容）
    
    参数:
        repo (git.Repo): Git仓库对象
        commit_index (int): 提交索引，1表示最早的提交，2表示第二早的提交，以此类推
        
    返回:
        dict: 包含变化文件信息的字典
    """
    try:
        # 获取所有提交，按时间顺序排列（最早的在前）
        commits = list(repo.iter_commits(reverse=True))
        
        if commit_index < 1 or commit_index > len(commits):
            return {"error": f"提交索引 {commit_index} 超出范围 (1-{len(commits)})"}
            
        current_commit = commits[commit_index - 1]
        
        # 如果是第一个提交，返回所有文件
        if commit_index == 1:
            print(f"获取第 {commit_index} 个提交的所有文件: {current_commit.hexsha[:8]}")
            return {
                "commit_info": {
                    "index": commit_index,
                    "hash": current_commit.hexsha,
                    "message": current_commit.message.strip(),
                    "author": str(current_commit.author),
                    "date": current_commit.committed_datetime.isoformat()
                },
                "changes": {
                    "added": [],
                    "modified": [],
                    "deleted": []
                },
                "is_initial": True
            }
        
        # 获取前一个提交
        previous_commit = commits[commit_index - 2]
        
        print(f"获取第 {commit_index} 个提交的增量变化: {current_commit.hexsha[:8]} vs {previous_commit.hexsha[:8]}")
        
        # 获取两个提交之间的差异
        diff = previous_commit.diff(current_commit)
        
        changes = {
            "added": [],
            "modified": [],
            "deleted": []
        }
        
        for item in diff:
            if item.new_file:
                changes["added"].append(item.b_path)
            elif item.deleted_file:
                changes["deleted"].append(item.a_path)
            elif item.renamed_file:
                changes["modified"].append(f"{item.a_path} -> {item.b_path}")
            else:
                changes["modified"].append(item.a_path or item.b_path)
        
        return {
            "commit_info": {
                "index": commit_index,
                "hash": current_commit.hexsha,
                "message": current_commit.message.strip(),
                "author": str(current_commit.author),
                "date": current_commit.committed_datetime.isoformat()
            },
            "changes": changes,
            "is_initial": False
        }
        
    except Exception as e:
        return {"error": f"获取提交变化失败: {e}"}

def get_repository_commits(repo_url: str, max_commits: int = 20) -> Dict:
    """
    获取Git仓库的提交列表
    
    参数:
        repo_url (str): Git仓库URL (SSH或HTTPS格式)
        max_commits (int): 最大返回提交数量，默认20
        
    返回:
        dict: 包含提交列表的字典
    """
    # 创建临时目录并手动管理清理
    tmpdirname = tempfile.mkdtemp()
    try:
        # 克隆仓库
        repo = clone_repository(repo_url, tmpdirname)
        
        # 获取提交列表
        result = get_commit_list(repo, max_commits)
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "commits": [],
            "total_commits": 0,
            "showing": 0
        }
    finally:
        # 手动清理临时目录，处理Windows权限问题
        try:
            safe_rmtree(tmpdirname)
        except Exception as cleanup_error:
            print(f"清理临时目录时出错: {cleanup_error}")

def get_repository_commit_changes(repo_url: str, commit_index: int, include_diff_content: bool = True) -> Dict:
    """
    直接从仓库URL获取指定提交的详细变化信息
    
    参数:
        repo_url (str): Git仓库URL (SSH或HTTPS格式)
        commit_index (int): 提交索引，1表示最早的提交，2表示第二早的提交，以此类推
        include_diff_content (bool): 是否包含具体的diff内容，默认True
        
    返回:
        dict: 包含详细变化信息的字典
    """
    # 创建临时目录并手动管理清理
    tmpdirname = tempfile.mkdtemp()
    try:
        # 克隆仓库
        repo = clone_repository(repo_url, tmpdirname)
        
        # 获取详细变化信息
        result = get_commit_changes_detailed(repo, commit_index, include_diff_content)
        
        return result
        
    except Exception as e:
        return {"error": f"获取提交变化失败: {e}"}
    finally:
        # 手动清理临时目录，处理Windows权限问题
        try:
            safe_rmtree(tmpdirname)
        except Exception as cleanup_error:
            print(f"清理临时目录时出错: {cleanup_error}")

def crawl_github_files_incremental(
    repo_url: str,
    commit_index: int = None,
    max_file_size: int = 1 * 1024 * 1024,  # 1 MB
    include_patterns: Union[str, Set[str]] = None,
    exclude_patterns: Union[str, Set[str]] = None,
    only_changed_files: bool = False
) -> Dict:
    """
    通过本地克隆从Git仓库爬取文件，支持增量获取指定提交的变化
    
    参数:
        repo_url (str): Git仓库URL (SSH或HTTPS格式)
        commit_index (int, 可选): 提交索引，1表示最早的提交，2表示第二早的提交，以此类推
        max_file_size (int, 可选): 下载文件的最大大小(字节，默认1MB)
        include_patterns (str或str集合, 可选): 包含文件的模式(如"*.py", {"*.md", "*.txt"})
        exclude_patterns (str或str集合, 可选): 排除文件的模式
        only_changed_files (bool, 可选): 是否只返回变化的文件，默认False返回所有文件
        
    返回:
        dict: 包含文件、变化信息和统计信息的字典
    """
    # 创建临时目录并手动管理清理
    tmpdirname = tempfile.mkdtemp()
    try:
        # 克隆仓库
        repo = clone_repository(repo_url, tmpdirname)
        
        # 获取提交变化信息
        changes_info = get_commit_changes(repo, commit_index) if commit_index else None
        # 重置到指定提交
        if commit_index:
            reset_to_commit(repo, commit_index)
        
        # 如果只需要变化的文件，则过滤文件列表
        target_files = None
        if only_changed_files and changes_info and not changes_info.get("error"):
            if not changes_info.get("is_initial"):
                # 只获取新增和修改的文件
                target_files = set(changes_info["changes"]["added"] + changes_info["changes"]["modified"])
                print(f"只获取变化的文件: {len(target_files)} 个")
        
        # 过滤并读取文件
        result = filter_and_read_files(
            tmpdirname,
            max_file_size=max_file_size,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            target_files=target_files
        )
        
        # 添加变化信息到结果中
        if changes_info:
            result["commit_changes"] = changes_info
        
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
        # 克隆仓库
        repo = clone_repository(repo_url, tmpdirname)
        
        # 根据传参回到指定的commit
        if commit_index:
            reset_to_commit(repo, commit_index)
        
        # 过滤并读取文件
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
    currentIndex = 5
    repo_url = "https://github.com/zengyi-thinking/auto_mate_test2.git"
    
    # 通用调用方式示例
    print("=== 通用调用方式示例 ===")
    
    # 方式1: 使用预定义模式
    print("\n1. 使用预定义模式 - 只获取Python文件:")
    tmpdirname = tempfile.mkdtemp()
    repo = clone_repository(repo_url, tmpdirname)
    reset_to_commit(repo, currentIndex)
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
    
    # 增量功能示例
    print("\n=== 增量功能示例 ===")
    
    # 获取简化的变化信息
    print(f"\n1. 获取第{currentIndex}个提交的简化变化信息:")
    changeCode = get_commit_changes(repo, currentIndex)
    print(f"提交信息: {changeCode.get('commit_info', {}).get('message', 'N/A')}")
    if 'changes' in changeCode:
        changes = changeCode['changes']
        print(f"新增文件: {len(changes['added'])}")
        print(f"修改文件: {len(changes['modified'])}")
        print(f"删除文件: {len(changes['deleted'])}")
    
    # 获取详细的变化信息（包含具体代码内容）
    print(f"\n2. 获取第{currentIndex}个提交的详细变化信息:")
    detailed_changes = get_commit_changes_detailed(repo, currentIndex, include_diff_content=True)
    
    if 'error' not in detailed_changes:
        summary = detailed_changes['summary']
        print(f"变化统计:")
        print(f"  新增文件: {summary['files_added']}")
        print(f"  修改文件: {summary['files_modified']}")
        print(f"  删除文件: {summary['files_deleted']}")
        print(f"  新增行数: {summary['total_lines_added']}")
        print(f"  删除行数: {summary['total_lines_deleted']}")
        
    #     print(f"\n文件变化详情:")
    #     for i, file_change in enumerate(detailed_changes['file_changes'][:3]):  # 只显示前3个文件
    #         print(f"  {i+1}. {file_change['path']} ({file_change['type']})")
    #         print(f"     +{file_change['lines_added']} -{file_change['lines_deleted']} 行")
            
    #         # 显示新内容的预览（如果是新增或修改的文件）
    #         if file_change['type'] in ['added', 'modified'] and file_change.get('new_content'):
    #             content = file_change['new_content']
    #             if content != "[Binary file]":
    #                 preview = content[:200].replace('\n', ' ')
    #                 if len(content) > 200:
    #                     preview += " [...]"
    #                 print(f"     内容预览: {preview}")
            
    #         # 显示diff内容（如果有）
    #         if file_change.get('diff_content') and file_change['diff_content'] != "[Binary file diff]":
    #             diff_lines = file_change['diff_content'].split('\n')[:10]  # 只显示前10行diff
    #             print(f"     Diff预览:")
    #             for line in diff_lines:
    #                 if line.startswith('+'):
    #                     print(f"       {line}")
    #                 elif line.startswith('-'):
    #                     print(f"       {line}")
    #                 elif line.startswith('@@'):
    #                     print(f"       {line}")
        
    #     if len(detailed_changes['file_changes']) > 3:
    #         print(f"  ... 还有 {len(detailed_changes['file_changes']) - 3} 个文件变化")
    # else:
    #     print(f"获取详细变化失败: {detailed_changes['error']}")
    buffer = []
    
    if detailed_changes.get('file_changes'):
        buffer.append("\n文件变化详情:")
        for i, file_change in enumerate(detailed_changes['file_changes']):  # 显示所有文件
            # buffer.append(f"  {i+1}. {file_change['path']} ({file_change['type']})")
            # buffer.append(f"     +{file_change['lines_added']} -{file_change['lines_deleted']} 行")
            
            # 显示新内容的预览（如果是新增或修改的文件）
            # if file_change['type'] in ['added', 'modified'] and file_change.get('new_content'):
            #     content = file_change['new_content']
            #     if content != "[Binary file]":
            #         preview = content[:200].replace('\n', ' ')
            #         if len(content) > 200:
            #             preview += " [...]"
            #         buffer.append(f"     内容预览: {preview}")
            
            # 显示diff内容（如果有）
            if file_change.get('diff_content') and file_change['diff_content'] != "[Binary file diff]":
                diff_lines = file_change['diff_content'].split('\n')[:]
                buffer.append(f"     Diff内容:")
                buffer.append(f"  {i+1}. {file_change['path']} ({file_change['type']})")
                for line in diff_lines:
                    if line.startswith('+'):
                        buffer.append(f"       {line}")
                    elif line.startswith('-'):
                        buffer.append(f"       {line}")
                    elif line.startswith('@@'):
                        buffer.append(f"       {line}")
    else:
        buffer.append(f"获取详细变化失败: {detailed_changes.get('error', '未知错误')}")
    
    print('\n'.join(buffer))
    # safe_rmtree(tmpdirname)
    
    # # 使用便捷函数直接从URL获取变化
    # print(f"\n3. 使用便捷函数获取第{currentIndex}个提交的变化:")
    # url_changes = get_repository_commit_changes(repo_url, currentIndex, include_diff_content=False)
    # if 'error' not in url_changes:
    #     print(f"提交: {url_changes['commit_info']['message']}")
    #     print(f"变化文件数: {len(url_changes['file_changes'])}")
    #     for file_change in url_changes['file_changes'][:2]:  # 只显示前2个
    #         print(f"  - {file_change['path']} ({file_change['type']})")
    # else:
    #     print(f"获取失败: {url_changes['error']}")   