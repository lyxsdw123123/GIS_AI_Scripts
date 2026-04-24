from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "首页成功"}

@app.get("/about")
def about():
    return {"name": "我的第一个FastAPI项目"}

@app.get("/add")
def add(a:int,b:int):
    return {"result": a+b}