from dotenv import load_dotenv
from .multi_query import multi_query
from .utils import convert_to_ranked_results

import os
load_dotenv()

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document

from typing import Any, Any, Tuple, List, Dict


def _get_docs_from_retriever(query, retriever):
    if hasattr(retriever, "invoke"):
        docs = retriever.invoke(query)
    else:
        docs = retriever.get_relevant_documents(query)

    docs = list(docs) if docs is not None else []
    return docs

RetrivalItem = Tuple[str, str, Document] # (doc_id, page_content, payload)
FusedItem = Tuple[str, float, Document] # (doc_id, fused_score, payload)

def rank_fusion_rrf(
    retrival_results: List[List[RetrivalItem]],
    k: int = 60,
    weights: List[float] = None,
) -> List[FusedItem]:
    if weights is None:
        weights = [1.0] * len(retrival_results)
    if len(weights) != len(retrival_results):
        raise ValueError("Length of weights must match the number of retrival result lists.")
    
    fused_scores: Dict[str, float] = {}
    doc_payloads: Dict[str, Document] = {}

    for retriever_idx, retrieval_list in enumerate(retrival_results):
        weight = weights[retriever_idx]

        for rank_idx, (doc_id, page_content, payload) in enumerate(retrieval_list):
            rank = rank_idx + 1
            
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + weight * (1.0 / (k+rank))

            if doc_id not in doc_payloads:
                doc_payloads[doc_id] = payload
            
    docs_id_sorted = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

    fused_results: List[FusedItem] = [(doc_id, fused_scores[doc_id], doc_payloads[doc_id]) for doc_id, _ in docs_id_sorted]

    return fused_results

# def rag_fusion_pipeline(
#     query: str,
#     docs: List[Document],
#     llm: Any,
#     retriever: Any,
#     prompt_template: str,
#     top_k: int = 5,
# ) -> List[Document]: 
#     queries = multi_query(
#         query=query,
#         llm=llm,
#         prompt_template=prompt_template,
#         k_queries=top_k,
#     )

#     # Remove empty queries and strip whitespace
#     queries = [q.strip() for q in queries if q.strip() != ""]

#     retrieval_results = []

#     for q in queries:
#         retrieval_docs = _get_docs_from_retriever(q, retriever)
#         ranked_results = convert_to_ranked_results(retrieval_docs)
#         retrieval_results.append(ranked_results)

#     fused_results = rank_fusion_rrf(retrieval_results, k=60)

#     docs = [item[2] for item in fused_results[:top_k]]

#     return docs

def _format_retrieval_results(retrieval_docs: List[Document]) -> str:
    formatted_results = []
    for i, doc in enumerate(retrieval_docs):
        page_content = doc.page_content
        formatted_results.append(f"Nội dung của tài liệu {i+1}: {page_content}\n---")
    return "\n".join(formatted_results)


def retrieve_with_rrf(
    queries: List[str],
    retriever: Any,
    top_k: int,
) -> str: 
    queries = [q.strip() for q in queries if q.strip() != ""]

    retrieval_results = []

    for q in queries:
        retrieval_docs = _get_docs_from_retriever(q, retriever)
        ranked_results = convert_to_ranked_results(retrieval_docs)
        retrieval_results.append(ranked_results)

    fused_results = rank_fusion_rrf(retrieval_results, k=60)

    docs = [item[2] for item in fused_results[:top_k]]

    formatted_docs = _format_retrieval_results(docs)

    return formatted_docs
    

if __name__ == "__main__":
    pass

