# 共享目录问题修复

## 🔍 问题分析

你遇到的问题是每次都显示"现有目录无效，重新克隆"，原因是：

1. **绕过共享目录机制**: 其他代码文件中直接调用 `clone_repository(repo_url, tmpdirname)`，传入了临时目录
2. **使用旧的临时目录**: 这些调用使用 `tempfile.mkdtemp()` 创建的临时目录，而不是共享目录
3. **每次都是新目录**: 临时目录每次都不同，所以无法复用已克隆的仓库

## 🛠️ 修复内容

### 1. 修复的文件

#### `agentflow/nodes.py`
```python
# 修复前
tmpdirname = tempfile.mkdtemp()
repo = clone_repository(git_url, tmpdirname)

# 修复后  
repo = get_or_clone_repository(git_url)
```

#### `app/services/course_service.py`
```python
# 修复前
tmpdirname = tempfile.mkdtemp()
repo = clone_repository(repo_url, tmpdirname)

# 修复后
repo = get_or_clone_repository(repo_url)
```

#### `app/routers/levels.py`
```python
# 修复前
tmpdirname = tempfile.mkdtemp()
repo = clone_repository(course.git_url, tmpdirname)

# 修复后
repo = get_or_clone_repository(course.git_url)
```

### 2. 添加的导入

所有修复的文件都添加了：
```python
from agentflow.utils.crawl_github_files import get_or_clone_repository
```

## ✅ 修复验证

### 测试结果
```
=== 测试共享目录修复 ===

1. 测试仓库: auto_mate_test2.git
   第一次调用... ✅ 克隆成功
   第二次调用... ✅ 使用已存在的仓库目录

2. 测试仓库: auto_mate_test3_call.git  
   第一次调用... ✅ 克隆成功
   第二次调用... ✅ 使用已存在的仓库目录

3. 测试仓库: auto_mate_test4_complex.git
   第一次调用... ✅ 克隆成功
   第二次调用... ✅ 使用已存在的仓库目录

最终目录状态:
- shared_repo_94143d04: 0.04 MB (✅ 共享目录)
- shared_repo_518176b5: 0.03 MB (✅ 共享目录)  
- shared_repo_2c4b0db7: 0.04 MB (✅ 共享目录)
```

## 🎯 修复效果

### 修复前的问题
```
现有目录无效，重新克隆: C:\Users\lulu\AppData\Local\Temp\tmp04xud__3
克隆仓库 https://github.com/zengyi-thinking/auto_mate_test4_complex.git 到目录 C:\Users\lulu\AppData\Local\Temp\tmp04xud__3 ...
```

### 修复后的效果
```
使用已存在的仓库目录: C:\Users\lulu\AppData\Local\Temp\git_crawl_temp\shared_repo_2c4b0db7
```

## 📊 性能提升

1. **避免重复克隆**: 同一个项目只需要克隆一次
2. **目录复用**: 后续操作直接使用已存在的目录
3. **资源节约**: 减少磁盘空间和网络带宽使用
4. **速度提升**: 跳过克隆步骤，直接使用本地仓库

## 🔧 技术细节

### 共享目录命名规则
```python
repo_hash = get_repo_hash(repo_url)  # MD5哈希前8位
target_dir = f"shared_repo_{repo_hash}"
```

### 目录验证机制
```python
if os.path.exists(target_dir):
    try:
        repo = git.Repo(target_dir)
        # 验证远程URL是否匹配
        if repo.remotes.origin.url == repo_url:
            print(f"使用已存在的仓库目录: {target_dir}")
            repo.remotes.origin.fetch()  # 更新到最新状态
            return repo
    except Exception as e:
        print(f"现有目录无效，重新克隆: {e}")
        safe_rmtree(target_dir)
```

## 🚀 使用建议

### 1. 统一使用新函数
```python
# 推荐使用
repo = get_or_clone_repository(repo_url)

# 避免使用（除非有特殊需求）
repo = clone_repository(repo_url, custom_dir)
```

### 2. 定期清理
```python
from agentflow.utils.crawl_github_files import cleanup_temp_directories

# 清理超过24小时的目录
cleanup_temp_directories(max_age_hours=24)
```

### 3. 监控使用情况
```python
from agentflow.utils.crawl_github_files import get_temp_directory_info

info = get_temp_directory_info()
print(f"共享目录数量: {info['total_directories']}")
print(f"总大小: {info['total_size_mb']} MB")
```

## 📝 总结

通过这次修复：

1. ✅ **解决了重复克隆问题**: 现在同一项目会复用已存在的目录
2. ✅ **提升了性能**: 避免了不必要的网络请求和磁盘操作
3. ✅ **保持了并发安全**: 所有操作仍然是线程安全的
4. ✅ **简化了代码**: 移除了手动管理临时目录的代码
5. ✅ **向后兼容**: 现有API调用方式保持不变

现在你的系统会正确使用共享目录，不再出现"现有目录无效，重新克隆"的问题！