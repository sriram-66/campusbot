import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import config, db, rag


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    db.init_db()
    db.init_feedback()
    n = rag.ingest_folder()
    print(f"Ingested {n} chunks from {config.DATA_DIR}/")
    yield


app = FastAPI(title="CampusBot", lifespan=lifespan)


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


class FeedbackRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    rating: int  # 1 = helpful, -1 = not helpful


def require_admin(token: str | None):
    if token != config.ADMIN_TOKEN:
        raise HTTPException(401, "Invalid admin token")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(400, "Message cannot be empty")
    history = db.get_history(req.session_id)
    answer, sources = rag.answer(req.message, history)
    db.save_message(req.session_id, "user", req.message)
    db.save_message(req.session_id, "assistant", answer)
    return ChatResponse(answer=answer, sources=sources)


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    if req.rating not in (1, -1):
        raise HTTPException(400, "Rating must be 1 or -1")
    db.save_feedback(req.session_id, req.question, req.answer, req.rating)
    return {"status": "saved"}


@app.post("/admin/upload")
async def upload(file: UploadFile = File(...), x_admin_token: str | None = Header(None)):
    require_admin(x_admin_token)
    if not file.filename.lower().endswith((".pdf", ".txt", ".md")):
        raise HTTPException(400, "Only PDF, TXT, or MD files are allowed")
    name = os.path.basename(file.filename)
    path = os.path.join(config.DATA_DIR, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    chunks = rag.ingest_file(path)
    return {"file": name, "chunks": chunks}


@app.get("/admin/stats")
def stats(x_admin_token: str | None = Header(None)):
    require_admin(x_admin_token)
    return {
        "documents": sorted(os.listdir(config.DATA_DIR)),
        "chunks": rag.collection.count(),
        "feedback": db.feedback_stats(),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
