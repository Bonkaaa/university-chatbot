from langgraph.graph import add_messages
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langchain_core.documents import Document

from typing_extensions import TypedDict, Annotated, Any, List
import json

from ..rag_core import setup_logger
from ..rag_core import UniversityDocumentLoader, create_splitter, create_retriever, generate_answer_agent, retrieve_with_rrf, get_multi_query_agent

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
    retrieved_docs: str

    final_answer: str

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

# def split_docs_node(state: State) -> State:
#     try: 
#         splitter = create_splitter(chunk_size=state["chunk_size"], chunk_overlap=state["chunk_overlap"])
#         split_docs = splitter.split_documents(state["raw_docs"])
#         logger.info(f"Split documents into {len(split_docs)} chunks")
#         return {
#             "split_docs": split_docs,
#         }
#     except Exception as e:
#         logger.error(f"Error occurred while splitting documents: {e}")
#         return {
#             "split_docs": [],
#         }
    

def vector_store_retriever_node(state: State) -> State:
    try: 
        retriever = create_retriever(
            docs=state["split_docs"],
            embed_model=state["embed_model"],
            k=state["top_k_docs"],
        )
        logger.info(f"Created retriever with top_k={state['top_k_docs']} using embed_model={state['embed_model']}")
        return {
            "retriever": retriever,
        }
    except Exception as e:
        logger.error(f"Error occurred while creating retriever: {e}")
        return {
            "retriever": None,
        }
    

# def get_llm_node(state: State) -> Any:
#     try: 
#         llm = get_llm(state["main_model"])
#         logger.info(f"Created LLM with model={state['main_model']}")
#         return {
#             "llm": llm,
#         }
#     except Exception as e:
#         logger.error(f"Error occurred while creating LLM: {e}")
#         return {
#             "llm": None,
#         }

def multi_query_node(state: State) -> State:
    multi_query_agent = get_multi_query_agent(state["main_model"])

    user_message = f"""
    Message for Multi-Query Agent:
    Question: {state['query']}
    Top K Retrieved Docs: {state['top_k_queries']}
    """

    human_message = HumanMessage(content=user_message)

    new_messages = [human_message]

    agent_input = {
        "question": state["query"],
        "k_queries": state["top_k_queries"],
    }

    try:
        response = multi_query_agent.invoke(agent_input)
        queries = response.queries
        logger.info(f"Multi-Query Agent generated queries: {queries}")
        

        ai_message = AIMessage(content=json.dumps(
            {
                "queries": queries,
            },
            ensure_ascii=False,
        ))
        new_messages.append(ai_message)

        return {
            "messages": new_messages,
            "queries": queries,
        }
    except Exception as e:
        logger.error(f"Error occurred while invoking Multi-Query Agent: {e}")
        return {
            "messages": new_messages,
            "queries": [],
        }

def retrieve_with_rrf_node(state: State) -> State:
    try:
        retrieved_docs = retrieve_with_rrf(
            queries=state["queries"],
            retriever=state["retriever"],
            top_k=state["top_k_docs"],
        )
        logger.info(f"Retrieved {len(retrieved_docs)} documents using RRF fusion")
        return {
            "retrieved_docs": retrieved_docs,
        }
    except Exception as e:
        logger.error(f"Error occurred while retrieving with RRF fusion: {e}")
        return {
            "retrieved_docs": [],
        }

def generate_answer_node(state: State) -> State:
    try:
        answer_agent = generate_answer_agent(
            model_name=state["main_model"],
            temperature=0.2,
        )

        agent_input = {
            "question": state["query"],
            "retrieved_docs": state["retrieved_docs"],
        }

        response = answer_agent.invoke(agent_input)
        logger.info(f"Answer: {response}")
        return {
            "final_answer": response,
        }
    except Exception as e:
        logger.error(f"Error occurred while generating answer: {e}")
        return {
            "final_answer": "",
        }



