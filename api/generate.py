from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

# 在这里填入你自己的豆包 API Key 和 endpoint
API_KEY = "你的豆包API_KEY"
API_URL = "992f03a7-b58f-4850-8c86-c485b04e3ccd"

class Item(BaseModel):
    type: str
    style: str
    len: str
    content: str

@app.post("/api/generate")
async def gen(item: Item):
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

    resp = requests.post(API_URL, json=payload, timeout=50)
    result = resp.json()
    text = result["choices"][0]["message"]["content"].strip()

    return {"result": text}