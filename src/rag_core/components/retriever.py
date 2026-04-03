from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever

from .data_ingestion.document_loaders import UniversityDocumentLoader
from .data_ingestion.text_splitter import create_splitter

def create_retriever(
    docs: list[Document],
    embed_model: str,
    type: str = "Dense",
    search_type: str = "similarity",
    k: int = 5,
    fetch_k: int = 20,
    lambda_mult: float = 0.5,
):
    # Two types of search: similarity and mmr
    # Similarity search retrieves the top k most similar documents based on cosine similarity.
    # MMR (Maximal Marginal Relevance) search retrieves documents that are both relevant to the query and diverse from each other, using a lambda parameter to balance relevance and diversity.

    if type == "Sparse":
        retriever = BM25Retriever.from_documents(
            documents=docs,
        )
        retriever.k = k
        return retriever

    embeddings = OllamaEmbeddings(
        model=embed_model,
    )

    vector_stores = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
    )

    search_kwargs = {
        "k": k,
    }

    if search_type == "mmr":
        search_kwargs["fetch_k"] = fetch_k
        search_kwargs["lambda_mult"] = lambda_mult
    
    return vector_stores.as_retriever(search_kwargs=search_kwargs, search_type=search_type)

if __name__ == "__main__":
    loader = UniversityDocumentLoader("data/raw_documents")
    docs = loader.load_all_documents()

    text_splitter = create_splitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    retriever = create_retriever(
        docs=split_docs,
        embed_model="mxbai-embed-large",
    )

    # query = "Điều kiện để được xét công nhận tốt nghiệp đại học là gì?"

    # retrieved_docs = retriever.invoke(query)

    # Save retrieved documents to a text file for inspection
    # with open("retrieved_docs.txt", "w", encoding="utf-8") as f:
    #     for i, doc in enumerate(retrieved_docs):
    #         doc_id = doc.metadata.get("source", f"unknown_id_{i}")
    #         content = doc.page_content
    #         f.write(f"Document ID: {doc_id}\nContent: {content}\n---\n")


    # print(f"Retrieved {len(retrieved_docs)} documents:")
    # print("\n---\n".join([f"Document ID: {doc.metadata.get('source', 'unknown_id')}\nContent: {doc.page_content}" for doc in retrieved_docs]))

    # Save split documents to a text file for inspection
    with open("split_docs.txt", "w", encoding="utf-8") as f:
        for i, doc in enumerate(split_docs):
            doc_id = doc.metadata.get("source", f"unknown_id_{i}")
            content = doc.page_content
            f.write(f"Document ID: {doc_id}\nContent: {content}\n---\n")
    
    

