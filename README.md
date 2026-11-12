# CampusBot

An AI chatbot that answers student questions about admissions, fees, exams, and hostels using a college's own documents (Retrieval-Augmented Generation).

   **Live demo:** https://campusbot-lr7z.onrender.com

## Features
- Answers only from uploaded college documents, with source references
- Replies "I don't know, please contact the college office" when the answer isn't in the documents
- Remembers recent messages in a conversation (SQLite)
- Helpful / Not helpful feedback on every answer
- Admin page to upload new PDFs or text files and review feedback
- Dockerized for deployment

## Tech stack
Python, FastAPI, ChromaDB (vector search), Google Gemini API (free tier), SQLite, HTML/CSS/JavaScript, Docker

## How it works
1. Documents in `data/` are split into overlapping chunks and stored in ChromaDB.
2. For each question, the 3 most similar chunks are retrieved.
3. The chunks and recent chat history are sent to the LLM, which is instructed to answer only from that context.
4. The answer and its sources are returned to the chat UI.

## Run locally
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
export ADMIN_TOKEN=your_password
uvicorn app.main:app --reload
```
- Chat: http://localhost:8000
- Admin: http://localhost:8000/admin.html
- API docs: http://localhost:8000/docs

## Run with Docker
```bash
docker build -t campusbot .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key -e ADMIN_TOKEN=your_password campusbot
```

## Deploy on Render
1. Push this folder to a GitHub repo.
2. On render.com, create a **New Web Service** and connect the repo.
3. Choose **Docker** as the runtime.
4. Add environment variables `GEMINI_API_KEY` and `ADMIN_TOKEN`.
5. Deploy, then open the URL Render gives you.

Note: on free tiers the disk resets on redeploy, so uploaded documents, chat history, and feedback are lost. Attach a persistent disk (and set `DATA_DIR`, `CHROMA_DIR`, `DB_PATH` to paths on it) for permanent storage.

## API
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/chat` | Ask a question |
| POST | `/feedback` | Rate an answer |
| POST | `/admin/upload` | Upload a document (needs `X-Admin-Token`) |
| GET | `/admin/stats` | Documents and feedback stats (needs `X-Admin-Token`) |

## Future improvements
- Streaming responses
- Per-department document filters
- Student login

## Switching the AI provider
Set `LLM_PROVIDER` to `gemini` (default), `groq`, or `openai`, and set that provider's key
(`GEMINI_API_KEY`, `GROQ_API_KEY`, or `OPENAI_API_KEY`). Use `MODEL` to choose a different model.
