from pathlib import Path

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent
# ----------------------------------

## Data directories
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DOCS_DIR = DATA_DIR / "processed_documents"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
EMBEDDING_CACHE_DIR = DATA_DIR / "embedding_cache"
RAW_DOCS_DIR = DATA_DIR / "raw_documents"
CONVERSATION_DB_DIR = DATA_DIR / "conversation_db"
USER_CHAT_HISTORY_DATA = DATA_DIR / "chat_history_db"
DOCS_FOR_SCRAPE_DIR = DATA_DIR / "raw_docs_for_scrape"
# ----------------------------------

## Agent
# MODEL_NAME = "xiaomi/mimo-v2-omni"
MODEL_NAME = "openai/gpt-oss-120b"
# EMBED_MODEL_NAME = "hf.co/CompendiumLabs/bge-m3-gguf:latest"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# ----------------------------------

## RAG
### Retriever
RETRIEVER_TYPE = "hybrid"  # Options: "dense", "sparse", "hybrid"

### Config number
MAX_CONVERSATION_HISTORY = 5
# ----------------------------------

## Backend
DATABASE_DIR = ROOT_DIR / "database"
# ----------------------------------

## Public root
PUBLIC_ROOT = ROOT_DIR / "public"
# ----------------------------------

# CONFIG = "$env:PYTHONPATH = C:\university_chatbot"

