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

# 加载 Prompt 模板（容错处理）
try:
    with open("prompt_templates.json", "r", encoding="utf-8") as f:
        prompt_config = json.load(f)
    templates = prompt_config.get("templates", {})
except Exception as e:
    templates = {}
    print(f"模板加载失败：{str(e)}")

# ====================== 替换为你的真实豆包 API Key ======================
API_KEY = "992f03a7-b58f-4850-8c86-c485b04e3ccd"  # 必须改！改成自己的API Key
# =======================================================================
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

class Item(BaseModel):
    type: str
    style: str
    len: str
    content: str

# 生成文书核心接口
@app.post("/api/generate")
async def generate(item: Item):
    # 1. 校验API Key
    if not API_KEY or API_KEY == "你的豆包API密钥":
        return {"result": "❌ 错误：未配置有效豆包API Key，请在代码中替换API_KEY字段"}
    
    # 2. 校验文书类型
    if item.type not in templates:
        return {"result": f"❌ 错误：暂不支持「{item.type}」类型的文书生成"}
    
    # 3. 生成Prompt（适配固定风格场景）
    try:
        template = templates[item.type]["prompt"]
        # 述职报告强制正式风格，其他场景用用户选择的风格
        style = "正式" if item.type == "述职报告" else item.style
        prompt = template.format(
            style=style,
            wordCount=item.len,
            content=item.content
        )
    except Exception as e:
        return {"result": f"❌ 模板解析错误：{str(e)}"}

    # 4. 调用豆包API（核心修复：模型改为doubao-1.5-chat）
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "doubao-1.5-chat",  # ✅ 已修复：使用通用可访问模型
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000  # 适配长文本生成
        }

        # 发送请求（超时30秒）
        resp = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        result_data = resp.json()

        # 5. 解析返回结果（完整容错）
        if resp.status_code == 200 and "choices" in result_data and result_data["choices"]:
            text = result_data["choices"][0]["message"]["content"].strip()
            return {"result": text}
        elif "error" in result_data:
            error_msg = result_data["error"]["message"]
            return {"result": f"❌ 豆包API错误：{error_msg}"}
        else:
            return {"result": "❌ 生成失败：AI未返回有效内容，请检查背景信息或重试"}
            
    except requests.exceptions.ConnectionError:
        return {"result": "❌ 网络错误：无法连接到豆包服务器，请稍后重试"}
    except requests.exceptions.Timeout:
        return {"result": "❌ 超时错误：请求豆包API超时（30秒），请重试"}
    except Exception as e:
        return {"result": f"❌ 系统异常：{str(e)}"}

# 获取场景参考样例
@app.get("/api/examples/{doc_type}")
async def get_example(doc_type: str):
    example = templates.get(doc_type, {}).get("example", "")
    return {"example": example}

# 首页返回前端页面
@app.get("/")
async def root():
    return FileResponse("index.html")
