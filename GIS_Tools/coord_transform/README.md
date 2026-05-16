# 坐标转换工具

WGS84 / GCJ02（火星坐标）/ BD09（百度坐标） 三种坐标系互转。

## 外部库

| 库 | 用途 | 必须？ |
|---|---|---|
| openpyxl | Excel 文件（.xlsx）读写 | 否，仅处理 Excel 时需要 |
| math, csv, sys, argparse, pathlib, typing | 核心数学、CSV、命令行等 | 全部为标准库，无需安装 |

如果只使用 CSV 格式或单点模式，不需要安装任何第三方库。

```bash
# 全部安装
pip install -r requirements.txt

# 只装 openpyxl
pip install openpyxl
```

## 文件结构

```
coord_transform/
├── __init__.py       # 包入口，对外暴露 6 个转换函数
├── transform.py      # 核心转换算法
├── cli.py            # 命令行入口
├── data/             # 模拟数据
├── requirements.txt
└── README.md
```

## 作为代码库使用

```python
from GIS_Tools.coord_transform import wgs84_to_gcj02, bd09_to_wgs84

new_lng, new_lat = wgs84_to_gcj02(116.397428, 39.908722)

# 批量
for record in data:
    record["lng"], record["lat"] = bd09_to_wgs84(record["lng"], record["lat"])
```

## 命令行使用

```bash
# 单点转换
python -m GIS_Tools.coord_transform.cli --from wgs84 --to gcj02 --lng 116.397 --lat 39.908

# CSV 批量转换
python -m GIS_Tools.coord_transform.cli --from wgs84 --to gcj02 -i in.csv -o out.csv --lng-col lng --lat-col lat

# Excel 批量转换
python -m GIS_Tools.coord_transform.cli --from gcj02 --to wgs84 -i in.xlsx -o out.xlsx --lng-col 经度 --lat-col 纬度
```

## 技术说明

- GCJ02 ↔ WGS84：利用加密函数的空间缓变性做近似推算，误差 < 1.5m
- BD09 ↔ GCJ02：极坐标变换，精确数学逆运算，误差为 0
