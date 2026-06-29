
import os

from dotenv import load_dotenv

# 加载 .env
load_dotenv()

# ==========================
# LLM
# ==========================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

LLM_MODEL = "deepseek-chat"

# ==========================
# Web Search
# ==========================

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ==========================
# Database
# ==========================

BASE_DIR = os.path.dirname(__file__)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "persistence",
    "agent.db"
)

# ==========================
# Logging
# ==========================

LOG_PATH = os.path.join(
    BASE_DIR,
    "logs",
    "agent.log"
)

# ==========================
# RAG
# ==========================

TOOLS_DIR = os.path.join(
    BASE_DIR,
    "tools"
)

RAG_INDEX_PATH = os.path.join(
    TOOLS_DIR,
    "knowledge.index"
)

RAG_CHUNK_PATH = os.path.join(
    TOOLS_DIR,
    "chunks.pkl"
)

# ==========================
# FastAPI
# ==========================

HOST = "127.0.0.1"

PORT = 8000

# ==========================
# Debug
# ==========================

DEBUG = True