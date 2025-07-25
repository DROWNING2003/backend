# /check-completion API 使用说明

## 概述

`/check-completion` API 已升级为使用 `check_flow` 进行智能代码检查。该API支持两种输入格式，既保持了向后兼容性，又提供了更强大的文件树检查功能。

## API端点

```
POST /levels/check-completion
```

## 支持的输入格式

### 格式1：文件树格式（推荐）

这是推荐的格式，支持多文件项目和复杂的目录结构。

**请求示例：**
```json
{
  "level_id": 1,
  "course_id": 1,
  "user_file_tree": {
    "type": "directory",
    "uri": "file:///project",
    "children": [
      {
        "type": "file",
        "uri": "file:///project/main.py",
        "content": "def hello():\n    print('Hello, World!')\n\nhello()"
      },
      {
        "type": "file",
        "uri": "file:///project/utils.py",
        "content": "def helper_function():\n    return 'Helper'"
      }
    ]
  }
}
```

**参数说明：**
- `level_id` (int): 关卡ID
- `course_id` (int): 课程ID
- `user_file_tree` (object): 用户提交的文件树结构

### 格式2：字符串格式（兼容模式）

这是为了兼容旧版本API而保留的格式，适用于单文件简单代码。

**请求示例：**
```json
{
  "level_id": 1,
  "user_answer": "def hello():\n    print('Hello, World!')\n\nhello()"
}
```

**参数说明：**
- `level_id` (int): 关卡ID
- `user_answer` (string): 用户提交的代码字符串

## 响应格式

两种输入格式都返回相同的响应结构：

```json
{
  "passed": true,
  "feedback": "很好！你成功实现了要求的功能。代码结构清晰，逻辑正确...",
  "suggestions": [
    "可以添加更多注释来提高代码可读性",
    "考虑添加错误处理机制"
  ]
}
```

**响应字段说明：**
- `passed` (boolean): 是否通过关卡检查
- `feedback` (string): 详细的反馈信息
- `suggestions` (array): 改进建议列表（可选）

## 使用示例

### Python 请求示例

```python
import requests
import json

# 文件树格式请求
def check_with_file_tree():
    url = "http://localhost:8000/levels/check-completion"
    
    data = {
        "level_id": 1,
        "course_id": 1,
        "user_file_tree": {
            "type": "directory",
            "uri": "file:///project",
            "children": [
                {
                    "type": "file",
                    "uri": "file:///project/solution.py",
                    "content": "print('Hello, World!')"
                }
            ]
        }
    }
    
    response = requests.post(url, json=data)
    return response.json()

# 字符串格式请求（兼容模式）
def check_with_string():
    url = "http://localhost:8000/levels/check-completion"
    
    data = {
        "level_id": 1,
        "user_answer": "print('Hello, World!')"
    }
    
    response = requests.post(url, json=data)
    return response.json()
```

### JavaScript 请求示例

```javascript
// 文件树格式请求
async function checkWithFileTree() {
    const response = await fetch('/levels/check-completion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            level_id: 1,
            course_id: 1,
            user_file_tree: {
                type: "directory",
                uri: "file:///project",
                children: [
                    {
                        type: "file",
                        uri: "file:///project/solution.py",
                        content: "print('Hello, World!')"
                    }
                ]
            }
        })
    });
    
    return await response.json();
}

// 字符串格式请求（兼容模式）
async function checkWithString() {
    const response = await fetch('/levels/check-completion', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            level_id: 1,
            user_answer: "print('Hello, World!')"
        })
    });
    
    return await response.json();
}
```

### cURL 请求示例

```bash
# 文件树格式请求
curl -X POST "http://localhost:8000/levels/check-completion" \
     -H "Content-Type: application/json" \
     -d '{
       "level_id": 1,
       "course_id": 1,
       "user_file_tree": {
         "type": "directory",
         "uri": "file:///project",
         "children": [
           {
             "type": "file",
             "uri": "file:///project/main.py",
             "content": "print(\"Hello, World!\")"
           }
         ]
       }
     }'

# 字符串格式请求（兼容模式）
curl -X POST "http://localhost:8000/levels/check-completion" \
     -H "Content-Type: application/json" \
     -d '{
       "level_id": 1,
       "user_answer": "print(\"Hello, World!\")"
     }'
```

## 错误处理

### 常见错误响应

