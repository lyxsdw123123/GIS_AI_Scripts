from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
UI_HTML_PATH = BASE_DIR / "ui.html"

@app.get("/")
def home():
    return {"message": "首页成功"}

@app.get("/about")
def about():
    return {"name": "我的第一个FastAPI项目"}

@app.get("/add")
def add(a:int,b:int):
    return {"result": a+b}


@app.get("/ui", response_class=HTMLResponse)
def ui():
    if not UI_HTML_PATH.exists():
        raise HTTPException(status_code=500, detail="ui.html 不存在")
    return UI_HTML_PATH.read_text(encoding="utf-8")
