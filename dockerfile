# 构建阶段
FROM python:3.11-slim as builder

WORKDIR /app

# 安装构建依赖（包含完整的Git和SSH）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    git \
    openssh-client \
    ca-certificates && \
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

# 安装运行时依赖（Git + SSH + 根证书）
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    openssh-client \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    # 配置Git全局设置
    git config --global http.sslVerify true && \
    git config --global http.postBuffer 524288000

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 环境变量
ENV PATH="/opt/venv/bin:$PATH"
ENV GIT_PYTHON_REFRESH=quiet
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/{logs,app/logs,agentflow/logs} && \
    chmod -R 777 /app/logs

# 暴露端口
EXPOSE 8080

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]