**400 Bad Request - 缺少必要参数**
```json
{
  "detail": "缺少必要参数: level_id"
}
```

**400 Bad Request - 参数格式错误**
```json
{
  "detail": "请提供 user_file_tree + course_id 或 user_answer 参数"
}
```

**404 Not Found - 关卡不存在**
```json
{
  "detail": "关卡 999 不存在"
}
```

**500 Internal Server Error - 服务器错误**
```json
{
  "detail": "检查流程未返回结果"
}
```

## 功能特性

### 1. 智能代码分析
- 使用大语言模型进行代码评判
- 多维度分析：功能完整性、代码正确性、代码质量、创新性
- 提供具体的改进建议和鼓励

### 2. 灵活的输入支持
- **文件树格式**：支持多文件项目，复杂目录结构
- **字符串格式**：兼容旧版API，适用于简单代码

### 3. 标准答案对比
- 自动获取关卡对应的标准实现
- 克隆Git仓库并重置到指定提交
- 智能对比用户代码和标准答案

### 4. 完善的错误处理
- 参数验证和格式检查
- 数据库连接异常处理
- Git仓库访问异常处理
- LLM调用异常处理

## 性能考虑

### 1. 缓存机制
- LLM响应缓存，避免重复调用
- Git仓库克隆结果可复用

### 2. 资源管理
- 自动清理临时目录
- 文件大小限制防止内存溢出

### 3. 超时控制
- 设置合理的超时时间
- 避免长时间阻塞请求

## 最佳实践

### 1. 输入格式选择
- **推荐使用文件树格式**：功能更强大，支持多文件项目
- **字符串格式仅用于简单场景**：单文件代码或向后兼容

### 2. 错误处理
```python
try:
    response = requests.post(url, json=data, timeout=30)
    response.raise_for_status()
    result = response.json()
    
    if result.get('passed'):
        print("✅ 通过检查")
    else:
        print("❌ 未通过检查")
        print(f"反馈: {result.get('feedback')}")
        
except requests.exceptions.Timeout:
    print("请求超时，请稍后重试")
except requests.exceptions.RequestException as e:
    print(f"网络请求失败: {e}")
except Exception as e:
    print(f"处理响应失败: {e}")
```

### 3. 文件树构建
```python
def build_file_tree(files_dict):
    """
    从文件字典构建文件树
    
    Args:
        files_dict: {"path/to/file.py": "file content", ...}
    
    Returns:
        文件树结构
    """
    children = []
    for file_path, content in files_dict.items():
        children.append({
            "type": "file",
            "uri": f"file:///project/{file_path}",
            "content": content
        })
    
    return {
        "type": "directory",
        "uri": "file:///project",
        "children": children
    }
```

## 测试验证

### 运行测试
```bash
# 确保服务运行
uvicorn app.main:app --reload

# 运行API测试
python test_check_completion_api.py
```

### 测试覆盖
- ✅ 文件树格式请求测试
- ✅ 字符串格式请求测试  
- ✅ 无效请求处理测试
- ✅ 错误响应格式测试

## 迁移指南

### 从旧版API迁移

**旧版调用方式：**
```python
# 旧版 - 仍然支持
data = {
    "level_id": 1,
    "user_answer": "print('Hello')"
}
```

**推荐的新方式：**
```python
# 新版 - 推荐使用
data = {
    "level_id": 1,
    "course_id": 1,  # 新增
    "user_file_tree": {  # 替代 user_answer
        "type": "directory",
        "uri": "file:///project",
        "children": [
            {
                "type": "file",
                "uri": "file:///project/main.py",
                "content": "print('Hello')"
            }
        ]
    }
}
```

### 迁移步骤
1. **保持现有代码不变** - 旧版格式仍然支持
2. **逐步迁移到文件树格式** - 获得更强大的功能
3. **更新错误处理逻辑** - 适应新的错误响应格式
4. **测试验证** - 确保迁移后功能正常

## 总结

升级后的 `/check-completion` API 具备以下优势：

✅ **向后兼容** - 支持旧版字符串格式
✅ **功能增强** - 支持多文件项目检查
✅ **智能评判** - 基于LLM的深度代码分析
✅ **标准对比** - 自动获取标准答案进行对比
✅ **完善处理** - 全面的错误处理和资源管理

该API现在可以满足从简单代码检查到复杂项目评估的各种需求。