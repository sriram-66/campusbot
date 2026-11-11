import os
import chromadb
from openai import OpenAI
from pypdf import PdfReader
from . import config

_client = None


def get_client():
    global _client
    if _client is None:
        if not config.LLM_API_KEY:
            raise RuntimeError(f"{config.KEY_ENV_NAME} is not set")
        _client = OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)
    return _client


chroma = chromadb.PersistentClient(path=config.CHROMA_DIR)
collection = chroma.get_or_create_collection("college_docs")

SYSTEM_PROMPT = (
    "You are CampusBot, a helpful assistant for college students. "
    "Answer ONLY using the context provided. If the answer is not in the "
    "context, reply exactly: \"I don't know, please contact the college office.\" "
    "Keep answers short and clear."
)


def read_file(path: str) -> str:
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str):
    step = config.CHUNK_SIZE - config.CHUNK_OVERLAP
    return [text[i:i + config.CHUNK_SIZE] for i in range(0, len(text), step) if text[i:i + config.CHUNK_SIZE].strip()]


def ingest_file(path: str) -> int:
    """Split a file into chunks and store them in ChromaDB."""
    name = os.path.basename(path)
    chunks = chunk_text(read_file(path))
    if not chunks:
        return 0
    collection.upsert(
        ids=[f"{name}-{i}" for i in range(len(chunks))],
        documents=chunks,
        metadatas=[{"source": name} for _ in chunks],
    )
    return len(chunks)


def ingest_folder(folder: str = config.DATA_DIR) -> int:
    total = 0
    if not os.path.isdir(folder):
        return 0
    for f in os.listdir(folder):
        if f.lower().endswith((".pdf", ".txt", ".md")):
            total += ingest_file(os.path.join(folder, f))
    return total


def retrieve(question: str):
    if collection.count() == 0:
        return [], []
    res = collection.query(query_texts=[question], n_results=config.TOP_K)
    return res["documents"][0], [m["source"] for m in res["metadatas"][0]]


def answer(question: str, history: list[dict]):
    """history: [{'role': 'user'|'assistant', 'content': str}, ...]"""
    docs, sources = retrieve(question)
    context = "\n\n---\n\n".join(docs) if docs else "No documents available."

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}]
    )

    response = get_client().chat.completions.create(
        model=config.MODEL,
        max_tokens=1500,
        temperature=0.2,
        messages=messages,
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        text = "I don't know, please contact the college office."
    return text, sorted(set(sources))
