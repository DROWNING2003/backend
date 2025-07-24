# GitHub仓库学习平台 - API接口文档 v2.0

## API概览

### 基础信息
- **基础URL**: `http://localhost:8001/api`
- **API版本**: v2.0
- **数据格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: JWT Token（待实现）
- **接口格式**: 统一POST格式（提升安全性和灵活性）

### 接口设计原则
- **统一POST格式**: 所有接口均使用POST方法，参数在请求体中传递
- **安全性优先**: 敏感参数不暴露在URL中
- **灵活扩展**: 支持复杂数据结构和筛选条件
- **无长度限制**: 避免URL长度限制问题

### 通用请求头
```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer {token}  # 待实现
```

### 通用响应格式

#### 成功响应
```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

#### 错误响应
```json
{
  "success": false,
  "detail": "错误描述",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

---

## 1. 任务进度管理 API

### 1.1 获取用户学习进度

**接口描述**: 获取用户的学习进度信息，支持筛选特定教程

```http
POST /api/progress/get
```

**请求体**:
```json
{
  "user_id": "user123",
  "tutorial_id": 1  // 可选，不传则获取所有进度
}
```

**响应示例**:
```json
{
  "success": true,
  "user_id": "user123",
  "total": 2,
  "progresses": [
    {
      "id": 1,
      "user_id": "user123",
      "tutorial_id": 1,
      "tutorial_title": "Python基础入门",
      "status": "in_progress",
      "progress_percentage": 45.5,
      "current_step": "第2章：基础语法",
      "total_time_spent": 90,
      "score": 85.0,
      "started_at": "2025-01-01T10:00:00Z",
      "last_accessed_at": "2025-01-02T15:30:00Z",
      "chapter_progresses": [
        {
          "chapter_id": 1,
          "status": "completed",
          "score": 90.0,
          "time_spent": 45,
          "attempts": 1,
          "completed_at": "2025-01-01T11:00:00Z"
        }
      ],
      "extra_data": {
        "achievements": ["first_chapter_completed"],
        "notes": "学习进展顺利"
      }
    }
  ]
}
```

### 1.2 创建用户学习进度

```http
POST /api/progress/create
```

**请求体**:
```json
{
  "user_id": "user123",
  "tutorial_id": 1,
  "initial_data": {
    "source": "web_app",
    "device": "desktop"
  }
}
```

### 1.3 更新用户学习进度

```http
POST /api/progress/update
```

**请求体**:
```json
{
  "user_id": "user123",
  "tutorial_id": 1,
  "progress_data": {
    "status": "in_progress",
    "progress_percentage": 60.0,
    "current_step": "第3章：控制流程",
    "total_time_spent": 120,
    "score": 88.5,
    "extra_data": {
      "last_exercise": "loops_practice",
      "difficulty_rating": 3
    }
  }
}
```

### 1.4 删除用户学习进度

```http
POST /api/progress/delete
```

**请求体**:
```json
{
  "user_id": "user123",
  "tutorial_id": 1
}
```

---

## 2. 课程管理 API

### 2.1 获取课程列表

```http
POST /api/courses
```

**请求体**:
```json
{
  "skip": 0,
  "limit": 10,
  "is_published": true,
  "difficulty": 1,
  "search": "Python"
}
```

### 2.2 获取特定课程

```http
POST /api/courses/detail
```

**请求体**:
```json
{
  "course_id": 1
}
```

---

## 3. GitHub仓库管理 API

### 3.1 分析仓库代码

```http
POST /api/github/analyze
```

### 3.2 获取LLM服务状态

```http
POST /api/github/llm-status
```

---

## 4. AI对话 API

### 4.1 发起对话

```http
POST /api/llm/chat
```

### 4.2 获取对话历史

```http
POST /api/llm/history
```

---

## 5. 文本转语音 API

### 5.1 生成语音文件

```http
POST /api/tts/generate
```

---

## 6. LLM Node服务 API

### 6.1 聊天对话

```http
POST /api/llm-nodes/chat
```

### 6.2 内容分析

```http
POST /api/llm-nodes/analyze
```

### 6.3 代码生成

```http
POST /api/llm-nodes/generate-code
```

### 6.4 文本翻译

```http
POST /api/llm-nodes/translate
```

### 6.5 结构化数据提取

```http
POST /api/llm-nodes/extract-structured
```

### 6.6 批量分析

```http
POST /api/llm-nodes/batch-analysis
```

### 6.7 Node状态检查

```http
POST /api/llm-nodes/node-status
```

---

## 数据模型定义

### UserProgress Schema
```json
{
  "id": "integer",
  "user_id": "string",
  "tutorial_id": "integer",
  "status": "string(not_started|in_progress|completed|paused)",
  "progress_percentage": "float(0-100)",
  "current_step": "string|null",
  "total_time_spent": "integer(minutes)",
  "score": "float",
  "extra_data": "object|null",
  "started_at": "datetime",
  "last_accessed_at": "datetime",
  "completed_at": "datetime|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Tutorial Schema
```json
{
  "id": "integer",
  "title": "string",
  "description": "string|null",
  "difficulty": "string(beginner|intermediate|advanced)",
  "estimated_time": "integer(minutes)",
  "is_active": "boolean",
  "extra_data": "object|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Course Schema
```json
{
  "id": "integer",
  "title": "string",
  "description": "string|null",
  "github_url": "string|null",
  "difficulty": "integer(1-10)",
  "estimated_time": "integer|null",
  "is_published": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 错误处理

### 常见状态码
| 状态码 | 描述 | 示例 |
|--------|------|------|
| 200 | 请求成功 | 正常返回数据 |
| 400 | 请求参数错误 | 参数验证失败 |
| 404 | 资源不存在 | 找不到指定资源 |
| 500 | 服务器内部错误 | 系统异常 |

---

## 开发环境

### 本地开发
- **API地址**: http://localhost:8001/api
- **文档地址**: http://localhost:8001/docs
- **ReDoc地址**: http://localhost:8001/redoc

---

## 更新日志

### v2.0.0 (2025-01-24)
- 重构数据库结构，精简表设计
- 统一所有接口为POST格式
- 移除等级管理，改为任务进度管理
- 新增LLM Node服务API
- 优化数据存储，使用JSON字段提高灵活性
