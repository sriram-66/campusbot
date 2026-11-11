import os

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
_PRESETS = {
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-flash-latest"),
    "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini"),
}
KEY_ENV_NAME, _base_url, _model = _PRESETS.get(PROVIDER, _PRESETS["gemini"])
LLM_API_KEY = os.getenv(KEY_ENV_NAME, "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", _base_url)
MODEL = os.getenv("MODEL", _model)
DATA_DIR = os.getenv("DATA_DIR", "data")
CHROMA_DIR = os.getenv("CHROMA_DIR", "chroma_store")
DB_PATH = os.getenv("DB_PATH", "chat.db")
TOP_K = 3
CHUNK_SIZE = 800      # characters per chunk
CHUNK_OVERLAP = 100
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "change-me")
