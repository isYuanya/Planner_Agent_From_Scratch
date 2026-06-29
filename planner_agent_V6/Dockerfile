FROM python:3.11-slim

WORKDIR /app

# ── 系统依赖 (faiss 运行时可能需要) ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# ── Python 依赖 ──
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── 应用代码 ──
COPY . .

# ── 创建运行时目录 ──
RUN mkdir -p /app/logs /app/persistence

EXPOSE 8000

# ── 健康检查 ──
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# ── 默认: FastAPI 后端 ──
CMD ["uvicorn", "entry.api:app", "--host", "0.0.0.0", "--port", "8000"]
