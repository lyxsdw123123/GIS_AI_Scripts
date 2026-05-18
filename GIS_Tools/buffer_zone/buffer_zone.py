import argparse
import os
import sys

import folium
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import prepared

REQUIRED_COLS = ("name", "lat", "lon")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="点位缓冲区分析 — 生成缓冲区、可视化地图、叠加分析、统计输出"
    )
    parser.add_argument("--xlsx", default=None, help="输入 Excel 路径；默认 data/points.xlsx")
    parser.add_argument("--outdir", default=None, help="输出目录；默认 output/")
    parser.add_argument("--radius", type=str, default="500", help="缓冲半径（米），多个用逗号分隔，如 500,1000,1500")
    parser.add_argument("--dissolve", action="store_true", help="合并所有重叠缓冲区")
    parser.add_argument("--pois", default=None, help="叠加分析用 POI Excel，默认不叠加")
    parser.add_argument("--zoom", type=int, default=13, help="地图缩放级别（默认 13）")
    parser.add_argument("--no-html", action="store_true", help="不生成 HTML 地图")
    return parser.parse_args()


def load_points(xlsx_path: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Excel 缺少字段: {sorted(missing)}；当前字段: {list(df.columns)}")
    df = df.copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("没有可用的坐标点")
    return df


def to_geo_dataframe(df: pd.DataFrame) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        df, geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])], crs="EPSG:4326"
    )


def get_utm_epsg(lon: float, lat: float) -> int:
    zone = int((lon + 180) / 6) + 1
    return 32600 + zone if lat >= 0 else 32700 + zone


def create_buffers(
    gdf: gpd.GeoDataFrame, radii: list[float], dissolve: bool
) -> list[tuple[float, gpd.GeoDataFrame]]:
    lon, lat = gdf["lon"].mean(), gdf["lat"].mean()
    epsg = get_utm_epsg(lon, lat)
    proj_gdf = gdf.to_crs(epsg)

    results = []
    for r in sorted(radii):
        buf = proj_gdf.buffer(r)
        buf_gdf = gpd.GeoDataFrame(geometry=buf, crs=epsg).to_crs(4326)
        if dissolve:
            buf_gdf = gpd.GeoDataFrame(geometry=[buf_gdf.union_all()], crs=4326)
            buf_gdf["name"] = f"buffer_{r}m"
        else:
            buf_gdf["name"] = [f"{n}_{r}m" for n in gdf["name"]]
        results.append((r, buf_gdf))
    return results


def spatial_stats(
    buf_gdf: gpd.GeoDataFrame,
    poi_gdf: gpd.GeoDataFrame | None,
    radius: float,
) -> dict:
    area_km2 = sum(g.area for g in buf_gdf.geometry) * 111320**2 / 1e6
    result = {"radius_m": radius, "area_km2": round(area_km2, 4)}

    if poi_gdf is not None:
        union_buf = buf_gdf.union_all()
        prepared_buf = prepared.prep(union_buf)
        inside = poi_gdf.geometry.apply(lambda g: prepared_buf.contains(g))
        result["poi_inside"] = int(inside.sum())
        result["poi_total"] = len(poi_gdf)
        result["poi_pct"] = round(inside.sum() / len(poi_gdf) * 100, 1)
    return result


def build_map(
    gdf: gpd.GeoDataFrame,
    buffers: list[tuple[float, gpd.GeoDataFrame]],
    poi_gdf: gpd.GeoDataFrame | None,
    zoom_start: int,
) -> folium.Map:
    m = folium.Map(location=[gdf["lat"].mean(), gdf["lon"].mean()], zoom_start=zoom_start)

    for _, row in gdf.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=str(row["name"]),
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    colors = ["orange", "red", "purple", "green", "blue", "darkred"]
    for i, (radius, buf_gdf) in enumerate(buffers):
        color = colors[i % len(colors)]
        folium.GeoJson(
            buf_gdf,
            name=f"缓冲区 {radius}m",
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": 0.2,
            },
            tooltip=folium.GeoJsonTooltip(fields=["name"], labels=False),
        ).add_to(m)

    if poi_gdf is not None:
        for _, row in poi_gdf.iterrows():
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=4,
                color="green",
                fill=True,
                fill_opacity=0.7,
                popup=str(row.get("name", "")),
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def print_stats(all_stats: list[dict]) -> None:
    print("\n" + "=" * 50)
    print("缓冲区统计")
    print("=" * 50)
    has_poi = any("poi_inside" in s for s in all_stats)
    header = f"{'半径':>8}  {'面积(km²)':>12}"
    if has_poi:
        header += f"  {'POI覆盖':>10}  {'占比':>8}"
    print(header)
    print("-" * 50)
    for s in all_stats:
        line = f"{s['radius_m']:>6}m  {s['area_km2']:>10.4f}"
        if "poi_inside" in s:
            line += f"  {s['poi_inside']:>4}/{s['poi_total']:<4}  {s['poi_pct']:>6}%"
        print(line)
    print("=" * 50 + "\n")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    base_dir = os.path.dirname(__file__)

    xlsx_path = args.xlsx or os.path.join(base_dir, "data", "points.xlsx")
    output_dir = args.outdir or os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    radii = [float(r.strip()) for r in args.radius.split(",")]

    df = load_points(xlsx_path)
    gdf = to_geo_dataframe(df)

    buffers = create_buffers(gdf, radii, args.dissolve)

    poi_gdf = None
    if args.pois:
        poi_df = load_points(args.pois)
        poi_gdf = to_geo_dataframe(poi_df)

    all_stats = []
    for radius, buf_gdf in buffers:
        stat = spatial_stats(buf_gdf, poi_gdf, radius)
        all_stats.append(stat)
    print_stats(all_stats)

    if not args.no_html:
        m = build_map(gdf, buffers, poi_gdf, args.zoom)
        html_path = os.path.join(output_dir, "buffer.html")
        m.save(html_path)
        print(f"地图已保存: {html_path}")

    for radius, buf_gdf in buffers:
        buf_gdf.to_file(
            os.path.join(output_dir, f"buffer_{radius}m.geojson"), driver="GeoJSON"
        )
        print(f"缓冲区已导出: buffer_{radius}m.geojson")

    if poi_gdf is not None:
        union_all = gpd.GeoDataFrame(
            geometry=[gpd.GeoDataFrame(pd.concat([b[1] for b in buffers])).union_all()],
            crs=4326,
        )
        covered = poi_gdf[poi_gdf.geometry.apply(lambda g: union_all.geometry.iloc[0].contains(g))]
        covered_out = os.path.join(output_dir, "covered_pois.xlsx")
        covered[["name", "lat", "lon"]].to_excel(covered_out, index=False)
        print(f"覆盖的 POI 已导出: {covered_out}")


if __name__ == "__main__":
    main()
