# excel_to_map

将 Excel 点数据（字段：`name` / `lat` / `lon`）转换为：

- HTML 交互式地图（默认输出）
- GeoJSON（可选）
- Shapefile（可选）

## 目录结构

- `data/data.xlsx`：默认输入
- `output/`：默认输出目录

## 依赖

- 必需：`pandas`、`folium`
- 可选（导出 GeoJSON/SHP 才需要）：`geopandas`、`shapely`

安装示例（pip）：

```bash
pip install pandas folium
pip install geopandas shapely
```

## 用法

在项目根目录 `d:\GIS_AI_Scripts` 下执行：

```bash
py .\GIS_Tools\excel_to_map\excel_to_map.py
```

仅导出 GeoJSON（仍会生成 HTML）：

```bash
py .\GIS_Tools\excel_to_map\excel_to_map.py --geojson
```

仅导出 Shapefile（仍会生成 HTML）：

```bash
py .\GIS_Tools\excel_to_map\excel_to_map.py --shp
```

指定输出目录：

```bash
py .\GIS_Tools\excel_to_map\excel_to_map.py --geojson --outdir .\GIS_Tools\excel_to_map\output\output_custom
```

自定义输出文件名/路径：

```bash
py .\GIS_Tools\excel_to_map\excel_to_map.py --geojson --html-path my_map.html --geojson-path my_points.geojson --outdir .\GIS_Tools\excel_to_map\output\output_custom
```

## 参数

- `--xlsx`：输入 Excel 路径；不填默认 `data/data.xlsx`
- `--outdir`：输出目录；不填默认 `output/`
- `--zoom`：HTML 地图初始缩放（默认 12）
- `--no-html`：不生成 HTML
- `--geojson`：导出 GeoJSON（需 geopandas + shapely）
- `--shp`：导出 Shapefile（需 geopandas + shapely）
- `--html-path` / `--geojson-path` / `--shp-path`：输出路径；绝对路径直接使用，相对路径基于 `outdir`
