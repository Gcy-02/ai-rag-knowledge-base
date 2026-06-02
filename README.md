# AI 企业知识库 RAG 助手

这是一个小型但完整的 RAG 项目。我没有一开始就做很重的系统，比如登录、权限、Docker、复杂后台管理，而是先把最关键的一条链路跑通：

上传资料，提问，检索相关内容，再让模型基于资料回答。

![RAG Web Demo](screenshots/rag-web-demo.png)

## 这个项目解决什么

企业内部经常有一类很具体的问题：

- 请假流程怎么走？
- 报销要经过谁审批？
- 退款多久处理？
- 员工手册里某一条制度到底怎么说？

这些信息可能散在 txt、PDF、员工手册、制度文档里。人当然可以自己翻，但真实场景里，大家更想直接问一句，然后拿到一个有来源的回答。

这个项目就是围绕这个场景做的：把企业资料放进知识库，让用户可以用自然语言提问。

## 当前做到哪一步

现在已经做到一个可以展示的版本：

- 内置 `company.txt` 作为基础企业资料
- 支持上传 PDF
- 支持把文本切成 Chunk
- 支持 OpenAI Embedding
- 支持 ChromaDB 向量检索
- 支持 GPT 基于检索结果回答
- 支持返回引用来源
- 支持一个最简单的网页界面
- README 里放了项目截图，方便 GitHub 直接展示

说白了，它还不是一个企业级系统，但已经能把 RAG 项目的主干讲清楚。

## 技术栈

- Python
- FastAPI
- OpenAI Embeddings
- OpenAI Chat Completions
- ChromaDB
- pypdf
- HTML / CSS / JavaScript
- Uvicorn

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

这里我比较在意的是“引用来源”。只给一个流畅回答，其实不够像知识库；用户还要知道这个回答是从哪段资料来的。哪怕现在只是 `source + location`，也比纯聊天式回答更可信。

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

## 快速运行

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

打开网页：

```text
http://127.0.0.1:8000/
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

## 没有 API Key 怎么预览

如果只是想看页面效果和基本交互，可以开 Demo Mode：

```powershell
$env:RAG_DEMO_MODE="true"
uvicorn app:app --reload
```

这个模式主要是为了展示页面和流程，不等于真实的 Embedding + GPT 问答。真正的 RAG 问答还是需要配置 `OPENAI_API_KEY`。

## 接口说明

### `GET /health`

健康检查。

### `GET /documents`

查看当前知识库里的文件列表。

### `POST /upload`

上传 PDF 文档。

请求类型：

```text
multipart/form-data
```

字段：

```text
file: PDF 文件
```

### `POST /ask`

向知识库提问。

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

## 我觉得这个项目最能展示的点

第一，它不是只写了一个调用 GPT 的接口。项目里有资料解析、切块、Embedding、向量检索、回答生成和来源返回，RAG 的基本结构是完整的。

第二，它有网页界面和截图。面试官打开 GitHub，不需要先读很多代码，就能大概知道这个项目是干什么的。

第三，它保留了边界。比如 PDF 解析现在只处理文本型 PDF，不做 OCR；上传文件也只是最小版本，没有做用户系统和权限。这个阶段先把主流程做好，比一上来堆很多半成品功能更重要。

## 后续可以继续做什么

- 支持多文件批量上传
- 支持 Word / Excel / Markdown 文档解析
- 支持 OCR 图片识别
- 支持文档删除和重新索引
- 支持对话历史
- 支持用户登录和权限控制
- 支持 Docker 部署
- 增加自动化测试和 CI

如果继续升级，我会优先做“文档管理”和“引用定位更精确”。因为这两个点更接近真实知识库，而不是只把页面做得更热闹。
