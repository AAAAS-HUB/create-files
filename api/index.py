from fastapi import FastAPI
from pydantic import BaseModel
import requests
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 解决跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== 必须替换成你的豆包 API Key ======================
API_KEY = "992f03a7-b58f-4850-8c86-c485b04e3ccd"  # 重点：改这里！
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
# =======================================================================

class Item(BaseModel):
    type: str
    style: str
    len: str
    content: str

# 生成文书接口
@app.post("/api/generate")
async def generate(item: Item):
    prompt = f"""
你是专业职场文书助手，只输出正文，不解释、不寒暄、不加多余内容。
请生成一篇【{item.type}】，风格{item.style}，字数{item.len}字。
背景信息：{item.content}
    """.strip()

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "doubao-1.5-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=50)
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return {"result": text}
    except Exception as e:
        return {"result": f"服务错误：{str(e)}"}

# 首页 → 直接返回网页（修正路径！）
@app.get("/")
async def root():
    return FileResponse("index.html")  # 关键：去掉 ../
