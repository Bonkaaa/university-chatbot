from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever

from langchain_classic.embeddings.cache import CacheBackedEmbeddings
from langchain_classic.storage import LocalFileStore  
from langchain_classic.indexes import SQLRecordManager, index

from pathlib import Path

from .data_ingestion.document_loaders import UniversityDocumentLoader
from .data_ingestion.text_splitter import create_splitter
from ..utils import setup_logger
from ...config import CHROMA_DB_DIR, EMBEDDING_CACHE_DIR, RAW_DOCS_DIR

logger = setup_logger("retriever.log", "retriever")


# ROOT_DIR = Path(__file__).parent.parent.parent.parent
# DATA_DIR = ROOT_DIR / "data"


def create_retriever(
    docs: list[Document],
    embed_model: str,
    type: str = "Dense",
    search_type: str = "similarity",
    k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
    persist_directory: str = str(CHROMA_DB_DIR),
    cache_directory: str = str(EMBEDDING_CACHE_DIR),
):
    # Two types of search: similarity and mmr
    # Similarity search retrieves the top k most similar documents based on cosine similarity.
    # MMR (Maximal Marginal Relevance) search retrieves documents that are both relevant to the query and diverse from each other, using a lambda parameter to balance relevance and diversity.

    # --- Sparse (BM25) Retriever ---
    if type == "Sparse":
        retriever = BM25Retriever.from_documents(
            documents=docs,
        )
        retriever.k = k
        return retriever

    # --- Base Embeddings ---
    base_embeddings = OllamaEmbeddings(
        model=embed_model,
    )

    # --- Embedding Cache ---
    store = LocalFileStore(cache_directory)

    cached_embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings=base_embeddings,
        document_embedding_cache=store,
        key_encoder="sha256"
    )
    logger.info(f"Initialized CacheBackedEmbeddings with cache directory: {cache_directory}")


    # --- Vector Store (Chroma) ---
    vector_stores = Chroma(
        persist_directory=persist_directory,
        embedding_function=cached_embeddings,
    )
    logger.info(f"Initialized Chroma vector store with persist directory: {persist_directory}")


    namespace = "chroma"
    record_manager = SQLRecordManager(
        namespace=namespace,
        db_url=f"sqlite:///{CHROMA_DB_DIR}/record_manager_cache.sql",
    )
    logger.info(f"Initialized SQLRecordManager with namespace: {namespace} and db_url: sqlite:///{CHROMA_DB_DIR}/record_manager_cache.sql")

    record_manager.create_schema()

    # Sync documents to vector store
    index(
        docs_source=docs,
        record_manager=record_manager,
        vector_store=vector_stores,
        cleanup="incremental",
        source_id_key="source",
        key_encoder="sha256",
    )
    logger.info(f"Indexed {len(docs)} documents into the vector store")

    search_kwargs = {
        "k": k,
    }

    if search_type == "mmr":
        search_kwargs["fetch_k"] = fetch_k
        search_kwargs["lambda_mult"] = lambda_mult
    
    return vector_stores.as_retriever(search_kwargs=search_kwargs, search_type=search_type)

if __name__ == "__main__":
    loader = UniversityDocumentLoader(RAW_DOCS_DIR)
    docs = loader.load_all_documents()

    text_splitter = create_splitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    retriever = create_retriever(
        docs=split_docs,
        embed_model="hf.co/CompendiumLabs/bge-m3-gguf",
    )

    print(retriever)

# python -m src.rag_core.components.retriever 
    

