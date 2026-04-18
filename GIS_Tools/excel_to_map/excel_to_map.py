import argparse
import os

import folium
import pandas as pd

#Excel(name/lat/lon) -> output\map.html；可选导出 output\points.geojson / output\points.shp
REQUIRED_COLS=("name","lat","lon")

def parse_args() -> argparse.Namespace:
    parser=argparse.ArgumentParser()
    parser.add_argument("--xlsx", default=None)
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--zoom", type=int, default=12)
    parser.add_argument("--no-html", action="store_true")
    parser.add_argument("--geojson", action="store_true")
    parser.add_argument("--shp", action="store_true")
    parser.add_argument("--html-path", default=None)
    parser.add_argument("--geojson-path", default=None)
    parser.add_argument("--shp-path", default=None)
    return parser.parse_args()

def resolve_output_path(output_dir: str, provided_path: str | None, default_name: str) -> str:
    if not provided_path:
        return os.path.join(output_dir, default_name)
    if os.path.isabs(provided_path):
        return provided_path
    return os.path.join(output_dir, provided_path)

#读取数据
def load_points(xlsx_path: str) -> pd.DataFrame:
    df=pd.read_excel(xlsx_path)

    missing=set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"Excel 缺少字段: {sorted(missing)}；当前字段: {list(df.columns)}")

    df=df.copy()
    df["lat"]=pd.to_numeric(df["lat"], errors="coerce")
    df["lon"]=pd.to_numeric(df["lon"], errors="coerce")
    df=df.dropna(subset=["lat","lon"]).reset_index(drop=True)
    if df.empty:
        raise ValueError("没有可用的坐标点（lat/lon 为空或无法解析）")

    return df

#创建地图
def build_map(df: pd.DataFrame, zoom_start: int=12) -> folium.Map:
    m=folium.Map(location=[df.loc[0,"lat"], df.loc[0,"lon"]], zoom_start=zoom_start)
    for row in df.itertuples(index=False):
        folium.Marker(location=[row.lat, row.lon], popup=str(row.name)).add_to(m)
    return m

#导出矢量数据
def export_vectors(
    df: pd.DataFrame,
    geojson_path: str,
    shp_path: str,
    export_geojson: bool,
    export_shp: bool,
) -> bool:
    if not (export_geojson or export_shp):
        return False

    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ModuleNotFoundError:
        return False

    gdf=gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["lon"], df["lat"])],
        crs="EPSG:4326",
    )
    if export_geojson:
        gdf.to_file(geojson_path, driver="GeoJSON")
    if export_shp:
        gdf.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")
    return True

#主函数
def main() -> None:
    args=parse_args()
    base_dir=os.path.dirname(__file__)
    data_path=args.xlsx or os.path.join(base_dir, "data", "data.xlsx")
    output_dir=args.outdir or os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    df=load_points(data_path)
    if not args.no_html:
        html_path=resolve_output_path(output_dir, args.html_path, "map.html")
        os.makedirs(os.path.dirname(html_path) or ".", exist_ok=True)
        build_map(df, zoom_start=args.zoom).save(html_path)
    if args.geojson or args.shp:
        geojson_path=resolve_output_path(output_dir, args.geojson_path, "points.geojson")
        shp_path=resolve_output_path(output_dir, args.shp_path, "points.shp")
        os.makedirs(os.path.dirname(geojson_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(shp_path) or ".", exist_ok=True)
        export_vectors(
            df,
            geojson_path,
            shp_path,
            args.geojson,
            args.shp,
        )


if __name__=="__main__":
    main()
