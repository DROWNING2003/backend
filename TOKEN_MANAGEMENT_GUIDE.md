# Token管理解决方案

## 问题描述

当处理大量代码或长文本时，可能会遇到以下错误：
```
openai.BadRequestError: Error code: 400 - {'error': {'message': 'Invalid request: Your request exceeded model token limit: 131072', 'type': 'invalid_request_error'}}
```

这表示请求超过了模型的token限制（131,072 tokens）。

## 解决方案

我们实现了一个完整的token管理系统来自动处理这个问题：

### 1. 自动Token检查和截断

在 `call_llm` 函数中添加了自动token检查：

```python
from agentflow.utils.call_llm import call_llm

# 现在会自动检查和截断过长的prompt
response = call_llm(long_prompt, use_cache=True, max_tokens=120000)
```

### 2. 智能内容截断

#### 文件内容截断
```python
from agentflow.utils.token_manager import token_manager

# 截断文件内容，每个文件最多3000 tokens
truncated_files = token_manager.truncate_files_content(files_data, max_tokens_per_file=3000)
```

#### Diff内容截断
```python
# 智能截断diff内容，保留最重要的变更
truncated_diff = token_manager.truncate_diff_content(diff_lines, max_lines=50)
```

#### 通用文本截断
```python
# 截断任意文本到指定token数量
truncated_text = token_manager.truncate_text(long_text, max_tokens=10000)
```

### 3. Prompt优化

#### 抽象概念识别优化
```python
optimized_context, optimized_prompt = token_manager.optimize_prompt_for_abstractions(
    context, file_listing, base_prompt, max_context_tokens=100000
)
```

#### 关卡生成优化
```python
optimized_buffer, optimized_prompt = token_manager.optimize_prompt_for_level_generation(
    buffer, base_prompt, max_buffer_tokens=80000
)
```

## 已优化的节点

### 1. IdentifyAbstractions节点
- 自动截断文件内容（每个文件最多3000 tokens）
- 优化整体prompt结构
- 使用安全的LLM调用

### 2. ToLevelConverter节点
- 智能截断diff内容（每个文件最多50行）
- 优化变更详情buffer
- 控制总体prompt长度

### 3. EvaluateContextWorthiness节点
- 截断变更摘要
- 使用安全的LLM调用

## 使用建议

### 1. 监控Token使用
```python
from agentflow.utils.token_manager import count_tokens

# 检查文本的token数量
token_count = count_tokens(your_text)
print(f"Token数量: {token_count}")
```

### 2. 调整截断参数

根据你的需求调整截断参数：

```python
# 更严格的文件截断
truncated_files = token_manager.truncate_files_content(files_data, max_tokens_per_file=2000)

# 更严格的diff截断
truncated_diff = token_manager.truncate_diff_content(diff_lines, max_lines=30)
```

### 3. 使用安全的LLM调用

```python
from agentflow.utils.token_manager import safe_call_llm

# 自动处理token限制的LLM调用
response = safe_call_llm(prompt, use_cache=True, max_tokens=100000)
```

## 配置选项

### 默认Token限制
- 最大prompt tokens: 120,000
- 文件内容截断: 3,000 tokens/文件
- Diff内容截断: 50行/文件
- 变更摘要截断: 10,000 tokens

### 自定义配置

你可以通过修改以下参数来调整行为：

```python
# 在call_llm中设置更严格的限制
response = call_llm(prompt, max_tokens=80000)

# 在token_manager中调整截断参数
token_manager = TokenManager(model_name="gpt-4", max_tokens=100000)
```

## 监控和调试

### 日志输出
系统会自动记录token使用情况：

```
INFO:agentflow.nodes:文件 large_file.py 被截断: 5000 -> 3000 tokens
WARNING:llm_logger:Prompt过长 (150000 tokens)，截断到 120000 tokens
INFO:agentflow.nodes:变更详情token数: 8500
```

### 测试Token管理
运行测试脚本验证功能：

```bash
python test_token_management.py
```

## 最佳实践

1. **预防性截断**: 在构建prompt之前就截断内容
2. **保留重要信息**: 优先保留代码变更和关键信息
3. **监控使用**: 定期检查token使用情况
4. **渐进式截断**: 如果仍然超限，进一步减少token数量
5. **缓存使用**: 启用缓存避免重复的昂贵调用

## 故障排除

### 如果仍然遇到token限制错误：

1. **检查token数量**:
   ```python
   print(f"Prompt tokens: {count_tokens(your_prompt)}")
   ```

2. **进一步减少内容**:
   ```python
   # 更严格的截断
   call_llm(prompt, max_tokens=50000)
   ```

3. **分批处理**:
   将大任务分解为多个小任务

4. **检查累积变更**:
   如果累积了太多提交，考虑重置累积状态

通过这些改进，你的系统现在可以自动处理token限制问题，确保稳定运行。