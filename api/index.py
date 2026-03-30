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
try:
    with open("prompt_templates.json", "r", encoding="utf-8") as f:
        prompt_config = json.load(f)
    templates = prompt_config.get("templates", {})
except:
    templates = {}

# ====================== 必须改这2处 ======================
API_KEY = "992f03a7-b58f-4850-8c86-c485b04e3ccd"  # 改1：替换为自己的Key
MODEL_ID = "ep-20260323110516-75srd"  # 改2：替换为方案1/2/3的模型ID
# =========================================================
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

class Item(BaseModel):
    type: str
    style: str
    len: str
    content: str

@app.post("/api/generate")
async def generate(item: Item):
    # 1. 校验API Key
    if not API_KEY or API_KEY == "你的真实豆包API密钥":
        return {"result": "❌ 错误：未配置有效API Key"}
    
    # 2. 校验文书类型
    if item.type not in templates:
        return {"result": f"❌ 错误：不支持「{item.type}」类型"}
    
    # 3. 生成Prompt
    try:
        template = templates[item.type]["prompt"]
        style = "正式" if item.type == "述职报告" else item.style
        prompt = template.format(style=style, wordCount=item.len, content=item.content)
    except Exception as e:
        return {"result": f"❌ 模板错误：{str(e)}"}

    # 4. 调用API（最终适配版）
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_ID,  # 使用自定义模型ID
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        result_data = resp.json()

        # 解析结果
        if resp.status_code == 200 and "choices" in result_data and result_data["choices"]:
            text = result_data["choices"][0]["message"]["content"].strip()
            return {"result": text}
        elif "error" in result_data:
            return {"result": f"❌ API错误：{result_data['error']['message']}（请换方案2的模型ID）"}
        else:
            return {"result": "❌ 生成失败：无有效返回"}
            
    except requests.exceptions.ConnectionError:
        return {"result": "❌ 网络错误：无法连接服务器"}
    except Exception as e:
        return {"result": f"❌ 系统异常：{str(e)}"}

@app.get("/api/examples/{doc_type}")
async def get_example(doc_type: str):
    example = templates.get(doc_type, {}).get("example", "")
    return {"example": example}

@app.get("/")
async def root():
    return FileResponse("index.html")
