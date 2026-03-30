from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
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

# 加载 Prompt 模板
with open("prompt_templates.json", "r", encoding="utf-8") as f:
    prompt_config = json.load(f)
templates = prompt_config["templates"]

# ====================== 替换成你的豆包 API Key ======================
API_KEY = "992f03a7-b58f-4850-8c86-c485b04e3ccd"
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
    # 获取对应场景的模板
    if item.type not in templates:
        return {"result": "暂不支持该文书类型"}
    
    # 替换模板变量（处理述职报告等固定风格的场景）
    template = templates[item.type]["prompt"]
    # 述职报告强制正式风格
    if item.type == "述职报告":
        style = "正式"
    else:
        style = item.style
    
    prompt = template.format(
        style=style,
        wordCount=item.len,
        content=item.content
    )

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

# 新增接口：获取各场景的参考样例（给前端展示）
@app.get("/api/examples/{doc_type}")
async def get_example(doc_type: str):
    if doc_type not in templates:
        return {"example": ""}
    return {"example": templates[doc_type]["example"]}

# 首页 → 返回网页
@app.get("/")
async def root():
    return FileResponse("index.html")