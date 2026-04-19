# natural_language_to_map.py

import requests
import folium
from pathlib import Path
import sys

# ==================================================
# 🔥 关键：解决 config.py 在上级目录的问题
# ==================================================

# 当前文件：natural_language_to_map.py
# parents[0] = natural_language_to_map
# parents[1] = AI_Learning
# parents[2] = GIS_AI_Scripts（config.py 所在目录）

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import AMAP_KEY
from llm_backend import parse_query


# ==================================================
# 输出目录
# ==================================================
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================================================
# 调用高德POI
# ==================================================
def get_poi(city, keyword):
    url = "https://restapi.amap.com/v3/place/text"

    params = {
        "key": AMAP_KEY,
        "keywords": keyword,
        "city": city,
        "offset": 20,
        "page": 1
    }

    res = requests.get(url, params=params)
    data = res.json()

    return data.get("pois", [])


# ==================================================
# 生成地图
# ==================================================
def create_map(city, keyword, pois):
    if not pois:
        print("❌ 未找到数据")
        return

    lng, lat = pois[0]["location"].split(",")

    m = folium.Map(
        location=[float(lat), float(lng)],
        zoom_start=12
    )

    for poi in pois:
        name = poi["name"]
        addr = poi.get("address", "无地址")
        lng, lat = poi["location"].split(",")

        folium.Marker(
            location=[float(lat), float(lng)],
            popup=f"{name}<br>{addr}",
            tooltip=name
        ).add_to(m)

    # 输出文件
    filename = f"{city}_{keyword}_分布地图.html"
    save_path = OUTPUT_DIR / filename

    m.save(str(save_path))

    print("✅ 地图已生成：")
    print(save_path)


# ==================================================
# 主函数
# ==================================================
def main():
    query = input("请输入需求（如：长沙高校分布）：")

    city, keyword = parse_query(query)

    if not city:
        print("❌ 未识别城市")
        return

    if not keyword:
        print("❌ 未识别类别")
        return

    print(f"📍 城市：{city}")
    print(f"📌 类别：{keyword}")

    pois = get_poi(city, keyword)

    create_map(city, keyword, pois)


if __name__ == "__main__":
    main()
