"""从父目录 .env 加载配置"""
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# 确保能加载到根目录的 .env
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")

AMAP_KEY = os.getenv("AMAP_KEY")
AMAP_JS_KEY = os.getenv("AMAP_JS_KEY", AMAP_KEY)  # JS API key（需开通Web端JS API服务）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
