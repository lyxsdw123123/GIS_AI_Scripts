# natural_language_to_map（AI + 地图检索/可视化学习脚本）

这是一个面向初学者的 Python 小项目：把自然语言需求（例如“长沙高校分布”“雨花区医院分布”）解析为检索参数，调用高德地图 Web 服务获取 POI，并生成可交互的 HTML 地图（点位 + 热力图 + 行政区边界 + POI 数量角标）。

## 基本功能

- 自然语言解析：使用通义千问（DashScope）把用户输入解析为 `city` 与 `keyword`
- POI 检索：调用高德 POI 文本搜索接口获取结果，并支持分页抓取（限制总页数/总条数，避免过慢）
- 地图可视化（Folium/Leaflet）：
  - POI 点位标注（Marker）
  - POI 热力图（HeatMap）
  - 行政区边界叠加（高德行政区查询接口返回的边界 polyline）
  - 左上角显示本次获取的 POI 总数量
- 输出：生成 HTML 文件到 `output/` 目录

## 目录结构

- `natural_language_to_map.py`：主程序（POI 抓取、边界获取、地图生成、输出）
- `llm_backend.py`：通义千问调用与 JSON 解析（把自然语言转为结构化参数）

## 依赖库介绍（你会学到什么）

- `requests`
  - 用途：发起 HTTP 请求，访问高德地图 Web API 与 DashScope API
  - 学习点：参数拼装、超时控制、JSON 响应解析
- `python-dotenv`
  - 用途：从项目根目录的 `.env` 文件读取密钥（`AMAP_KEY`、`DASHSCOPE_API_KEY` 等）
  - 学习点：安全管理 API Key（避免写死在代码里）
- `folium`
  - 用途：用 Python 生成 Leaflet 地图的 HTML
  - 学习点：图层（Layer）、标注（Marker）、多边形（Polygon）、图层控制器（LayerControl）
- `folium.plugins.HeatMap`
  - 用途：把点数据渲染为热力图，直观呈现空间密度
  - 学习点：`radius/blur/min_opacity` 等可视化参数如何影响“密度表达”
- `branca.element.MacroElement` / `branca.element.Template`
  - 用途：向 Folium 生成的 HTML 注入自定义固定定位元素（例如左上角 POI 数量角标）
  - 学习点：把“自定义 HTML UI”叠加到地图页面中
- `pathlib.Path`
  - 用途：更可靠的跨平台路径处理（输出目录、根目录定位）

## 准备工作

### 1) 安装依赖

建议在虚拟环境中安装：

```bash
pip install -r requirements.txt
```

### 2) 配置环境变量（在项目根目录 `d:\GIS_AI_Scripts` 下）

在 `d:\GIS_AI_Scripts\.env` 中写入：

```ini
AMAP_KEY=你的高德Web服务Key
DASHSCOPE_API_KEY=你的DashScope Key
QWEN_MODEL=qwen-turbo
```

说明：

- `AMAP_KEY` 必填：用于高德 POI/行政区接口
- `DASHSCOPE_API_KEY` 建议填写：用于 LLM 解析自然语言；若为空，解析会失败
- `QWEN_MODEL` 可选：默认 `qwen-turbo`

## 运行方式

在本目录运行：

```bash
python natural_language_to_map.py
```

输入示例：

- `长沙高校分布`
- `雨花区医院分布`

输出：

- 在 `output/` 下生成 `城市_关键词_分布地图.html`

## 常见问题

- 看不到更新效果
  - 重新运行脚本会生成/覆盖 HTML；请确认打开的是最新生成的文件
  - 浏览器可能缓存本地文件，建议关闭标签页后重新打开或强制刷新
- POI 数量偏少
  - 脚本做了分页抓取上限（页数/总条数），避免请求过多过慢
  - 可在 `natural_language_to_map.py` 的 `get_poi()` 调整 `per_page/max_pages/max_items`

