"""旅行智能体 — FastAPI 服务端"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from travel_agent.services.planner import run_agent, AgentResult
from travel_agent.models.user_state import UserState
import traceback
from travel_agent.config import AMAP_KEY, AMAP_JS_KEY

app = FastAPI(title="小旅 - 旅行智能体")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC = Path(__file__).parent / "static"


# ── API 模型 ──

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    state: dict | None = None  # {location, mood, fatigue, curiosity, budget, companion, preferences}


class ChatResponse(BaseModel):
    reply: str
    pois: list[dict] = []   # [{name, lng, lat, address, rating}]
    city: str = ""


# ── API 路由 ──

@app.get("/api/config")
async def get_config():
    """前端获取配置（Amap JS Key 等）"""
    return {
        "amap_js_key": AMAP_JS_KEY,    # 前端地图 JS API 用
        "amap_ws_key": AMAP_KEY,        # 前端地理编码 REST API 用
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "消息不能为空")

    try:
        # 结构化用户状态
        user_state = UserState(**(req.state or {}))
        result: AgentResult = await run_agent(req.message, req.history, user_state)
        return ChatResponse(
            reply=result.reply,
            pois=result.pois,
            city=result.city,
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"{type(e).__name__}: {e}")


# ── 静态文件 ──

@app.get("/")
async def root():
    return FileResponse(STATIC / "index.html")


# 挂载静态资源（CSS/JS/图片）
app.mount("/static", StaticFiles(directory=STATIC), name="static")
