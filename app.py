import os
from functools import lru_cache
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "company.txt"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "company_knowledge"

load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

app = FastAPI(
    title="AI Enterprise RAG Knowledge Base",
    description="A minimal RAG demo built with FastAPI, OpenAI Embeddings, Chroma, and GPT.",
    version="1.0.0",
)


class AskRequest(BaseModel):
    question: str = Field(..., examples=["请假流程是什么？"])


class AskResponse(BaseModel):
    question: str
    answer: str
    contexts: list[str]


def load_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def split_chunks(text: str, max_chars: int = 120) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    chunks = []
    current = ""

    for paragraph in paragraphs:
        if not current:
            current = paragraph
        elif len(current) + len(paragraph) + 2 <= max_chars:
            current = f"{current}\n\n{paragraph}"
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def get_openai_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="请先设置 OPENAI_API_KEY 环境变量。")
    return OpenAI()


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


@lru_cache(maxsize=1)
def get_collection():
    client = get_openai_client()
    text = load_text(DATA_FILE)
    chunks = split_chunks(text)
    embeddings = embed_texts(client, chunks)

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    ids = [f"chunk-{index}" for index in range(len(chunks))]
    collection.upsert(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": DATA_FILE.name, "chunk": index} for index in range(len(chunks))],
    )
    return collection


def retrieve(client: OpenAI, question: str, top_k: int = 3) -> list[str]:
    query_embedding = embed_texts(client, [question])[0]
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    return results["documents"][0]


def answer_question(client: OpenAI, question: str, contexts: list[str]) -> str:
    context_text = "\n\n---\n\n".join(contexts)
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是企业知识库助手。只根据提供的资料回答问题；资料没有的信息，就说知识库里没有相关信息。",
            },
            {
                "role": "user",
                "content": f"资料：\n{context_text}\n\n问题：{question}",
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


@app.get("/")
def home():
    return {
        "name": "AI Enterprise RAG Knowledge Base",
        "docs": "/docs",
        "ask": "/ask",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空。")

    client = get_openai_client()
    contexts = retrieve(client, question)
    answer = answer_question(client, question, contexts)

    return AskResponse(question=question, answer=answer, contexts=contexts)
