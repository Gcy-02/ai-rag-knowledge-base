# AI 企业知识库 RAG 助手

一个面向企业内部知识问答的 RAG Demo。项目支持读取本地知识文件、上传 PDF 文档、向量化入库、语义检索、基于 GPT 生成回答，并在回答中返回引用来源。

![RAG Web Demo](screenshots/rag-web-demo.png)

## 项目介绍

很多企业内部资料分散在员工手册、流程制度、FAQ 文档中，员工查询成本高，HR 或行政也需要重复回答同类问题。本项目模拟一个企业知识库助手：用户上传文档后，可以直接用自然语言提问，系统会从知识库中检索相关内容，再让大模型基于检索结果生成回答。

## 技术栈

- Python
- FastAPI
- OpenAI Embeddings
- OpenAI Chat Completions
- ChromaDB
- pypdf
- HTML / CSS / JavaScript
- Uvicorn

## 核心功能

- 内置企业资料 `data/company.txt`
- 支持 PDF 上传
- 支持 PDF 文本解析
- 支持文本 Chunk 切分
- 支持 OpenAI Embedding 向量化
- 支持 ChromaDB 向量检索
- 支持 GPT 基于检索上下文回答
- 支持返回引用来源
- 支持最简 Web 问答界面
- 支持 FastAPI Swagger 接口文档

## RAG 流程

```text
company.txt / PDF
  -> 文本解析
  -> Chunk 切分
  -> OpenAI Embedding
  -> ChromaDB 向量库
  -> 用户提问
  -> 问题向量化
  -> 相似 Chunk 检索
  -> GPT 基于上下文回答
  -> 返回答案和引用来源
```

## 项目结构

```text
ai-rag-knowledge-base/
├─ app.py
├─ requirements.txt
├─ README.md
├─ data/
│  └─ company.txt
├─ static/
│  ├─ index.html
│  ├─ styles.css
│  └─ app.js
└─ screenshots/
   └─ rag-web-demo.png
```

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

设置 OpenAI API Key：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
```

启动服务：

```bash
uvicorn app:app --reload
```

打开 Web 页面：

```text
http://127.0.0.1:8000/
```

打开 API 文档：

```text
http://127.0.0.1:8000/docs
```

如果只是想本地预览页面和交互，不调用 OpenAI，可以开启 Demo Mode：

```powershell
$env:RAG_DEMO_MODE="true"
uvicorn app:app --reload
```

## 接口说明

### GET `/health`

健康检查接口。

### GET `/documents`

查看当前知识库文件列表。

### POST `/upload`

上传 PDF 文档。

请求类型：

```text
multipart/form-data
```

字段：

```text
file: PDF 文件
```

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
  "answer": "请假流程是：提前一天申请，领导审批，HR 备案。",
  "citations": [
    {
      "source": "company.txt",
      "location": "company profile"
    }
  ],
  "contexts": [
    {
      "text": "请假流程：...",
      "source": "company.txt",
      "location": "company profile"
    }
  ]
}
```

## 项目亮点

- 不是简单关键词匹配，而是完整 RAG 链路
- 支持 PDF 上传，接近真实企业知识库场景
- 回答返回引用来源，方便用户判断可信度
- 使用 ChromaDB 做本地向量库，适合 Demo 和快速迭代
- 使用 FastAPI 提供接口，方便后续接前端或部署
- 提供 Web 页面，面试官可以直观看到上传、提问、回答流程

## 后续优化

- 支持多文件批量上传
- 支持 Word / Excel / Markdown 文档解析
- 支持 OCR 图片识别
- 支持用户登录和权限控制
- 支持对话历史
- 支持文档删除和重新索引
- 支持 Docker 部署
- 增加自动化测试和 CI
