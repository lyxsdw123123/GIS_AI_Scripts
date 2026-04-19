from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

AMAP_KEY = os.getenv("AMAP_KEY")
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")