# buffer_zone

点位缓冲区分析：生成缓冲区、可视化地图、叠加分析、统计输出

## 依赖

```bash
pip install pandas folium geopandas shapely openpyxl
```

## 用法

```bash
# 基础缓冲（500m）
python buffer_zone.py --xlsx data/points.xlsx --radius 500

# 合并所有重叠缓冲区
python buffer_zone.py --xlsx data/points.xlsx --radius 1000 --dissolve

# 多层环形缓冲
python buffer_zone.py --xlsx data/points.xlsx --radius 500,1000,1500

# 叠加 POI 分析
python buffer_zone.py --xlsx data/points.xlsx --radius 500 --pois data/pois.xlsx

# 组合使用
python buffer_zone.py --xlsx data/points.xlsx --radius 1000 --dissolve --pois data/pois.xlsx
```

## 参数

- `--xlsx`：输入 Excel 路径；默认 `data/points.xlsx`
- `--outdir`：输出目录；默认 `output/`
- `--radius`：缓冲半径（米），多个用逗号分隔
- `--dissolve`：合并所有重叠缓冲区
- `--pois`：叠加分析用 POI Excel 路径
- `--zoom`：地图缩放级别（默认 13）
- `--no-html`：不生成 HTML 地图

## 输出

- `output/buffer.html` — 交互式地图
- `output/buffer_{radius}m.geojson` — 缓冲区矢量数据
- `output/covered_pois.xlsx` — 落在缓冲区内的 POI（如果指定了 `--pois`）
