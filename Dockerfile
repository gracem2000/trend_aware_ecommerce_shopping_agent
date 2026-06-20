# 热点电商导购系统（Streamlit）—— 容器镜像
FROM python:3.12-slim

WORKDIR /app

# 装依赖（利用 docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷代码（.dockerignore 会排除 .venv / data / __pycache__ 等）
COPY . .

# 数据目录：PaaS 把持久卷挂到 /data，否则数据写在容器内（重新部署会丢）
RUN mkdir -p /data
ENV DATABASE_PATH=/data/app.db \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8501

# PaaS 注入 PORT；本地默认 8501
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]
