import logging
import os
from config import LOG_PATH

# ── 关掉三方库的 stderr 输出 (tqdm 进度条 / HF 警告等) ──
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

os.makedirs("logs", exist_ok=True)

# ── 根 logger 配置 ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

# ── 业务 logger ──
from config import DEBUG  # noqa: E402

logger = logging.getLogger("planner_agent")
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

# ── 压制三方库噪音 ──
for noisy in [
    "openai",
    "httpx",
    "httpcore",
    "urllib3",
    "sentence_transformers",
    "huggingface_hub",
    "faiss",
    "PIL",
    "tqdm",
    "filelock",
]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

# ── 彻底关掉 openai HTTP 请求日志 ──
logging.getLogger("openai._base_client").setLevel(logging.WARNING)

# ── 关掉 HF Hub 未认证警告 ──
logging.getLogger("huggingface_hub.utils").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.file_download").setLevel(logging.ERROR)

# ── 关掉 tqdm 进度条 ──
logging.getLogger("tqdm").setLevel(logging.ERROR)