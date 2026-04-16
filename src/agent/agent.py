from langgraph.graph import add_messages
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, RemoveMessage
from langchain_core.documents import Document

from typing_extensions import TypedDict, Annotated, Any, List, Dict
import json

from ..rag_core import setup_logger
from ..rag_core import UniversityDocumentLoader, create_splitter, create_retriever, generate_answer_agent
from ..config import MAX_CONVERSATION_HISTORY

class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]

    query: str
    queries: List[str]
    path_to_docs: str

    chunk_size: int
    chunk_overlap: int

    embed_model: str
    main_model: str

    retriever: Any

    top_k_docs: int
    top_k_queries: int

    raw_docs: List[Document]
    split_docs: List[Document]
    retrieved_docs: List[Document]

    final_answer: Dict[str, Any]

logger = setup_logger("agent.log", "agent")

def load_docs_node(state: State) -> State:
    try:
        loader = UniversityDocumentLoader(state["path_to_docs"])
        docs = loader.load_all_documents()
        logger.info(f"Loaded {len(docs)} documents from {state['path_to_docs']}")
    #     return {
    #         "raw_docs": docs,
    #     }
    # except Exception as e:
    #     logger.error(f"Error occurred while loading documents: {e}")
    #     return {
    #         "raw_docs": [],
    #     }
        return {
            "split_docs": docs, 
        }
    except Exception as e:
        logger.error(f"Error occurred while loading documents: {e}")
        return {
            "split_docs": [],
        }
    

def vector_store_retriever_node(state: State) -> State:
    try: 
        retriever = create_retriever(
        docs=state["split_docs"],
        embed_model=state["embed_model"],
        k=state["top_k_docs"],
        )
        logger.info(f"Created retriever with top_k={state['top_k_docs']} using embed_model={state['embed_model']}")

        retrieved_docs = retriever.invoke(state["query"])
        logger.info(f"Retrieved {len(retrieved_docs)} documents using retriever")
        return {
            "retrieved_docs": retrieved_docs,
        }
    except Exception as e:
        logger.error(f"Error occurred while retrieving with retriever: {e}")
        return {
            "retrieved_docs": [],
        }

async def generate_answer_node(state: State) -> State:
    user_message = f"""
    Question from user: {state['query']}
    Retrieved documents: {state['retrieved_docs']}
    """
    # Process the message state
    messages = state.get("messages", [])
    delete_command = []

    if len(messages) > MAX_CONVERSATION_HISTORY:
        old_messages = messages[:-MAX_CONVERSATION_HISTORY]
        for msg in old_messages:
            delete_command.append(RemoveMessage(id=msg.id))

    human_message = HumanMessage(content=user_message)

    new_messages = [human_message]

    # If no documents were retrieved, we can skip calling the answer generation agent and return a default response
    if not state["retrieved_docs"] or len(state["retrieved_docs"]) == 0:
        ai_message = AIMessage(content="Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn.")
        new_messages.append(ai_message)
        return {
            "final_answer": {
                "answer": "Xin lỗi, tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn.",
                "confidence": 0.0,
                "intent": "unknown",
            },
            "messages": delete_command + new_messages,
        }

    try:
        answer_agent = generate_answer_agent(
            model_name=state["main_model"],
            temperature=0.2,
        )

        agent_input = {
            "question": state["query"],
            "retrieved_docs": state["retrieved_docs"],
        }

        response_dict = {
            "answer": "",
            "confidence": 0.0,
            "intent": "unknown",
            "sources": [doc.metadata.get("source", "unknown") for doc in state["retrieved_docs"]],
        }

        async for chunk in answer_agent.astream(agent_input):
            if not isinstance(chunk, dict):
                continue

            answer = chunk.get("answer")
            confidence = chunk.get("confidence")
            intent = chunk.get("intent")

            if isinstance(answer, str):
                response_dict["answer"] = answer
            if isinstance(confidence, (float, int)):
                response_dict["confidence"] = float(confidence)
            if isinstance(intent, str) and intent.strip():
                response_dict["intent"] = intent

        logger.info(f"Answer: {response_dict}")

        ai_message = AIMessage(content=response_dict["answer"])

        new_messages.append(ai_message)

        return {
            "final_answer": response_dict,
            "messages": delete_command + new_messages,
        }
    except Exception as e:
        logger.error(f"Error occurred while generating answer: {e}")
        return {
            "final_answer": {
                "answer": "Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời.",
                "confidence": 0.0,
                "follow_up_question": [],
                "intent": "unknown",
            },
            "messages": delete_command + new_messages,
        }



