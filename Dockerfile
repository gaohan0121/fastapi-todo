# 使用官方 Python 基础镜像，体积较小
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
# --no-cache-dir 减少镜像层大小
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有文件到容器
COPY . .

# 暴露 FastAPI 运行的端口
EXPOSE 8000

# 运行应用的命令
# --host 0.0.0.0 是必须的，让应用监听所有网络接口
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]