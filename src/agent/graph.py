from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langchain_core.documents import Document
from langgraph.checkpoint.sqlite import SqliteSaver

from typing_extensions import TypedDict, Annotated, Any, List

import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()  # Load environment variables from .env file

from ..rag_core import setup_logger, create_thread_id

logger = setup_logger("agent_graph.log", "agent_graph")


from .agent import (
    State,
    load_docs_node,
    generate_answer_node,
    retrieve_with_retriever_node
)

# def create_agent_graph() -> StateGraph:
#     graph = StateGraph(State)

#     # Define the nodes in the graph
#     graph.add_node("load_docs", load_docs_node)
#     graph.add_node("vector_store_retriever", vector_store_retriever_node)
#     graph.add_node("retrieve_with_retriever", retrieve_with_retriever_node)
#     graph.add_node("generate_answer", generate_answer_node)

#     # Define the edges between the nodes
#     graph.add_edge(START, "load_docs")
#     graph.add_edge("load_docs", "vector_store_retriever")
#     graph.add_edge("vector_store_retriever", "retrieve_with_retriever")
#     graph.add_edge("retrieve_with_retriever", "generate_answer")

#     graph.add_edge("generate_answer", END)

#     return graph.compile()


class RAGAgent:
    def __init__(
        self, 
        conversation_db_path: str,

        path_to_docs: str,

        embed_model: str,
        main_model: str,

        top_k_docs: int = 5,
        
        split_docs: List[Document] =[],
        retrieved_docs: List[Document] =[],
    ):
        if not os.path.exists(conversation_db_path):
            # Create the database file if it doesn't exist
            os.makedirs(os.path.dirname(conversation_db_path), exist_ok=True)
            with open(conversation_db_path, 'w') as f:
                pass  # Just create an empty file
        self.db_path = conversation_db_path


        self.path_to_docs = path_to_docs
        self.embed_model = embed_model
        self.main_model = main_model
        self.top_k_docs = top_k_docs
        self.split_docs = split_docs
        self.retrieved_docs = retrieved_docs


        self.builder = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(State)

        # Define the nodes in the graph
        graph.add_node("load_docs", load_docs_node)
        graph.add_node("retrieve_with_retriever", retrieve_with_retriever_node)
        graph.add_node("generate_answer", generate_answer_node)

        # Define the edges between the nodes
        graph.add_edge(START, "load_docs")
        graph.add_edge("load_docs", "retrieve_with_retriever")
        graph.add_edge("retrieve_with_retriever", "generate_answer")

        graph.add_edge("generate_answer", END)

        return graph

    def chat(
        self,
        query: str,
    ):
        with SqliteSaver.from_conn_string(self.db_path) as checkpointer:
            graph = self.builder.compile(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": create_thread_id(),
                }
            }

            init_state: State = {
                "query": query,
                "path_to_docs": self.path_to_docs,

                "embed_model": self.embed_model,
                "main_model": self.main_model,

                "top_k_docs": self.top_k_docs,

                "split_docs": self.split_docs,
                "retrieved_docs": self.retrieved_docs,

                "final_answer": {
                    "answer": "",
                    "confidence": 0.0,
                    "follow_up_question": [],
                    "intent": "",
                },
            }

            response = graph.invoke(init_state, config=config)

            return response

            

if __name__ == "__main__":
    pass