import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")


def _resolve_path(value: str) -> Path:
    """把配置中的相对路径统一解析到项目根目录。"""
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "local-deepseek-data-agent"
)

DATABASE_PATH = _resolve_path(
    os.getenv("DATABASE_PATH", "retail.db")
)

SALES_DATA_FILE = _resolve_path(
    os.getenv(
        "SALES_DATA_FILE",
        "datasets/02_真实零售交易大数据/Online_Retail.xlsx",
    )
)

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))
