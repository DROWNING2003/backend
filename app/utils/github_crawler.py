"""
GitHub仓库爬取工具
集成原有的crawl_github_files功能到FastAPI应用中
"""

import os
import tempfile
import fnmatch
import logging
from typing import Union, Set, Dict, List, Optional
from datetime import datetime

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None

logger = logging.getLogger(__name__)


class GitHubCrawler:
    """GitHub仓库爬取器"""
    
    def __init__(self):
        self.default_max_file_size = 1 * 1024 * 1024  # 1 MB
        self.default_include_patterns = {"*.py", "*.js", "*.ts", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"}
        self.default_exclude_patterns = {
            "*.pyc", "*.pyo", "*.pyd", "__pycache__/*", ".git/*", 
            "node_modules/*", "*.log", "*.tmp", "*.cache"
        }
    
    async def crawl_repository(
        self,
        repo_url: str,
        max_file_size: Optional[int] = None,
        use_relative_paths: bool = True,
        include_patterns: Optional[Union[str, Set[str]]] = None,
        exclude_patterns: Optional[Union[str, Set[str]]] = None,
        branch: str = "main"
    ) -> Dict:
        """
        爬取GitHub仓库文件
        
        参数:
            repo_url: Git仓库URL (SSH或HTTPS格式)
            max_file_size: 下载文件的最大大小(字节)
            use_relative_paths: 是否使用相对路径
            include_patterns: 包含文件的模式
            exclude_patterns: 排除文件的模式
            branch: 分支名称
            
        返回:
            包含文件和统计信息的字典
        """
        try:
            # 检查Git是否可用
            if not GIT_AVAILABLE:
                return {
                    "files": {},
                    "stats": {
                        "error": "GitPython未安装，无法克隆仓库",
                        "downloaded_count": 0,
                        "skipped_count": 0,
                        "repo_url": repo_url,
                        "branch": branch,
                        "timestamp": datetime.now().isoformat()
                    }
                }

            # 设置默认值
            if max_file_size is None:
                max_file_size = self.default_max_file_size
            if include_patterns is None:
                include_patterns = self.default_include_patterns
            if exclude_patterns is None:
                exclude_patterns = self.default_exclude_patterns

            # 将单个模式转换为集合
            if include_patterns and isinstance(include_patterns, str):
                include_patterns = {include_patterns}
            if exclude_patterns and isinstance(exclude_patterns, str):
                exclude_patterns = {exclude_patterns}

            logger.info(f"开始爬取仓库: {repo_url}")

            # 通过Git克隆仓库到临时目录
            with tempfile.TemporaryDirectory() as tmpdirname:
                logger.info(f"克隆仓库到临时目录: {tmpdirname}")
                
                try:
                    repo = git.Repo.clone_from(repo_url, tmpdirname, branch=branch)
                except Exception as e:
                    logger.error(f"克隆仓库出错: {e}")
                    # 如果是SSH失败，尝试转换为HTTPS URL
                    if "git@github.com:" in repo_url and ("Connection closed" in str(e) or "exit code(128)" in str(e)):
                        https_url = repo_url.replace("git@github.com:", "https://github.com/")
                        if not https_url.endswith('.git'):
                            https_url += '.git'
                        logger.info(f"SSH连接失败，尝试使用HTTPS: {https_url}")
                        try:
                            repo = git.Repo.clone_from(https_url, tmpdirname, branch=branch)
                            logger.info("HTTPS克隆成功！")
                        except Exception as e2:
                            logger.error(f"HTTPS克隆也失败: {e2}")
                            return {
                                "files": {},
                                "stats": {
                                    "error": str(e2),
                                    "downloaded_count": 0,
                                    "skipped_count": 0,
                                    "repo_url": repo_url,
                                    "branch": branch,
                                    "timestamp": datetime.now().isoformat()
                                }
                            }
                    else:
                        return {
                            "files": {},
                            "stats": {
                                "error": str(e),
                                "downloaded_count": 0,
                                "skipped_count": 0,
                                "repo_url": repo_url,
                                "branch": branch,
                                "timestamp": datetime.now().isoformat()
                            }
                        }
                
                # 遍历目录并收集文件
                files = {}
                skipped_files = []
                
                for root, dirs, filenames in os.walk(tmpdirname):
                    # 跳过.git目录
                    if '.git' in dirs:
                        dirs.remove('.git')
                    
                    for filename in filenames:
                        abs_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(abs_path, tmpdirname)
                        
                        # 检查文件大小
                        try:
                            file_size = os.path.getsize(abs_path)
                        except OSError:
                            continue
                        
                        if file_size > max_file_size:
                            skipped_files.append({
                                "path": rel_path,
                                "size": file_size,
                                "reason": "size_limit"
                            })
                            logger.debug(f"跳过 {rel_path}: 大小 {file_size} 超过限制 {max_file_size}")
                            continue
                        
                        # 检查包含/排除模式
                        if not self._should_include_file(rel_path, filename, include_patterns, exclude_patterns):
                            skipped_files.append({
                                "path": rel_path,
                                "size": file_size,
                                "reason": "pattern_mismatch"
                            })
                            logger.debug(f"跳过 {rel_path}: 不匹配包含/排除模式")
                            continue
                        
                        # 读取文件内容
                        try:
                            with open(abs_path, "r", encoding="utf-8-sig") as f:
                                content = f.read()
                            files[rel_path] = content
                            logger.debug(f"添加 {rel_path} ({file_size} 字节)")
                        except Exception as e:
                            logger.warning(f"读取 {rel_path} 失败: {e}")
                            skipped_files.append({
                                "path": rel_path,
                                "size": file_size,
                                "reason": f"read_error: {str(e)}"
                            })
                
                # 获取仓库信息
                repo_info = self._get_repository_info(repo)
                
                result = {
                    "files": files,
                    "stats": {
                        "downloaded_count": len(files),
                        "skipped_count": len(skipped_files),
                        "skipped_files": skipped_files,
                        "repo_url": repo_url,
                        "branch": branch,
                        "include_patterns": list(include_patterns) if include_patterns else None,
                        "exclude_patterns": list(exclude_patterns) if exclude_patterns else None,
                        "max_file_size": max_file_size,
                        "timestamp": datetime.now().isoformat(),
                        "repository_info": repo_info
                    }
                }
                
                logger.info(f"爬取完成: {len(files)} 个文件，跳过 {len(skipped_files)} 个文件")
                return result
                
        except Exception as e:
            logger.error(f"爬取仓库失败: {str(e)}")
            return {
                "files": {},
                "stats": {
                    "error": str(e),
                    "downloaded_count": 0,
                    "skipped_count": 0,
                    "repo_url": repo_url,
                    "branch": branch,
                    "timestamp": datetime.now().isoformat()
                }
            }

    def _should_include_file(
        self,
        file_path: str,
        file_name: str,
        include_patterns: Optional[Set[str]],
        exclude_patterns: Optional[Set[str]]
    ) -> bool:
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
            exclude_file = any(
                fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(file_name, pattern)
                for pattern in exclude_patterns
            )
            return not exclude_file

        return include_file

    def _get_repository_info(self, repo) -> Dict:
        """获取仓库信息"""
        try:
            return {
                "name": os.path.basename(repo.working_dir),
                "current_branch": repo.active_branch.name,
                "latest_commit": {
                    "hash": repo.head.commit.hexsha,
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": repo.head.commit.committed_datetime.isoformat()
                },
                "remote_url": repo.remotes.origin.url if repo.remotes else None
            }
        except Exception as e:
            logger.warning(f"获取仓库信息失败: {e}")
            return {"error": str(e)}

    def get_file_summary(self, files: Dict[str, str]) -> Dict:
        """获取文件摘要信息"""
        if not files:
            return {"total_files": 0, "total_size": 0, "file_types": {}}

        file_types = {}
        total_size = 0

        for file_path, content in files.items():
            # 获取文件扩展名
            _, ext = os.path.splitext(file_path)
            ext = ext.lower() if ext else "no_extension"

            # 统计文件类型
            if ext not in file_types:
                file_types[ext] = {"count": 0, "size": 0}

            file_size = len(content.encode('utf-8'))
            file_types[ext]["count"] += 1
            file_types[ext]["size"] += file_size
            total_size += file_size

        return {
            "total_files": len(files),
            "total_size": total_size,
            "file_types": file_types
        }
    
    def _should_include_file(
        self,
        file_path: str,
        file_name: str,
        include_patterns: Optional[Set[str]],
        exclude_patterns: Optional[Set[str]]
    ) -> bool:
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
            exclude_file = any(
                fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(file_name, pattern)
                for pattern in exclude_patterns
            )
            return not exclude_file
        
        return include_file
