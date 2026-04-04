from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langchain_core.documents import Document

from typing_extensions import TypedDict, Annotated, Any, List

import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from ..rag_core import setup_logger

logger = setup_logger("agent_graph.log", "agent_graph")


from .agent import (
    State,
    load_docs_node,
    # split_docs_node,
    vector_store_retriever_node,
    multi_query_node,
    generate_answer_node,
    retrieve_with_rrf_node,
)

def create_agent_graph() -> StateGraph:
    graph = StateGraph(State)

    # Define the nodes in the graph
    graph.add_node("load_docs", load_docs_node)
    # graph.add_node("split_docs", split_docs_node)
    graph.add_node("vector_store_retriever", vector_store_retriever_node)
    graph.add_node("multi_query", multi_query_node)
    graph.add_node("retrieve_with_rrf", retrieve_with_rrf_node)
    graph.add_node("generate_answer", generate_answer_node)

    # Define the edges between the nodes
    graph.add_edge(START, "load_docs")


    # graph.add_edge("load_docs", "split_docs")
    # graph.add_edge("split_docs", "vector_store_retriever")
    
    graph.add_edge("load_docs", "vector_store_retriever")
    graph.add_edge("vector_store_retriever", "multi_query")

    graph.add_edge("multi_query", "retrieve_with_rrf")

    # Final answer generation
    graph.add_edge("retrieve_with_rrf", "generate_answer")

    graph.add_edge("generate_answer", END)

    return graph.compile()

if __name__ == "__main__":
    class State(TypedDict):
        messages: Annotated[List[AnyMessage], add_messages]

        query: str
        queries: List[str]
        path_to_docs: str

        chunk_size: int
        chunk_overlap: int

        embed_model: str
        main_model: str
        llm: Any

        top_k_docs: int
        top_k_queries: int

        raw_docs: List[Document]
        split_docs: List[Document]
        retrieved_docs: str

        final_answer: str

    init_state: State = {
        "messages": [],

        "query": "Điều kiện để được xét công nhận tốt nghiệp đại học là gì?",
        "queries": [],
        "path_to_docs": "data/raw_documents",

        "chunk_size": 2000,
        "chunk_overlap": 200,

        "embed_model": "mxbai-embed-large",
        "main_model": "llama3:8b",

        "top_k_docs": 3,
        "top_k_queries": 3,

        "raw_docs": [],
        "split_docs": [],
        "retrieved_docs": "",

        "final_answer": "",
    }

    graph = create_agent_graph()
    final_state = graph.invoke(init_state)

    print(f"Final Answer: {final_state['final_answer']}")


    



