# 构建阶段
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装依赖到虚拟环境
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -U pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# 运行时阶段
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 确保脚本使用虚拟环境的Python
ENV PATH="/opt/venv/bin:$PATH"

# 复制项目文件
COPY . .

# 创建日志目录
RUN mkdir -p /app/logs && \
    mkdir -p /app/app/logs && \
    mkdir -p /app/agentflow/logs

# 暴露端口（根据构建平台要求调整为8080）
EXPOSE 8080

# 环境变量配置
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV DEBUG=false

# 启动命令（端口同步调整为8080）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]