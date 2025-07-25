# 关卡检查流程使用说明

## 概述

这个检查流程用于验证用户提交的代码是否满足关卡要求。流程包括以下步骤：

1. **获取关卡信息** - 从数据库获取关卡要求和描述
2. **克隆仓库** - 克隆课程仓库并重置到指定提交
3. **获取标准答案** - 从指定提交获取标准实现代码
4. **分析用户代码** - 解析用户提交的文件树结构
5. **对比判断** - 使用LLM对比分析并给出评判结果

## 文件结构

```
agentflow/
├── flow.py              # 流程定义，包含 check_flow() 函数
├── nodes.py             # 节点实现，包含所有检查节点
└── utils/
    └── crawl_github_files.py  # Git仓库操作工具

app/routers/
└── levels.py            # API路由，包含 /check-with-flow 端点

check_flow_example.py    # 使用示例
test_check_flow.py       # 测试文件
```

## 核心节点说明

### 1. GetLevelInfoNode
- **功能**: 从数据库获取关卡信息和课程信息
- **输入**: `level_id`, `course_id`
- **输出**: 关卡详情和课程Git URL

### 2. CloneRepoNode
- **功能**: 克隆仓库并重置到指定提交
- **输入**: Git URL, 关卡顺序号
- **输出**: 仓库对象和临时目录

### 3. GetStandardCodeNode
- **功能**: 获取标准答案代码
- **输入**: 临时目录路径
- **输出**: 标准代码文件字典

### 4. AnalyzeUserCodeNode
- **功能**: 解析用户提交的文件树
- **输入**: 用户文件树结构
- **输出**: 用户代码文件字典

### 5. CompareAndJudgeNode
- **功能**: 使用LLM对比并评判
- **输入**: 关卡信息、标准代码、用户代码
- **输出**: 评判结果（通过/不通过、反馈、建议等）

## API使用方法

### 端点: POST /levels/check-with-flow

**请求格式:**
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
        "content": "print('Hello, World!')"
      }
    ]
  }
}
```

**响应格式:**
```json
{
  "passed": true,
  "feedback": "很好！你成功实现了要求的功能...",
  "suggestions": [
    "可以添加更多注释",
    "考虑处理边界情况"
  ]
}
```

## 编程使用方法

### 1. 直接使用Flow

```python
from agentflow.flow import check_flow

# 准备数据
shared = {
    "level_id": 1,
    "course_id": 1,
    "user_file_tree": {
        "type": "directory",
        "uri": "file:///project",
        "children": [...]
    },
    "language": "chinese",
    "use_cache": True
}

# 运行检查流程
flow = check_flow()
flow.run(shared)

# 获取结果
result = shared.get("judgment_result")
print(f"通过: {result['passed']}")
print(f"反馈: {result['feedback']}")
```

### 2. 单独使用判断节点

```python
from agentflow.nodes import CompareAndJudgeNode

# 准备数据
judge_node = CompareAndJudgeNode()
shared = {
    "level_info": {...},
    "standard_code": {...},
    "user_code": {...},
    "use_cache": True,
    "language": "chinese"
}

# 执行判断
prep_res = judge_node.prep(shared)
result = judge_node.exec(prep_res)
```

## 用户文件树格式

用户文件树应该遵循以下格式：

```json
{
  "type": "directory",
  "uri": "file:///project",
  "children": [
    {
      "type": "file",
      "uri": "file:///project/main.py",
      "content": "文件内容..."
    },
    {
      "type": "directory", 
      "uri": "file:///project/utils",
      "children": [
        {
          "type": "file",
          "uri": "file:///project/utils/helper.py",
          "content": "工具函数..."
        }
      ]
    }
  ]
}
```

## 评判标准

LLM会从以下维度评判用户代码：

1. **功能完整性** - 是否实现了关卡要求的功能
2. **代码正确性** - 语法是否正确，逻辑是否合理
3. **代码质量** - 代码风格、命名规范等
4. **创新性** - 是否有独特的实现思路

## 测试方法

运行测试文件验证功能：

```bash
python test_check_flow.py
```

运行示例：

```bash
python check_flow_example.py
```

## 配置选项

- `language`: 输出语言（默认"chinese"）
- `use_cache`: 是否使用LLM缓存（默认True）
- `max_file_size`: 最大文件大小限制（默认1MB）

## 错误处理

流程包含完善的错误处理机制：

- 数据库连接失败
- Git仓库克隆失败
- 文件解析错误
- LLM调用异常
- JSON解析错误

所有错误都会返回适当的错误信息和建议。

## 性能优化

- 使用临时目录管理Git仓库
- 支持LLM响应缓存
- 文件大小限制防止内存溢出
- 自动清理临时资源

## 扩展性

可以轻松添加新的检查节点：

1. 继承`Node`类
2. 实现`prep()`, `exec()`, `post()`方法
3. 在`check_flow()`中连接节点
4. 更新API路由

## 注意事项

1. 确保数据库连接正常
2. Git仓库URL必须可访问
3. 用户文件树格式必须正确
4. LLM服务必须可用
5. 临时目录会自动清理

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库配置
   - 确认数据库服务运行

2. **Git克隆失败**
   - 检查网络连接
   - 验证Git URL格式
   - 确认仓库访问权限

3. **LLM调用失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看LLM服务状态

4. **文件树解析错误**
   - 验证JSON格式
   - 检查必要字段
   - 确认文件内容编码

### 调试方法

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

查看共享数据：

```python
print("调试信息:")
for key, value in shared.items():
    print(f"  {key}: {type(value)}")
```