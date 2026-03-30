from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests

# 必须暴露 app 变量，Vercel 才能识别！
app = FastAPI()

# 填入你自己的豆包 API Key
DOUBAO_API_KEY = "你的豆包API_KEY"
DOUBAO_API_URL = "992f03a7-b58f-4850-8c86-c485b04e3ccd"

class Item(BaseModel):
    type: str
    style: str
    len: str
    content: str

@app.post("/api/generate")
async def generate(item: Item):
    prompt = f"""
你是专业职场文书助手，只输出正文，不解释、不寒暄、不加多余内容。
请生成一篇【{item.type}】，风格{item.style}，字数{item.len}字。
背景信息：{item.content}
    """.strip()

    headers = {
        "Authorization": f"Bearer {DOUBAO_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "doubao-1.5-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        resp = requests.post(DOUBAO_API_URL, json=payload, timeout=50)
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return {"result": text}
    except Exception as e:
        return {"result": f"错误：{str(e)}"}
