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
from src.app.crud.document_metadata_crud import create_document_metadata
from src.app.models.document_metadata import DocumentMetadata
import os

from sqlalchemy.orm import Session
from src.app.db import engine, Base, SessionLocal

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

# Setup database and add metadata table for initial documents
def setup_database():
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()

    try:
        for doc in RAW_DOCS_DIR.glob("*"):

            existing = db.query(DocumentMetadata).filter(DocumentMetadata.file_name == doc.name).first()

            if not existing:
                create_document_metadata(
                    db=db,
                    title=doc.stem,
                    file_name=doc.name,
                    file_type=doc.suffix[1:],  # Remove the dot from suffix
                    file_size=doc.stat().st_size / 1024,  # Size in KB
                    uploaded_by=1,  # Assuming '1' is the admin user ID
                )
                print(f"Added metadata for '{doc.name}' to the database.")
            else:
                print(f"Metadata for '{doc.name}' already exists in the database.")
    finally:
        db.close()

if __name__ == "__main__":
    setup_directories()
    setup_database()
    # Delete the all the row in the document metadata table to reset the metadata
    # db: Session = SessionLocal()
    # try:
    #     deleted = db.query(DocumentMetadata).delete()
    #     db.commit()
    #     print(f"Deleted {deleted} rows from the document metadata table.")
    # finally:
    #     db.close()