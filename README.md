# AI Enterprise RAG Knowledge Base

一个最小可运行的企业知识库 RAG Demo。项目基于 `company.txt` 中的企业流程资料，完成文本切分、Embedding、向量入库、语义检索，并使用 GPT 生成基于知识库内容的回答。

## 技术栈

- Python
- FastAPI
- OpenAI Embeddings
- OpenAI Chat Completions
- ChromaDB
- Uvicorn

## 核心功能

- 读取本地企业知识文件 `data/company.txt`
- 将企业知识文本切分为 Chunk
- 使用 OpenAI Embedding 模型生成向量
- 将向量和原文存入 ChromaDB
- 根据用户问题做语义检索
- 将检索到的上下文交给 GPT 生成回答
- 提供 FastAPI 接口和 Swagger 文档

## RAG 流程

```text
company.txt
  -> 文本切分 Chunk
  -> OpenAI Embedding
  -> ChromaDB 向量库
  -> 用户提问
  -> 问题向量化
  -> 相似 Chunk 检索
  -> GPT 基于上下文回答
```

## 项目结构

```text
ai-rag-knowledge-base/
├─ app.py
├─ requirements.txt
├─ README.md
└─ data/
   └─ company.txt
```

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

设置 OpenAI API Key。

PowerShell：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
```

macOS / Linux：

```bash
export OPENAI_API_KEY="你的 API Key"
```

启动服务：

```bash
uvicorn app:app --reload
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

## 接口说明

### GET `/health`

健康检查接口。

### POST `/ask`

企业知识库问答接口。

请求示例：

```json
{
  "question": "请假流程是什么？"
}
```

响应示例：

```json
{
  "question": "请假流程是什么？",
  "answer": "请假流程是：提前一天申请，领导审批，HR备案。",
  "contexts": [
    "请假流程：\n\n提前一天申请\n领导审批\nHR备案"
  ]
}
```

## 项目亮点

- 使用真实 RAG 链路，而不是简单关键词匹配
- 向量数据库使用 ChromaDB，适合本地 Demo 和快速验证
- API 服务使用 FastAPI，便于展示、测试和后续扩展
- 知识库内容独立放在 `data/company.txt`，结构清晰
- 当知识库没有相关信息时，提示模型不要编造答案

## 后续优化

- 支持多文档上传
- 支持 PDF 解析
- 支持 OCR 图片识别
- 增加前端问答页面
- 增加登录和权限控制
- 支持 Docker 部署
- 增加自动化测试和 CI
