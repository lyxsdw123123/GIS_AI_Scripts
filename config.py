from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent / ".env")

AMAP_KEY = os.getenv("AMAP_KEY")