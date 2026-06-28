# 🧳 小旅 — 旅行智能体

> 移动端优先的 AI 旅行规划助手。用户通过情绪化 UI 输入状态，结构化传给后端，Agent 自动搜索高德 POI 并生成个性化推荐，地图与对话双向联动。

---

## 一、用例图

```mermaid
graph TB
    USER["👤 旅行者"]

    subgraph 核心用例
        U1["📍 设置位置与状态<br/>(Emoji/滑块/Chip)"]
        U2["✨ 一键生成旅行计划"]
        U3["🗺️ 地图浏览推荐 POI"]
        U4["💬 多轮对话调整计划"]
        U5["🔍 点击 POI 查看详情"]
    end

    subgraph 系统自动
        S0["结构化状态注入<br/>UserState → System Prompt"]
        S1["搜索高德 POI"]
        S2["查询天气"]
        S3["综合用户状态排序"]
        S4["坐标标注地图"]
    end

    USER --> U1
    USER --> U2
    USER --> U3
    USER --> U4
    USER --> U5

    U1 --> S0
    U2 --> S0
    S0 --> S1
    S0 --> S2
    U2 --> S1
    U2 --> S2
    S1 --> S3
    S2 --> S3
    S3 --> U3
    S3 --> U4
    U4 --> S1
    U3 --> U5
    U5 --> U4

    S1 --> S4
    U4 --> S4
```

---

## 二、数据流图

```mermaid
sequenceDiagram
    actor User as 👤 旅行者
    participant UI as 🌐 前端 SPA
    participant API as ⚡ FastAPI
    participant LLM as 🧠 DeepSeek
    participant Amap as 🗺️ 高德 API

    Note over User,Amap: === 首次规划：状态采集 + 搜索 + 推荐 ===

    User->>UI: 点击 Emoji / 滑块 / Chip
    UI->>UI: 更新 state = {location, mood, fatigue, ...}
    User->>UI: 点击「✨ 开始规划」

    UI->>API: POST /api/chat<br/>{message, history, <b>state</b>}
    API->>API: UserState(**state) 校验结构化数据
    API->>API: _build_state_context() 拼入 System Prompt

    API->>LLM: System Prompt + 用户画像 + 历史 + 消息
    LLM-->>API: tool_calls: [search_nearby, get_weather]

    par 并行工具执行
        API->>Amap: POI 搜索
        Amap-->>API: POI 列表
    and
        API->>Amap: 天气查询
        Amap-->>API: 天气预报
    end

    API->>API: 提取 POI 坐标缓存
    API->>LLM: 工具结果
    LLM-->>API: 文本回复（综合状态+POI+天气）
    API-->>UI: {reply, pois, city}
    UI->>UI: 渲染 Markdown + 地图标记 + POI 卡片

    Note over User,Amap: === 追问 / 调整 ===

    User->>UI: 输入文字 / 点击卡片
    UI->>API: POST /api/chat<br/>{message, history, state}
    API->>LLM: 带历史的对话（状态复用）
    LLM-->>API: 文本回复（优先用已有数据）
    API-->>UI: {reply, pois, city}

    Note over User,Amap: === 地图联动 ===

    User->>UI: 点击地图上的 POI 标记
    UI->>UI: 弹出详情浮层
    User->>UI: 点击「了解更多」
    UI->>UI: 自动填入追问 → 触发 /api/chat
```

---

## 三、系统架构（含数据流向）

