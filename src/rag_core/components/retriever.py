import os
from dotenv import load_dotenv
load_dotenv()

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEndpointEmbeddings

from langchain_classic.embeddings.cache import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore  
from langchain_classic.indexes import SQLRecordManager, index
from langchain_classic.retrievers.ensemble import EnsembleRetriever


from pathlib import Path
from typing import List

from .data_ingestion.document_loaders import UniversityDocumentLoader
from .data_ingestion.text_splitter import create_splitter
from ..utils import setup_logger
from ...config import CHROMA_DB_DIR, EMBEDDING_CACHE_DIR, RAW_DOCS_DIR
from src.app.db import SessionLocal
from src.app.models import DocumentChunk

import pickle

logger = setup_logger("retriever.log", "retriever")

hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")


class RetrieverComponent:
    def __init__(
        self,
        embed_model: str,
        persist_directory: str = str(CHROMA_DB_DIR),
        cache_directory: str = str(EMBEDDING_CACHE_DIR),
    ):
        self.embed_model = embed_model
        self.persist_directory = Path(persist_directory)
        self.cache_directory = Path(cache_directory)
        self.sparse_cache_directory = self.cache_directory / "bm25_cache.pkl"

        # # Initialize the retriever as None; it will be created when needed
        # base_embeddings = OllamaEmbeddings(
        #     model=embed_model,
        # )
        base_embeddings = HuggingFaceEndpointEmbeddings(
            model=embed_model,
            huggingfacehub_api_token=hf_token,
        )

        self.store = LocalFileStore(str(self.cache_directory))

        self.cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
            underlying_embeddings=base_embeddings,
            document_embedding_cache=self.store,
            key_encoder="sha256"
        )
        
        logger.info(f"Initialized RetrieverComponent with embedding model: {embed_model}, persist directory: {persist_directory}, cache directory: {cache_directory}")

    def _get_vector_store(self):
        return Chroma(
            embedding_function=self.cached_embeddings,
            persist_directory=str(self.persist_directory),
        )
    
    def _sync_index(self, docs: list[Document]):
        # Create a new index manager and index the documents
        vector_store = self._get_vector_store()
        record_manager = SQLRecordManager(
            namespace="chroma",
            db_url=f"sqlite:///{self.persist_directory}/record_manager_cache.sql",
        )
        logger.info("Created SQLRecordManager for index synchronization.")

        record_manager.create_schema()

        index_stats = index(
            docs_source=docs,
            record_manager=record_manager,
            vector_store=vector_store,
            cleanup="incremental",
            source_id_key="source",
            key_encoder="sha256",
        )

        logger.info(f"Index synchronization completed. Stats: {index_stats}")

        # Persist document chunk records for provenance/linking
        try:
            db = SessionLocal()
            for d in docs:
                meta = d.metadata or {}
                doc_id = meta.get("document_id") if isinstance(meta, dict) else None
                if not doc_id:
                    # try to extract from source
                    source = meta.get("source") if isinstance(meta, dict) else None
                    if source:
                        fname = os.path.basename(source)
                        m = None
                        try:
                            import re
                            m = re.match(r'^([0-9a-fA-F-]{36})_', os.path.splitext(fname)[0])
                        except Exception:
                            m = None
                        if m:
                            doc_id = m.group(1)

                if not doc_id:
                    continue

                chunk_index = meta.get("chunk_index", 0) if isinstance(meta, dict) else 0

                # Skip if already exists
                exists = db.query(DocumentChunk).filter_by(document_id=doc_id, chunk_index=chunk_index).first()
                if exists:
                    continue

                record = DocumentChunk(
                    document_id=doc_id,
                    chunk_index=chunk_index,
                    source=meta.get("source") if isinstance(meta, dict) else None,
                    chuong=meta.get("chuong") if isinstance(meta, dict) else None,
                    dieu=meta.get("dieu") if isinstance(meta, dict) else None,
                    content=d.page_content if hasattr(d, 'page_content') else None,
                    external_vector_id=None,
                )
                db.add(record)
            db.commit()
        except Exception:
            logger.exception("Failed to persist document chunk records")
        finally:
            try:
                db.close()
            except Exception:
                pass

        return vector_store
    
    def get_sparse_retriever(self, docs: list[Document], k: int = 5, force_refresh: bool = False) -> BM25Retriever:
        if self.sparse_cache_directory.exists() and not force_refresh:
            logger.info(f"Loading BM25 retriever from cache at {self.sparse_cache_directory}")
            with open(self.sparse_cache_directory, "rb") as f:
                retriever = pickle.load(f)
        
        else:
            logger.info("Creating new BM25 retriever and caching it.")
            retriever = BM25Retriever.from_documents(
                documents=docs,
            )
            self.sparse_cache_directory.parent.mkdir(parents=True, exist_ok=True)
            with open(self.sparse_cache_directory, "wb") as f:
                pickle.dump(retriever, f)

        retriever.k = k
        return retriever
    
    def get_dense_retriever(
        self,
        docs: list[Document],
        k: int = 5,
        search_type: str = "similarity",
        **kwargs
    ):
        vector_store = self._sync_index(docs)
        search_kwargs = {
            "k": k,
            **kwargs
        }

        return vector_store.as_retriever(search_kwargs=search_kwargs, search_type=search_type)
    
    def get_hybrid_retriever(
        self,
        docs: list[Document],
        k: int = 5,
        weights: List[float] = [0.7, 0.3],
        force_refresh_sparse: bool = False,
    ):
        dense = self.get_dense_retriever(docs, k=k)
        sparse = self.get_sparse_retriever(docs, k=k, force_refresh=force_refresh_sparse)

        return EnsembleRetriever(
            retrievers=[dense, sparse],
            weights=weights,
            c=60,  # Number of documents to return before re-ranking
        )
    
if __name__ == "__main__":
    loader = UniversityDocumentLoader(RAW_DOCS_DIR)
    documents = loader.load_all_documents()

    retriever_component = RetrieverComponent(
        embed_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        persist_directory=str(CHROMA_DB_DIR),
        cache_directory=str(EMBEDDING_CACHE_DIR),
    )

    hybrid_retriever = retriever_component.get_hybrid_retriever(
        docs=documents, 
        k=5,
        weights=[0.7, 0.3],
        force_refresh_sparse=True
    )

    logger.info("Sync process completed. Ready to retrieve documents.")