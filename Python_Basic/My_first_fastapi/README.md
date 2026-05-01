## My_first_fastapi

一个用于学习 FastAPI 的最小示例项目，包含：
- 首页前端页面（含登录演示、加法 POST、items 路径参数查询、文件上传）
- 后端接口（GET/POST、Path 参数、Cookie 登录态、文件上传）
- 自动接口文档（Swagger）

## 安装依赖

在虚拟环境中安装：

```bash
pip install -r Python_Basic/My_first_fastapi/requirements.txt
```

## 依赖库说明

- `fastapi`：Web 框架，用来定义路由（GET/POST）、参数校验、返回 JSON/HTML，并自动生成 OpenAPI 文档。
- `uvicorn`：ASGI 服务器，用来启动并运行 FastAPI 应用（`uvicorn main:app --reload`）。
- `python-multipart`：解析 `multipart/form-data` 的依赖，文件上传（`UploadFile`/`File(...)`）必须安装它。

## 启动服务

方式 A：在 `D:\GIS_AI_Scripts` 目录运行（与你现在的 notebook.txt 一致）

```bash
uvicorn Python_Basic.My_first_fastapi.main:app --reload
```

方式 B：进入项目目录运行

```bash
cd Python_Basic/My_first_fastapi
uvicorn main:app --reload
```

启动后访问：
- 首页：http://127.0.0.1:8000/
- Swagger：http://127.0.0.1:8000/docs

## 功能与接口

### 1. 首页与 UI
- `GET /`：首页（读取 `home.html`）
- `GET /ui`：加法演示页（读取 `ui.html`）

### 2. 加法接口
- `GET /add?a=1&b=2`
- `POST /add`（JSON）

请求体示例：

```json
{ "a": 1, "b": 2 }
```

### 3. items（路径参数示例）
- `GET /items/{item_id}`

示例：
- http://127.0.0.1:8000/items/1

当前数据源是 `main.py` 里的字典 `ITEMS_DB`（仅演示，不持久化）。

### 4. 登录演示（Cookie）
这是最简“流程演示”，账号写死在后端：
- 用户名：admin
- 密码：123456

接口：
- `POST /login`（JSON：username/password）成功后设置 Cookie
- `POST /logout` 删除 Cookie
- `GET /me` 查询当前登录态

### 5. 文件上传
- `POST /upload`（multipart/form-data，字段名：`file`）

上传后的文件会保存到：
- `Python_Basic/My_first_fastapi/uploads/`

可以在 `/docs` 里直接选择文件测试上传。
