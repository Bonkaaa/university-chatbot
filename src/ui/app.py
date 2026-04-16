import chainlit as cl
import uuid

from src.agent import RAGAgent
from src.config import CONVERSATION_DB_DIR, RAW_DOCS_DIR, MODEL_NAME, EMBED_MODEL_NAME

agent = RAGAgent(
    conversation_db_path=CONVERSATION_DB_DIR,
    path_to_docs=RAW_DOCS_DIR,
    embed_model=EMBED_MODEL_NAME,
    main_model=MODEL_NAME
)

@cl.on_chat_start
async def start():
    thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)

    # 1. Tạo danh sách các nút gợi ý (Starters)
    # SỬA Ở ĐÂY: Dùng payload thay vì value
    starter_actions = [
        cl.Action(
            name="starter_action", 
            payload={"value": "Điều kiện để đăng ký và được xét công nhận tốt nghiệp là gì?"}, 
            label="🎓 Quy chế đào tạo"
        ),
        cl.Action(
            name="starter_action", 
            payload={"value": "Hướng dẫn tôi cách xin giấy chứng nhận sinh viên tạm thời."}, 
            label="📄 Thủ tục hành chính"
        ),
        cl.Action(
            name="starter_action", 
            payload={"value": "Điều kiện để được xét học bổng là gì ?"}, 
            label="🎓 Học bổng"
        )
    ]

    # 2. Gửi lời chào đi kèm danh sách nút bấm
    await cl.Message(
        content="👋 Xin chào! Tôi là chatbot của Đại học Bách khoa Hà Nội. Bạn có thể gõ câu hỏi hoặc chọn một trong các gợi ý dưới đây:",
        author="Chatbot",
        actions=starter_actions
    ).send()


# SỬA Ở ĐÂY: Bỏ @cl.on_message đi, đây chỉ là một hàm xử lý logic bình thường
async def process_user_query(user_query: str):
    thread_id = cl.user_session.get("thread_id")

    if not thread_id:
        thread_id = str(uuid.uuid4())
        cl.user_session.set("thread_id", thread_id)

    streamed_message = cl.Message(content="")
    await streamed_message.send()

    final_answer = None

    async for event in agent.astream_chat(user_query, thread_id):
        if event.get("type") == "token":
            token = event.get("content", "")
            if token:
                await streamed_message.stream_token(token)

        if event.get("type") == "final":
            final_answer = event.get("final_answer", {})

    if isinstance(final_answer, dict):
        cl.user_session.set("last_final_answer", final_answer)

        if not streamed_message.content and final_answer.get("answer"):
            streamed_message.content = final_answer["answer"]

    await streamed_message.update()


# SỬA Ở ĐÂY: Chỉ giữ lại 1 @cl.on_message để bắt sự kiện người dùng chat
@cl.on_message
async def handle_message(message: cl.Message):
    await process_user_query(message.content)


@cl.action_callback("starter_action")
async def on_starter_click(action: cl.Action):
    # Tùy chọn: Gỡ nút bấm mà người dùng vừa click để UI đỡ rối
    await action.remove()
    
    # SỬA Ở ĐÂY: Lấy giá trị từ payload thay vì action.value
    query_text = action.payload.get("value")
    
    # Hiển thị câu hỏi như thể người dùng vừa gõ vào
    await cl.Message(content=query_text, author="User").send()
    
    # Chạy luồng xử lý RAG
    await process_user_query(query_text)

# $env:PYTHONPATH = "C:\university_chatbot"