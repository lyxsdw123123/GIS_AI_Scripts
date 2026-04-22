# natural_language_to_map.py

import requests
import folium
from folium.plugins import HeatMap
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


def get_district_boundary(city):
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": AMAP_KEY,
        "keywords": city,
        "subdistrict": 0,
        "extensions": "all"
    }

    res = requests.get(url, params=params)
    data = res.json()
    districts = data.get("districts", [])
    if not districts:
        return []

    polyline = districts[0].get("polyline", "")
    if not polyline:
        return []

    polygons = []
    for polygon_text in polyline.split("|"):
        points = []
        for point_text in polygon_text.split(";"):
            if not point_text:
                continue
            lng, lat = point_text.split(",")
            points.append([float(lat), float(lng)])
        if points:
            polygons.append(points)

    return polygons


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

    boundary_group = folium.FeatureGroup(name=f"{city}行政区边界")
    marker_group = folium.FeatureGroup(name=f"{keyword}点位")
    heat_data = []

    district_polygons = get_district_boundary(city)
    for polygon in district_polygons:
        folium.Polygon(
            locations=polygon,
            color="blue",
            weight=2,
            fill=True,
            fill_color="blue",
            fill_opacity=0.08,
            popup=f"{city}行政区边界"
        ).add_to(boundary_group)
    boundary_group.add_to(m)

    for poi in pois:
        name = poi["name"]
        addr = poi.get("address", "无地址")
        lng, lat = poi["location"].split(",")
        lat_f = float(lat)
        lng_f = float(lng)

        heat_data.append([lat_f, lng_f])

        folium.Marker(
            location=[lat_f, lng_f],
            popup=f"{name}<br>{addr}",
            tooltip=name
        ).add_to(marker_group)
    marker_group.add_to(m)

    HeatMap(
        heat_data,
        name=f"{keyword}热力图",
        radius=18,
        blur=12,
        min_opacity=0.3
    ).add_to(m)

    folium.LayerControl().add_to(m)

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
    print(f"city={city}, keyword={keyword}")

    pois = get_poi(city, keyword)

    create_map(city, keyword, pois)


if __name__ == "__main__":
    main()
