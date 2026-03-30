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

# ====================== 必须替换成你的豆包 API Key ======================
API_KEY = "992f03a7-b58f-4850-8c86-c485b04e3ccd"  # <--- 这里一定要填你自己的！
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
    # 1. 基础校验
    if not API_KEY or API_KEY == "你的真实豆包API密钥":
        return {"result": "❌ 错误：未配置 API Key，请在后台代码中填入你的豆包 API 密钥"}
    
    # 2. 模板校验
    if item.type not in templates:
        return {"result": f"❌ 错误：不支持 '{item.type}' 类型"}
    
    # 3. 生成 Prompt
    try:
        template = templates[item.type]["prompt"]
        # 述职报告强制正式风格
        style = "正式" if item.type == "述职报告" else item.style
        prompt = template.format(style=style, wordCount=item.len, content=item.content)
    except Exception as e:
        return {"result": f"❌ 模板错误：{str(e)}"}

    # 4. 调用豆包 API（重点：增加了完整的容错和日志）
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "doubao-1.5-pro",  # 使用更强力的模型版本
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        # 发送请求
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        result_data = resp.json()

        # 5. 核心修复：处理 'choices' 报错 + 兼容新旧格式
        if "choices" in result_data and result_data["choices"]:
            text = result_data["choices"][0]["message"]["content"].strip()
            return {"result": text}
        elif "error" in result_data:
            return {"result": f"❌ API 错误：{result_data['error']['message']}"}
        else:
            return {"result": "❌ 服务错误：AI 未返回有效内容，请重试"}
            
    except requests.exceptions.ConnectionError:
        return {"result": "❌ 网络错误：无法连接到豆包服务器"}
    except Exception as e:
        return {"result": f"❌ 异常错误：{str(e)}"}

# 获取参考样例
@app.get("/api/examples/{doc_type}")
async def get_example(doc_type: str):
    example = templates.get(doc_type, {}).get("example", "")
    return {"example": example}

# 首页
@app.get("/")
async def root():
    return FileResponse("index.html")
