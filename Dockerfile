FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir feedparser snownlp textblob jieba

# 复制项目文件
COPY . .

# Hugging Face Spaces 需要端口 7860
EXPOSE 7860

# 启动 Streamlit（关闭 CORS 和 XSRF 保护以兼容 HF Spaces iframe）
CMD ["streamlit", "run", "App.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--browser.gatherUsageStats=false"]
