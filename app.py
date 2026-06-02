import hashlib
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_FILE = DATA_DIR / "company.txt"
STATIC_DIR = BASE_DIR / "static"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "company_knowledge"

load_dotenv(BASE_DIR / ".env")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEMO_MODE = os.getenv("RAG_DEMO_MODE", "false").lower() == "true"

app = FastAPI(
    title="AI Enterprise RAG Knowledge Base",
    description="A RAG demo with PDF upload, Chroma retrieval, source citations, and a web UI.",
    version="2.0.0",
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@dataclass(frozen=True)
class KnowledgeChunk:
    text: str
    source: str
    location: str
    chunk_index: int


class AskRequest(BaseModel):
    question: str = Field(..., examples=["What is the leave request process?"])


class SourceReference(BaseModel):
    source: str
    location: str


class RetrievedContext(BaseModel):
    text: str
    source: str
    location: str


class AskResponse(BaseModel):
    question: str
    answer: str
    citations: list[SourceReference]
    contexts: list[RetrievedContext]


class UploadResponse(BaseModel):
    filename: str
    message: str


class DocumentsResponse(BaseModel):
    documents: list[str]


def split_text(text: str, max_chars: int = 500) -> list[str]:
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


def split_company_sections(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sections = []
    current: list[str] = []

    for line in lines:
        starts_section = line.startswith("公司名称") or line.endswith("流程：")
        if starts_section and current:
            sections.append("\n".join(current))
            current = []
        current.append(line)

    if current:
        sections.append("\n".join(current))

    return sections


def load_company_chunks() -> list[KnowledgeChunk]:
    text = DATA_FILE.read_text(encoding="utf-8")
    return [
        KnowledgeChunk(text=chunk, source=DATA_FILE.name, location="company profile", chunk_index=index)
        for index, chunk in enumerate(split_company_sections(text))
    ]


def load_pdf_chunks(file_path: Path) -> list[KnowledgeChunk]:
    reader = PdfReader(str(file_path))
    chunks: list[KnowledgeChunk] = []

    for page_index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for chunk_index, chunk in enumerate(split_text(page_text, max_chars=500)):
            chunks.append(
                KnowledgeChunk(
                    text=chunk,
                    source=file_path.name,
                    location=f"page {page_index}",
                    chunk_index=chunk_index,
                )
            )

    return chunks


def load_all_chunks() -> list[KnowledgeChunk]:
    chunks = load_company_chunks()

    for file_path in sorted(UPLOAD_DIR.glob("*.pdf")):
        try:
            chunks.extend(load_pdf_chunks(file_path))
        except Exception:
            continue

    return chunks


def get_openai_client() -> OpenAI:
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")
    return OpenAI()


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def chunk_id(chunk: KnowledgeChunk) -> str:
    raw = f"{chunk.source}:{chunk.location}:{chunk.chunk_index}:{chunk.text}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def build_collection():
    chunks = load_all_chunks()
    if not chunks:
        raise HTTPException(status_code=400, detail="No knowledge documents found.")

    client = get_openai_client()
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = chroma_client.create_collection(name=COLLECTION_NAME)
    embeddings = embed_texts(client, [chunk.text for chunk in chunks])

    collection.upsert(
        ids=[chunk_id(chunk) for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=embeddings,
        metadatas=[
            {
                "source": chunk.source,
                "location": chunk.location,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    )
    return collection


def retrieve_with_openai(question: str, top_k: int = 3) -> list[RetrievedContext]:
    client = get_openai_client()
    query_embedding = embed_texts(client, [question])[0]
    collection = build_collection()
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    contexts = []
    for text, metadata in zip(results["documents"][0], results["metadatas"][0]):
        contexts.append(
            RetrievedContext(
                text=text,
                source=str(metadata.get("source", "")),
                location=str(metadata.get("location", "")),
            )
        )
    return contexts


def retrieve_for_demo(question: str, top_k: int = 3) -> list[RetrievedContext]:
    specific_keywords = [keyword for keyword in ["请假", "报销", "退款"] if keyword in question]
    generic_keywords = [
        keyword
        for keyword in ["流程", "公司", "未来科技", "审批", "备案"]
        if keyword in question
    ]
    keywords = specific_keywords or generic_keywords
    chunks = load_all_chunks()

    def score(chunk: KnowledgeChunk) -> int:
        return sum(1 for keyword in keywords if keyword in chunk.text)

    ranked = [(chunk, score(chunk)) for chunk in chunks]
    positive_matches = [item for item in ranked if item[1] > 0]
    selected = positive_matches if positive_matches else ranked[:1]
    selected = sorted(selected, key=lambda item: item[1], reverse=True)

    return [
        RetrievedContext(text=chunk.text, source=chunk.source, location=chunk.location)
        for chunk, _ in selected[:top_k]
        if chunk.text.strip()
    ]


def build_citations(contexts: list[RetrievedContext]) -> list[SourceReference]:
    seen = set()
    citations = []

    for context in contexts:
        key = (context.source, context.location)
        if key in seen:
            continue
        seen.add(key)
        citations.append(SourceReference(source=context.source, location=context.location))

    return citations


def answer_with_openai(question: str, contexts: list[RetrievedContext]) -> str:
    client = get_openai_client()
    context_text = "\n\n---\n\n".join(
        f"Source: {context.source}, {context.location}\n{context.text}" for context in contexts
    )
    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an enterprise knowledge base assistant. "
                    "Answer only from the provided context. "
                    "Include source references in the answer. "
                    "If the context does not contain the answer, say the knowledge base has no relevant information."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context_text}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def answer_for_demo(question: str, contexts: list[RetrievedContext]) -> str:
    if not contexts:
        return "知识库中没有找到相关信息。"

    source = contexts[0]
    return f"根据 {source.source}（{source.location}）：\n{source.text}"


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/documents", response_model=DocumentsResponse)
def documents():
    files = [DATA_FILE.name]
    files.extend(file_path.name for file_path in sorted(UPLOAD_DIR.glob("*.pdf")))
    return DocumentsResponse(documents=files)


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    target_path = UPLOAD_DIR / filename
    content = await file.read()
    target_path.write_bytes(content)
    build_collection.cache_clear()

    return UploadResponse(filename=filename, message="PDF uploaded. The vector index will refresh on the next question.")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    if os.getenv("OPENAI_API_KEY"):
        contexts = retrieve_with_openai(question)
        answer = answer_with_openai(question, contexts)
    elif DEMO_MODE:
        contexts = retrieve_for_demo(question)
        answer = answer_for_demo(question, contexts)
    else:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    return AskResponse(
        question=question,
        answer=answer,
        citations=build_citations(contexts),
        contexts=contexts,
    )
