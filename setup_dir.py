from src.config import (
    DATA_DIR,
    PROCESSED_DOCS_DIR,
    CHROMA_DB_DIR,
    EMBEDDING_CACHE_DIR,
    RAW_DOCS_DIR,
    CONVERSATION_DB_DIR,
    USER_CHAT_HISTORY_DATA,
    DOCS_FOR_SCRAPE_DIR,
    DATABASE_DIR,
)

import os

def setup_directories():
    directories = [
        DATA_DIR,
        PROCESSED_DOCS_DIR,
        CHROMA_DB_DIR,
        EMBEDDING_CACHE_DIR,
        RAW_DOCS_DIR,
        CONVERSATION_DB_DIR,
        USER_CHAT_HISTORY_DATA,
        DOCS_FOR_SCRAPE_DIR,
        DATABASE_DIR,
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory '{directory}' is set up.")

if __name__ == "__main__":
    setup_directories()