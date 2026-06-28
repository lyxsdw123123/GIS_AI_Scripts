"""高德地图 Web API 封装（带内存缓存）"""
from __future__ import annotations

import time
import httpx
from travel_agent.config import AMAP_KEY

BASE_URL = "https://restapi.amap.com/v3"

# 简单内存缓存：同一会话内避免重复 API 调用
_cache: dict[str, tuple[float, any]] = {}
CACHE_TTL = 300  # 5 分钟


def _cache_key(prefix: str, **params) -> str:
    return prefix + ":" + ",".join(f"{k}={v}" for k, v in sorted(params.items()) if v)


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, value):
    _cache[key] = (time.time(), value)


async def _get(path: str, params: dict) -> dict:
    params["key"] = AMAP_KEY
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}{path}", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            raise RuntimeError(f"高德API错误: {data.get('info')}")
        return data


async def search_pois(
    keywords: str,
    city: str = "",
    location: str = "",
    radius: int = 5000,
    types: str = "",
    offset: int = 10,
) -> list[dict]:
    """
    周边 POI 搜索（带缓存）。
    """
    ck = _cache_key("pois", keywords=keywords, city=city, location=location, radius=str(radius), types=types)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    params = {
        "keywords": keywords,
        "offset": offset,
        "extensions": "all",
    }
    if location:
        params["location"] = location
        params["radius"] = radius
    elif city:
        params["city"] = city
    else:
        raise ValueError("必须提供 city 或 location")

    if types:
        params["types"] = types

    data = await _get("/place/around", params)
    result = data.get("pois", [])
    _cache_set(ck, result)
    return result


async def text_search(
    keywords: str,
    city: str = "",
    citylimit: bool = True,
) -> list[dict]:
    """关键词搜索 POI（全市范围，带缓存）"""
    ck = _cache_key("text", keywords=keywords, city=city)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    params = {
        "keywords": keywords,
        "city": city,
        "citylimit": str(citylimit).lower(),
        "offset": 10,
        "extensions": "all",
    }
    data = await _get("/place/text", params)
    result = data.get("pois", [])
    _cache_set(ck, result)
    return result


async def get_weather(city: str) -> dict:
    """获取城市实时天气和预报（带缓存）"""
    ck = _cache_key("weather", city=city)
    cached = _cache_get(ck)
    if cached is not None:
        return cached

    from travel_agent.config import AMAP_KEY
    import httpx

    params = {"key": AMAP_KEY, "city": city, "extensions": "all"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{BASE_URL}/weather/weatherInfo", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            raise RuntimeError(f"天气查询失败: {data.get('info')}")
        _cache_set(ck, data)
        return data


async def geocode(address: str, city: str = "") -> dict:
    """地理编码：地址 → 坐标"""
    params = {"address": address}
    if city:
        params["city"] = city
    return await _get("/geocode/geo", params)


def _format_poi(p: dict) -> str:
    """格式化单个 POI 为一行摘要"""
    name = p.get("name", "未知")
    addr = p.get("address", "")
    biz_ext = p.get("biz_ext", {}) or {}
    deep_info = p.get("deep_info", {}) or {}
    rating = biz_ext.get("rating", "") or deep_info.get("rating", "")
    cost = biz_ext.get("cost", "") or deep_info.get("cost", "")
    tel = p.get("tel", "") or deep_info.get("tel", "")

    parts = [f"- **{name}**"]
    if addr:
        parts.append(f"  {addr}")
    if rating:
        parts.append(f"  评分 {rating}")
    if cost:
        parts.append(f"  人均 ¥{cost}")
    if tel:
        parts.append(f"  电话 {tel}")
    return "\n".join(parts)


def format_poi_list(pois: list[dict]) -> str:
    if not pois:
        return "未找到相关地点。"
    return "\n\n".join(_format_poi(p) for p in pois[:10])


def format_weather(data: dict) -> str:
    """格式化天气信息为人读文本"""
    forecasts = data.get("forecasts", [])
    if not forecasts:
        return "未获取到天气信息。"

    lines = []
    for f in forecasts:
        lines.append(f"**{f.get('city', '')}**  {f.get('reporttime', '')}")
        for cast in f.get("casts", []):
            lines.append(
                f"  {cast.get('date')} {cast.get('week')}: "
                f"{cast.get('dayweather')}/{cast.get('nightweather')}, "
                f"{cast.get('nighttemp')}°C~{cast.get('daytemp')}°C, "
                f"{cast.get('daywind')}风"
            )
    return "\n".join(lines)
