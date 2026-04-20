import json
import requests
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from config import DASHSCOPE_API_KEY, QWEN_MODEL


def call_qwen(messages, model: str | None = None, temperature: float = 0.2, max_tokens: int = 512, timeout: int = 20):
    if not DASHSCOPE_API_KEY:
        return None

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or QWEN_MODEL,
        "input": {"messages": messages},
        "parameters": {
            "result_format": "message",
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=timeout)
        data = res.json()
    except Exception:
        return None

    try:
        content = data["output"]["choices"][0]["message"]["content"]
    except Exception:
        return None

    return content if isinstance(content, str) and content.strip() else None


def call_qwen_json(messages, **kwargs):
    content = call_qwen(messages, **kwargs)
    if not content:
        return None

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(content[start : end + 1])
    except Exception:
        return None


def parse_query(query: str):
    query = (query or "").strip()
    if not query:
        return None, None

    system_prompt = (
        "你是地图POI检索参数解析器。"
        "把用户输入解析成严格JSON，只能包含字段：city, keyword。"
        "city: 城市名（不带“市”），未明确给出则为null。"
        "keyword: 用于POI检索的核心关键词，去掉“分布/地图/哪里/查询/推荐/周边/附近”等无关词。"
        "只输出JSON，不要输出解释或Markdown。"
    )

    obj = call_qwen_json(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        temperature=0.2,
        max_tokens=256,
    )
    print(f"llm_json={json.dumps(obj, ensure_ascii=False)}")

    city = None
    keyword = None
    if isinstance(obj, dict):
        c = obj.get("city")
        if isinstance(c, str) and c.strip():
            city = c.strip().removesuffix("市")
        k = obj.get("keyword")
        if isinstance(k, str) and k.strip():
            keyword = k.strip()

    if keyword:
        return city, keyword

    return None, None
