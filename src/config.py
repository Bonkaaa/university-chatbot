from pathlib import Path

### Root directory of the project
ROOT_DIR = Path(__file__).parent.parent

# Data directories
DATA_DIR = ROOT_DIR / "data"
PROCESSED_DOCS_DIR = DATA_DIR / "processed_documents"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"
EMBEDDING_CACHE_DIR = DATA_DIR / "embedding_cache"
RAW_DOCS_DIR = DATA_DIR / "raw_documents"
CONVERSATION_DB_DIR = DATA_DIR / "conversation_db"

# Agent
MODEL_NAME = "xiaomi/mimo-v2-omni"
EMBED_MODEL_NAME = "hf.co/CompendiumLabs/bge-m3-gguf:latest"

# Config number
MAX_CONVERSATION_HISTORY = 5

