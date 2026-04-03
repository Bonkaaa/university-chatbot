from langchain_core.documents import Document

from dotenv import load_dotenv
from typing import List, Any
# from ...components import load_docs, create_splitter, create_retriever, get_llm

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def multi_query(
    query: str,
    llm: Any,
    prompt_template: str,
    k_queries: int = 5,
) -> List[str]:

    multi_query_prompt = ChatPromptTemplate.from_template(prompt_template)

    generate_queries = (
        multi_query_prompt 
        | llm 
        | StrOutputParser()
        | (lambda x: x.split("\n"))
    )

    return generate_queries.invoke({"k_queries": k_queries, "question": query})

# def multi_query_raw(
#     query: str,
#     docs: List[Document],
#     k_queries: int = 5,
#     only_multi_query: bool = False,
# ) -> List[str]:
#     text_splitter = create_splitter(chunk_size=300, chunk_overlap=50)
#     docs_splits = text_splitter.split_documents(docs)

#     retriever = create_retriever(
#         docs=docs_splits,
#     )

#     llm = get_llm(
#         model_name="llama-3.1-8b-instant",
#         temperature=0.7,
#     )

#     multi_query_prompt = ChatPromptTemplate.from_template(MULTI_QUERY_TEMPLATE)

#     generate_queries = (
#         multi_query_prompt 
#         | llm 
#         | StrOutputParser()
#         | (lambda x: x.split("\n"))
#     )

#     # Support for multi queries RAG fusion
#     if only_multi_query:
#         return generate_queries.invoke({"k_queries": k_queries, "question": query}), retriever

#     queries = generate_queries.invoke({"k_queries": k_queries, "question": query})

#     unique_docs = set()

#     for q in queries:
#         retrieved_docs = retriever.invoke(q)
#         for doc in retrieved_docs:
#             if hasattr(doc, "page_content"):
#                 page_content = doc.page_content
#                 unique_docs.add(page_content)
#             else:
#                 continue

#     return list(unique_docs)


if __name__ == "__main__":
    pass