```mermaid
graph LR
    subgraph 前端["前端 (static/)"]
        HTML["index.html<br/>移动端 SPA"]
        CSS["style.css<br/>玻璃质感 + 渐变"]
        JS1["app.js<br/>状态管理 · 聊天 · Markdown"]
        JS2["map.js<br/>高德地图 · 标记联动"]
    end

    subgraph 后端["后端 (Python)"]
        SVR["server.py<br/>FastAPI · 路由 · CORS"]
        MD["models/user_state.py<br/>UserState 模型"]
        PLN["planner.py<br/>Agent 编排 · Tool Calling"]
        PR["prompts/system.py<br/>System Prompt"]
        DS["deepseek.py<br/>DeepSeek 调用"]
        AM["amap.py<br/>高德 API · 内存缓存"]
    end

    subgraph 外部["外部服务"]
        DSA["DeepSeek API"]
        AMA["高德 Web API + JS API"]
    end

    HTML --> CSS
    HTML --> JS1
    HTML --> JS2

    JS1 -->|"POST /api/chat<br/>{message, history, state}"| SVR
    JS2 -->|"JS SDK 加载"| AMA

    SVR -->|"UserState(**state)"| MD
    SVR --> PLN
    PLN --> PR
    PLN --> DS
    PLN --> AM
    DS --> DSA
    AM --> AMA
```

---

## 四、UserState 结构化状态流

```mermaid
flowchart LR
    subgraph 前端 UI
        EMOJI["😊 Emoji 选择器 → mood"]
        SLIDER["⚡ 滑块 → fatigue"]
        SLIDER2["🔍 滑块 → curiosity"]
        INPUT["📍 输入框 → location"]
        CHIPS["💡 Chip 标签 → companion, budget, preferences"]
    end

    subgraph JS["app.js"]
        STATE["state = {<br/>  location, mood, fatigue,<br/>  curiosity, budget,<br/>  companion, preferences<br/>}"]
        BUILD["buildStateMessage()<br/>→ 自然语言消息"]
        SEND["sendMessage()<br/>POST /api/chat"]
    end

    subgraph Python["server.py → planner.py"]
        VALIDATE["UserState(**state)<br/>Pydantic 校验"]
        CONTEXT["_build_state_context()<br/>→ Markdown 列表"]
        INJECT["注入 System Prompt 末尾"]
    end

    subgraph LLM["DeepSeek"]
        READ["直接读取用户画像<br/>不重复追问"]
    end

    EMOJI --> STATE
    SLIDER --> STATE
    SLIDER2 --> STATE
    INPUT --> STATE
    CHIPS --> STATE
    STATE --> BUILD
    STATE --> SEND
    SEND --> VALIDATE
    VALIDATE --> CONTEXT
    CONTEXT --> INJECT
    INJECT --> READ
```

System Prompt 末尾注入示例：

```markdown
## 当前用户画像（来自UI输入，直接使用不要追问）
- 📍 位置：杭州西湖区
- 😊 心情：7/10
- ⚡ 疲惫度：3/10
- 🔍 好奇心：8/10
- 👥 同行者：独自
- 💡 偏好：自然风光、安静文艺、避开人多
- 💰 预算：100-300
```

---

## 五、Agent 决策循环

```mermaid
flowchart TD
    A["👤 用户消息 + 📋 结构化状态"] --> B["构建 System Prompt<br/>+ 用户画像注入<br/>+ 历史消息"]
    B --> C["DeepSeek API<br/>带 4 个 tool 定义"]
    C --> D{"有 tool_calls?"}

    D -->|否| E{"已搜过 POI?"}
    E -->|否| F["🛑 拦截！注入指令：<br/>必须调用搜索工具<br/>→ 回到 C"]
    E -->|是| G["✅ 返回最终回复 + POI 坐标"]

    D -->|是| H["⚡ asyncio.gather<br/>并行执行所有工具<br/>(每个 ≤15s)"]
    H --> I["提取 POI 坐标<br/>缓存城市名"]
    I --> J["追加 tool 结果到 messages"]
    J --> K{"达到 3 轮?"}
    K -->|否| C
    K -->|是| L["强制结束<br/>不带 tools 调 LLM"]
    L --> G

    style F fill:#fef3c7,stroke:#f59e0b
    style G fill:#f0fdf4,stroke:#16a34a
    style H fill:#eef2ff,stroke:#6366f1
```

