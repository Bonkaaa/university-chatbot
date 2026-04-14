import chainlit as cl

from src.agent import RAGAgent
from src.config import CONVERSATION_DB_DIR, RAW_DOCS_DIR, MODEL_NAME, EMBED_MODEL_NAME

agent = RAGAgent(
    conversation_db_path=CONVERSATION_DB_DIR / "conversations_db.json",
    path_to_docs=RAW_DOCS_DIR,
    embed_model=EMBED_MODEL_NAME,
    main_model=MODEL_NAME
)

@cl.on_chat_start
async def start():
    await cl.Message(
        content="👋 Xin chào! Tôi là chatbot của Đại học Bách khoa Hà Nội. Bạn cần giúp gì hôm nay?"
    ).send()

@cl.on_message
async def handle_message(message: cl.Message):
    user_query = message.content
    response = agent.chat(user_query)

    await cl.Message(content=response["final_answer"]["answer"]).send()

# $env:PYTHONPATH = "C:\university_chatbot"

