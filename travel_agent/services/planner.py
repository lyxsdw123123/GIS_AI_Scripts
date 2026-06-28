"""旅行规划核心编排 —— Agent 循环 + Tool Calling"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from travel_agent.services.deepseek import chat
from travel_agent.services import amap
from travel_agent.prompts.system import SYSTEM_PROMPT
from travel_agent.models.user_state import UserState


@dataclass
class AgentResult:
    reply: str
    pois: list[dict] = field(default_factory=list)
    city: str = ""


# ── 工具定义 ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_nearby",
            "description": "搜索用户周边POI（景点/餐厅/公园等），返回名称、地址、坐标、评分",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "关键词，|分隔"},
                    "city": {"type": "string", "description": "城市名"},
                    "location": {"type": "string", "description": "中心点'lng,lat'"},
                    "radius": {"type": "integer", "description": "半径(米)，默认5000"},
                },
                "required": ["keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_citywide",
            "description": "全市范围搜索POI",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "搜索关键词"},
                    "city": {"type": "string", "description": "城市名"},
                },
                "required": ["keywords", "city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询城市天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode",
            "description": "地址转经纬度",
            "parameters": {
                "type": "object",
                "properties": {
                    "address": {"type": "string", "description": "地址"},
                    "city": {"type": "string", "description": "城市名"},
                },
                "required": ["address"],
            },
        },
    },
]


async def execute_tool(name: str, args: dict) -> tuple[str, dict]:
    """执行工具，返回 (给LLM的文本, 元数据)"""
    if name == "search_nearby":
        pois = await amap.search_pois(
            keywords=args.get("keywords", ""),
            city=args.get("city", ""),
            location=args.get("location", ""),
            radius=args.get("radius", 5000),
        )
        return amap.format_poi_list(pois), {"raw_pois": pois, "city": args.get("city", "")}

    if name == "search_citywide":
        pois = await amap.text_search(
            keywords=args.get("keywords", ""),
            city=args.get("city", ""),
        )
        return amap.format_poi_list(pois), {"raw_pois": pois, "city": args.get("city", "")}

    if name == "get_weather":
        data = await amap.get_weather(args.get("city", ""))
        return amap.format_weather(data), {"city": args.get("city", "")}

    if name == "geocode":
        data = await amap.geocode(args.get("address", ""), args.get("city", ""))
        geocodes = data.get("geocodes", [])
        if not geocodes:
            return "未找到该地址的坐标", {}
        g = geocodes[0]
        return f"地址: {g.get('formatted_address')}, 坐标: {g.get('location')}", {}

    return f"未知工具: {name}", {}


def _extract_poi_coords(raw_pois: list[dict]) -> list[dict]:
    """提取名称+坐标用于前端地图标注"""
    result = []
    for p in raw_pois:
        loc = p.get("location", "")
        if loc:
            lng, lat = loc.split(",")
            result.append({
                "name": p.get("name", "未知"),
                "address": p.get("address", ""),
                "lng": float(lng),
                "lat": float(lat),
                "rating": p.get("biz_ext", {}).get("rating", "") or p.get("deep_info", {}).get("rating", ""),
            })
    return result


def _build_state_context(state: UserState) -> str:
    """将结构化用户状态转为注入 System Prompt 的上下文"""
    if not state.is_ready():
        return ""
    parts = []
    parts.append(f"\n\n## 当前用户画像（来自UI输入，直接使用不要追问）")
    parts.append(f"- 📍 位置：{state.location}")
    parts.append(f"- 😊 心情：{state.mood}/10")
    parts.append(f"- ⚡ 疲惫度：{state.fatigue}/10")
    parts.append(f"- 🔍 好奇心：{state.curiosity}/10")
    if state.companion:
        parts.append(f"- 👥 同行者：{state.companion}")
    if state.preferences:
        parts.append(f"- 💡 偏好：{state.preferences}")
    if state.budget:
        parts.append(f"- 💰 预算：{state.budget}")
    return "\n".join(parts)


async def run_agent(user_message: str, history: list[dict], user_state: UserState | None = None) -> AgentResult:
    system_content = SYSTEM_PROMPT
    if user_state and user_state.is_ready():
        system_content += _build_state_context(user_state)

    messages = [{"role": "system", "content": system_content}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    captured_pois: list[dict] = []
    captured_city = ""
    has_searched = False

    for _ in range(3):
        response = await chat(messages, tools=TOOLS)

        # 无工具调用 → 检查是否已搜索
        if "tool_calls" not in response:
            if not has_searched:
                messages.append(response)
                messages.append({
                    "role": "system",
                    "content": "你必须先调用搜索工具获取真实数据，不能凭训练知识推荐。请调用 search_nearby 或 search_citywide。",
                })
                continue
            return AgentResult(
                reply=response.get("content", ""),
                pois=captured_pois,
                city=captured_city,
            )

        messages.append(response)
        tool_calls = response["tool_calls"]

        # 并行执行所有工具调用
        async def run_one(tc: dict):
            func = tc["function"]
            name = func["name"]
            if name in ("search_nearby", "search_citywide"):
                nonlocal has_searched
                has_searched = True
            try:
                args = json.loads(func["arguments"])
            except json.JSONDecodeError:
                args = {}
            try:
                text, meta = await asyncio.wait_for(execute_tool(name, args), timeout=15.0)
            except (asyncio.TimeoutError, Exception):
                text, meta = f"[{name} 超时]", {}
            return {"tc": tc, "text": text, "meta": meta}

        results = await asyncio.gather(*[run_one(tc) for tc in tool_calls])

        for r in results:
            meta = r["meta"]
            raw_pois = meta.get("raw_pois")
            if raw_pois:
                captured_pois.extend(_extract_poi_coords(raw_pois))
            if meta.get("city"):
                captured_city = meta["city"] or captured_city

            messages.append({
                "role": "tool",
                "tool_call_id": r["tc"]["id"],
                "content": r["text"],
            })

    final = await chat(messages)
    return AgentResult(
        reply=final.get("content", ""),
        pois=captured_pois,
        city=captured_city,
    )
