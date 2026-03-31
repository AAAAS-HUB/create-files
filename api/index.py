from fastapi import FastAPI, Response
from pydantic import BaseModel
import requests
import json
import uuid
import io
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from docx import Document

app = FastAPI()

# 解决跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 临时存储生成的内容
generated_content = {}

# 加载 Prompt 模板
try:
    with open("prompt_templates.json", "r", encoding="utf-8") as f:
        prompt_config = json.load(f)
    templates = prompt_config.get("templates", {})
except Exception as e:
    templates = {}
    print(f"模板加载失败：{str(e)}")

# ====================== 替换为你的信息 ======================
API_KEY = DOUBAO_API_KEY
MODEL_ID = "ep-20260323110516-75srd"  # 替换为你的模型ID
# =========================================================
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

class Item(BaseModel):
    type: str
    style: str
    len: str
    content: str

# 生成文案核心接口
@app.post("/api/generate")
async def generate(item: Item):
    # 1. 校验API Key
    if not API_KEY or API_KEY == DOUBAO_API_KEY:
        return {"result": "❌ 错误：未配置有效豆包API Key", "doc_id": ""}
    
    # 2. 校验文案类型
    if item.type not in templates:
        return {"result": f"❌ 错误：暂不支持「{item.type}」类型", "doc_id": ""}
    
    # 3. 生成Prompt（仅述职报告强制正式风格）
    try:
        template = templates[item.type]["prompt"]
        style = "正式" if item.type == "述职报告" else item.style
        prompt = template.format(
            style=style,
            wordCount=item.len,
            content=item.content
        )
    except Exception as e:
        return {"result": f"❌ 模板解析错误：{str(e)}", "doc_id": ""}

    # 4. 调用豆包API（超时优化+重试）
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL_ID,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,  # 社交媒体文案适当提高随机性，更有网感
            "max_tokens": 2000,
            "stream": False,
            "top_p": 0.9
        }

        # 自动重试机制
        retry_count = 0
        max_retry = 2
        resp = None
        while retry_count <= max_retry:
            try:
                resp = requests.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=15,
                    verify=False
                )
                break
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count > max_retry:
                    raise requests.exceptions.Timeout("多次请求超时")

        result_data = resp.json()

        # 5. 解析结果并存储
        if resp.status_code == 200 and "choices" in result_data and result_data["choices"]:
            text = result_data["choices"][0]["message"]["content"].strip()
            doc_id = str(uuid.uuid4())
            generated_content[doc_id] = {
                "title": item.type,
                "content": text
            }
            return {"result": text, "doc_id": doc_id}
        elif "error" in result_data:
            error_msg = result_data["error"]["message"]
            return {"result": f"❌ 豆包API错误：{error_msg}", "doc_id": ""}
        else:
            return {"result": "❌ 生成失败：无有效返回", "doc_id": ""}
            
    except requests.exceptions.ConnectionError:
        return {"result": "❌ 网络错误：无法连接服务器", "doc_id": ""}
    except requests.exceptions.Timeout:
        return {"result": "❌ 超时错误：请求超时，请重试", "doc_id": ""}
    except Exception as e:
        return {"result": f"❌ 系统异常：{str(e)}", "doc_id": ""}

# 下载文档接口（极简稳定版）
@app.get("/api/download/{doc_id}")
async def download_doc(doc_id: str):
    if doc_id not in generated_content:
        return Response(content="文档不存在或已过期", status_code=404)
    
    doc_data = generated_content[doc_id]
    title = doc_data["title"]
    content = doc_data["content"]

    try:
        # 创建Word文档
        doc = Document()
        doc.add_heading(title, level=1)
        doc.add_paragraph(content)

        # 保存到内存流
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        doc_stream.seek(0)

        # 返回下载响应（处理中文文件名）
        return StreamingResponse(
            doc_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={title}.docx".encode("utf-8").decode("latin-1")
            }
        )
    except Exception as e:
        return Response(content=f"文档生成失败：{str(e)}", status_code=500)

# 获取参考样例
@app.get("/api/examples/{doc_type}")
async def get_example(doc_type: str):
    example = templates.get(doc_type, {}).get("example", "")
    return {"example": example}

# 首页
@app.get("/")
async def root():
    return FileResponse("index.html")