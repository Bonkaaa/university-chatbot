from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langchain_core.documents import Document
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from typing_extensions import TypedDict, Annotated, Any, List

import os
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()  # Load environment variables from .env file

from ..rag_core import setup_logger

logger = setup_logger("agent_graph.log", "agent_graph")


from .agent import (
    State,
    load_docs_node,
    generate_answer_node,
    retrieve_with_retriever_node
)

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
        conversation_db_path = Path(conversation_db_path) / "conversations_db.json"

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

    async def astream_chat(
        self,
        query: str,
        thread_id: str,
    ):
        async with AsyncSqliteSaver.from_conn_string(self.db_path) as checkpointer:
            graph = self.builder.compile(checkpointer=checkpointer)

            config = {
                "configurable": {
                    "thread_id": thread_id,
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

            previous_answer = ""
            final_answer = None

            async for event in graph.astream_events(init_state, config=config, version="v2"):
                event_name = event.get("event", "")

                if event_name == "on_parser_stream":
                    chunk = event.get("data", {}).get("chunk", {})

                    if isinstance(chunk, dict):
                        current_answer = chunk.get("answer", "")

                        if isinstance(current_answer, str) and current_answer:
                            if current_answer.startswith(previous_answer):
                                delta = current_answer[len(previous_answer):]
                            else:
                                delta = current_answer

                            previous_answer = current_answer

                            if delta:
                                yield {
                                    "type": "token",
                                    "content": delta,
                                }

                if event_name == "on_chain_end" and event.get("name") == "generate_answer":
                    node_output = event.get("data", {}).get("output", {})
                    if isinstance(node_output, dict):
                        final_answer = node_output.get("final_answer")

            if not isinstance(final_answer, dict):
                final_answer = {
                    "answer": previous_answer,
                    "confidence": 0.0,
                    "intent": "unknown",
                }

            yield {
                "type": "final",
                "final_answer": final_answer,
            }

            

if __name__ == "__main__":
    pass