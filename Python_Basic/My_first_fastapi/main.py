from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
HOME_HTML_PATH = BASE_DIR / "home.html"
UI_HTML_PATH = BASE_DIR / "ui.html"

COOKIE_NAME = "demo_user"
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "123456"

ITEMS_DB = {
    1: {"name": "苹果", "price": 3.5},
    2: {"name": "香蕉", "price": 2.8},
    3: {"name": "橙子", "price": 4.2},
}

@app.get("/", response_class=HTMLResponse)
def home():
    if not HOME_HTML_PATH.exists():
        raise HTTPException(status_code=500, detail="home.html 不存在")
    return HOME_HTML_PATH.read_text(encoding="utf-8")

@app.get("/about")
def about():
    return {"name": "我的第一个FastAPI项目"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    item = ITEMS_DB.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item 不存在")
    return {"item_id": item_id, "item": item}

@app.get("/add")
def add(a:int,b:int):
    return {"result": a+b}

class AddRequest(BaseModel):
    a: int
    b: int


@app.post("/add")
def add_post(payload: AddRequest):
    return {"result": payload.a + payload.b}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(payload: LoginRequest, response: Response):
    if payload.username != DEMO_USERNAME or payload.password != DEMO_PASSWORD:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    response.set_cookie(COOKIE_NAME, payload.username, httponly=True, samesite="lax")
    return {"ok": True, "username": payload.username}


@app.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@app.get("/me")
def me(request: Request):
    username = request.cookies.get(COOKIE_NAME)
    if not username:
        return {"logged_in": False}
    return {"logged_in": True, "username": username}


@app.get("/ui", response_class=HTMLResponse)
def ui():
    if not UI_HTML_PATH.exists():
        raise HTTPException(status_code=500, detail="ui.html 不存在")
    return UI_HTML_PATH.read_text(encoding="utf-8")
