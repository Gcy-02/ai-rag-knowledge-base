# ai-rag-knowledge-base 学习指南

这份文件是给自己学习和面试复盘用的，不是正式产品文档。目标很简单：你能自己把这个 RAG 项目讲清楚，并且能现场跑起来。

## 先记住一句话

这个项目做的是：

```text
把企业资料放进知识库，用户提问后，系统先检索相关片段，再让 GPT 基于片段回答，并返回引用来源。
```

不要一上来背很多术语。先把这句话讲顺。

## 运行项目

进入项目目录：

```powershell
cd E:\biancheng\601practice\ai-rag-knowledge-base
```

安装依赖：

```powershell
pip install -r requirements.txt
```

如果只是看页面和流程：

```powershell
$env:RAG_DEMO_MODE="true"
uvicorn app:app --reload
```

如果要跑真实 Embedding + GPT：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
uvicorn app:app --reload
```

打开：

```text
http://127.0.0.1:8000/
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## 你先看这几个文件

```text
app.py              后端主逻辑
data/company.txt    内置知识库资料
static/index.html   页面结构
static/app.js       页面请求接口的逻辑
static/styles.css   页面样式
README.md           GitHub 展示文档
PROJECT_NOTES.md    面试讲解笔记
```

如果时间少，先看 `app.py` 和 `PROJECT_NOTES.md`。

## app.py 里最重要的流程

### 1. 读取资料

相关函数：

```python
load_company_chunks()
load_pdf_chunks()
load_all_chunks()
```

你可以这么讲：

> 项目默认读取 `company.txt`，如果用户上传 PDF，就用 `pypdf` 提取文本，再一起放进知识库。

### 2. 切 Chunk

相关函数：

```python
split_text()
split_company_sections()
```

你可以这么讲：

> V1 里没有做复杂的 token 切分，先按段落和流程标题切块。这样好理解，也方便展示 Top-K 召回。

### 3. 生成 Embedding

相关函数：

```python
embed_texts()
```

你可以这么讲：

> Embedding 的作用是把文本变成向量。知识块会变成向量，用户问题也会变成向量，后面才能做相似度检索。

### 4. 存进 ChromaDB

相关函数：

```python
build_collection()
```

你可以这么讲：

> ChromaDB 是本地向量库。项目会把每个 Chunk 的文本、向量、来源文件和页码信息都存进去。

### 5. 提问和检索

相关函数：

```python
retrieve_with_openai()
retrieve_for_demo()
```

你可以这么讲：

> 正常模式用 OpenAI Embedding + ChromaDB 做 Top-K 检索。Demo Mode 没有 API Key，所以用关键词匹配模拟检索，主要为了展示页面流程。

### 6. GPT 回答

相关函数：

```python
answer_with_openai()
answer_for_demo()
```

你可以这么讲：

> 真正回答时，不是直接把问题扔给 GPT，而是先把检索到的上下文拼进去，让模型只基于这些资料回答。

## 接口怎么记

### `GET /`

打开网页。

### `GET /documents`

看现在知识库里有哪些文件。

### `GET /stats`

看文档数、知识块数、PDF 数量、Top-K。

### `POST /upload`

上传 PDF。

### `POST /ask`

提交问题，返回：

```text
answer      回答
citations   引用来源
contexts    Top-K 召回结果
```

面试时重点讲 `/ask`，因为它最能体现 RAG。

## 面试官可能会问什么

### Q1：RAG 是什么？

可以这样答：

> RAG 就是先检索，再生成。用户提问后，系统先从知识库里找相关内容，再把这些内容交给大模型回答。这样比直接问大模型更适合企业知识库，因为回答有资料依据。

### Q2：为什么要切 Chunk？

可以这样答：

> 文档太长不能直接全部塞给模型，也不利于检索。所以要切成小块，每个 Chunk 单独做 Embedding。用户提问时，只召回最相关的几个 Chunk。

### Q3：Top-K 是什么？

可以这样答：

> Top-K 就是取最相关的 K 个知识块。比如 Top-K=3，就返回相似度最高的 3 个 Chunk。页面里把这 3 个结果展示出来，是为了让检索过程更可验证。

### Q4：为什么要引用来源？

可以这样答：

> 企业知识库不能只给一个看起来流畅的回答，还要让用户知道答案来自哪个文件、哪一页或哪一段。这个项目现在返回的是 source 和 location。

### Q5：这个项目的边界是什么？

可以这样答：

> 当前版本只处理文本型 PDF，不做 OCR；上传文件没有删除和权限管理；Demo Mode 只是展示流程。后续我会优先做文档管理和更精确的引用定位。

## 你可以现场改的小功能

如果面试官让你现场改，优先改这些小功能：

1. 把 Top-K 从 3 改成 5。
2. 给 `/stats` 多返回一个 `mode` 字段，显示当前是 Demo Mode 还是真实 OpenAI 模式。
3. 给上传接口限制文件大小。
4. 在回答里显示更多来源信息。

这些改动都不大，但能证明你真的懂代码。

## 最后自己检查一遍

你能讲清楚这几个问题，就差不多了：

- 资料从哪里来？
- Chunk 是怎么切的？
- Embedding 在哪里做？
- ChromaDB 在哪里用？
- `/ask` 接口做了几步？
- Demo Mode 和真实模式有什么区别？
- 当前项目哪里还不完善？

不要背得太满。讲清楚主流程，比说一堆高级词更重要。
