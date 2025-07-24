# GitHub仓库学习平台 - 后端API

一个帮助用户学习GitHub仓库的教育平台后端API，基于FastAPI构建。

## 功能特性

- 🎯 **等级管理** - 用户学习等级系统
- 📚 **课程管理** - GitHub仓库课程管理
- 🤖 **AI对话** - 集成LLM提供智能学习助手
- 🔊 **文本转语音** - 支持多语言TTS功能
- 🗄️ **数据库支持** - MySQL数据库集成
- 📝 **API文档** - 自动生成的API文档
- 🔒 **安全认证** - JWT令牌认证（待实现）

## 技术栈

- **框架**: FastAPI 0.104.1
- **数据库**: MySQL + SQLAlchemy 2.0
- **异步**: uvicorn + httpx
- **数据验证**: Pydantic 2.5
- **文档**: 自动生成OpenAPI文档

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口点
│   ├── routers/             # API路由
│   │   ├── __init__.py
│   │   ├── levels.py        # 等级管理API
│   │   ├── courses.py       # 课程管理API
│   │   ├── llm.py          # LLM对话API
│   │   └── tts.py          # 文本转语音API
│   ├── services/            # 业务逻辑层
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   ├── level.py         # 等级模型
│   │   └── course.py        # 课程模型
│   ├── schemas/             # Pydantic Schema
│   │   ├── __init__.py
│   │   ├── level.py         # 等级Schema
│   │   ├── course.py        # 课程Schema
│   │   ├── llm.py          # LLM Schema
│   │   └── tts.py          # TTS Schema
│   ├── database/            # 数据库配置
│   │   ├── __init__.py
│   │   └── connection.py    # 数据库连接
│   └── utils/               # 工具类
│       ├── __init__.py
│       ├── llm_client.py    # LLM客户端
│       └── tts_client.py    # TTS客户端
├── requirements.txt         # 依赖包列表
├── .env.example            # 环境变量模板
└── README.md               # 项目说明
```

## 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.8+
- MySQL 5.7+
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库连接和API密钥：

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/github_learning_platform
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 创建数据库

在MySQL中创建数据库：

```sql
CREATE DATABASE github_learning_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. 启动应用

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

应用将在 http://localhost:8000 启动。

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端点

### 等级管理
- `GET /api/levels` - 获取等级列表
- `GET /api/levels/{level_id}` - 获取特定等级
- `POST /api/levels/check` - 检查用户等级

### 课程管理
- `GET /api/courses` - 获取课程列表
- `GET /api/courses/{course_id}` - 获取特定课程

### AI对话
- `POST /api/llm/chat` - 与AI助手对话
- `GET /api/llm/conversations/{conversation_id}` - 获取对话历史

### 文本转语音
- `POST /api/tts/generate` - 生成语音文件
- `POST /api/tts/generate-async` - 异步生成语音
- `GET /api/tts/status/{task_id}` - 获取任务状态

## 开发指南

### 添加新的API端点

1. 在 `app/routers/` 中创建新的路由文件
2. 在 `app/schemas/` 中定义相应的Pydantic Schema
3. 在 `app/models/` 中定义数据模型（如需要）
4. 在 `app/main.py` 中注册新路由

### 数据库迁移

使用Alembic进行数据库迁移：

```bash
# 初始化迁移
alembic init alembic

# 创建迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 部署

### Docker部署（推荐）

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境配置

1. 设置环境变量 `DEBUG=false`
2. 配置反向代理（Nginx）
3. 使用进程管理器（Supervisor/systemd）
4. 配置日志轮转
5. 设置监控和告警

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。
