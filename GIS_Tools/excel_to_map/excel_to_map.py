import os

import folium
import pandas as pd

#Excel(name/lat/lon) -> output\map.html；可选导出 output\points.geojson / output\points.shp
REQUIRED_COLS=("name","lat","lon")

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
def export_vectors(df: pd.DataFrame, geojson_path: str, shp_path: str) -> bool:
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
    gdf.to_file(geojson_path, driver="GeoJSON")
    gdf.to_file(shp_path, driver="ESRI Shapefile", encoding="utf-8")
    return True

#主函数
def main() -> None:
    base_dir=os.path.dirname(__file__)
    data_path=os.path.join(base_dir, "data", "data.xlsx")
    output_dir=os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    df=load_points(data_path)
    build_map(df).save(os.path.join(output_dir, "map.html"))
    export_vectors(
        df,
        os.path.join(output_dir, "points.geojson"),
        os.path.join(output_dir, "points.shp"),
    )


if __name__=="__main__":
    main()
