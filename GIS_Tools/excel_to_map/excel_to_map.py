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
    return parser.parse_args()

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
        build_map(df, zoom_start=args.zoom).save(os.path.join(output_dir, "map.html"))
    if args.geojson or args.shp:
        export_vectors(
            df,
            os.path.join(output_dir, "points.geojson"),
            os.path.join(output_dir, "points.shp"),
            args.geojson,
            args.shp,
        )


if __name__=="__main__":
    main()