关键设计：
| 机制 | 说明 |
|------|------|
| 并行工具执行 | `asyncio.gather` 同时跑 POI搜索 + 天气查询 |
| 强制搜索拦截 | 第一轮 LLM 若凭知识直答，系统注入指令强制调工具 |
| 3 轮上限 | 防止无限循环，第 3 轮后不带 tools 强制输出 |
| 坐标捕获 | 工具执行时同步提取经纬度，前端地图直接使用 |
| 15s 工具超时 | 单工具超时自动跳过，不阻塞整体 |
| 状态注入 | UserState 结构化嵌入 System Prompt，LLM 不重复追问 |

---

## 六、项目结构

```
travel_agent/
│
├── server.py                  ← FastAPI 入口（路由 + 静态文件）
├── config.py                  ← 从 ../../.env 加载 API Key
├── requirements.txt           ← Python 依赖
├── README.md                  ← 本文档
│
├── models/
│   └── user_state.py          ← UserState 模型（Pydantic，1-10 量表）
│
├── services/                   ← 核心业务层
│   ├── planner.py             ← Agent 编排引擎（Tool Calling · 并行 · 拦截）
│   ├── deepseek.py            ← DeepSeek API 封装（OpenAI 兼容，30s 超时）
│   └── amap.py                ← 高德 API 封装（POI/天气/地理编码 + 5min 缓存）
│
├── prompts/
│   └── system.py              ← System Prompt（角色 · 三步法 · 输出格式）
│
└── static/                     ← 前端（移动端优先 SPA）
    ├── index.html              ← 单页应用入口
    ├── css/style.css           ← 渐变氛围 + 玻璃质感 + Markdown 样式
    ├── js/app.js               ← 主逻辑（状态管理 · 聊天 · Markdown 渲染）
    └── js/map.js               ← 高德地图模块（标记 · 联动 · 详情浮层）
```

| 文件 | 职责 | 关键函数 |
|------|------|----------|
| `server.py` | HTTP 入口，CORS，接收 state，转换 UserState | `POST /api/chat`, `GET /api/config` |
| `planner.py` | Agent 循环，并行工具执行，强制搜索拦截 | `run_agent()`, `execute_tool()`, `_build_state_context()` |
| `deepseek.py` | 调用 DeepSeek，支持 Function Calling | `chat(messages, tools)` |
| `amap.py` | 高德 API + 5 分钟内存缓存 | `search_pois()`, `text_search()`, `get_weather()` |
| `system.py` | Agent 角色定义、三步法、输出格式规范 | `SYSTEM_PROMPT` |
| `user_state.py` | 用户画像 Pydantic 模型，7 个维度 | `UserState.is_ready()`, `UserState.summary()` |
| `app.js` | 状态管理、Emoji/滑块/Chip 交互、结构化发送 | `sendMessage()`, `renderMarkdown()`, `buildStateMessage()` |
| `map.js` | 动态加载 JS SDK、标记管理、地图-对话联动 | `init()`, `setPOIMarkers()`, `flyTo()`, `geocode()` |

---

## 七、工具清单

Agent 可调用的 4 个高德工具：

| 工具 | 功能 | 参数 |
|------|------|------|
| `search_nearby` | 周边 POI 搜索 | keywords, city, location, radius |
| `search_citywide` | 全市 POI 搜索 | keywords, city |
| `get_weather` | 4 天天气预报 | city |
| `geocode` | 地址 → 经纬度 | address, city |

---

## 八、配置

在项目根目录 `d:\GIS_AI_Scripts\.env`：

```env
AMAP_KEY=你的高德Web服务Key
DEEPSEEK_API_KEY=你的DeepSeek Key
```

高德 Key 需开通：
- **Web服务 API** — 后端 POI 搜索、天气、地理编码
- **Web端 JS API** — 前端地图显示

---

## 九、启动

```bash
cd d:\GIS_AI_Scripts
.venv/Scripts/python -m uvicorn travel_agent.server:app --host 0.0.0.0 --port 7878
```

浏览器打开 `http://localhost:7878`
