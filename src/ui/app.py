import chainlit as cl
import uuid
import sqlite3
from pathlib import Path
from fastapi import Request, Form
from fastapi.responses import HTMLResponse
from passlib.context import CryptContext
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer

from src.agent import RAGAgent
from src.config import CONVERSATION_DB_DIR, RAW_DOCS_DIR, MODEL_NAME, EMBED_MODEL_NAME, USER_CHAT_HISTORY_DATA

# ==========================================
# 1. CẤU HÌNH DATABASE & BẢO MẬT USER
# ==========================================
# Khởi tạo công cụ băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Tạo bảng users nếu chưa có
def init_user_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, 
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_user_db()

# Bật tính năng lưu lịch sử chat của Chainlit vào file chainlit_history.db
Path(USER_CHAT_HISTORY_DATA).mkdir(parents=True, exist_ok=True)
cl.data._data_layer = SQLAlchemyDataLayer(conninfo=f"sqlite+aiosqlite:///{USER_CHAT_HISTORY_DATA}/chat_history.db")


# ==========================================
# 2. FASTAPI ROUTES: GIAO DIỆN ĐĂNG KÝ
# ==========================================
@cl.server.app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    html_content = """
    <html>
        <head>
            <title>Đăng ký - Chatbot ĐHBK</title>
            <style>
                body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f9; }
                .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 300px; text-align: center; }
                input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
                button { width: 100%; padding: 10px; background-color: #ba000d; color: white; border: none; border-radius: 4px; cursor: pointer; }
                button:hover { background-color: #9c000a; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="color: #ba000d;">Đăng ký tài khoản</h2>
                <form action="/register" method="post">
                    <input type="text" name="username" placeholder="Mã số sinh viên" required>
                    <input type="password" name="password" placeholder="Mật khẩu" required>
                    <button type="submit">Tạo tài khoản</button>
                </form>
                <p><a href="/">Quay lại trang Đăng nhập</a></p>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@cl.server.app.post("/register")
async def process_register(username: str = Form(...), password: str = Form(...)):
    hashed_pwd = pwd_context.hash(password)
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pwd))
        conn.commit()
    except sqlite3.IntegrityError:
        return HTMLResponse("<h3>Tài khoản đã tồn tại!</h3><a href='/register'>Thử lại</a>")
    finally:
        conn.close()
    
    return HTMLResponse("<h3>Đăng ký thành công!</h3><a href='/'>Bấm vào đây để Đăng nhập</a>")


# ==========================================
# 3. CHAINLIT AUTH: KIỂM TRA ĐĂNG NHẬP
# ==========================================
@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()

    # Kiểm tra xem user có tồn tại và mật khẩu có khớp mã hash không
    if result and pwd_context.verify(password, result[0]):
        return cl.User(identifier=username, metadata={"role": "student"})
    return None


# ==========================================
# 4. LOGIC CHATBOT CHÍNH CỦA BẠN
# ==========================================
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

    starter_actions = [
        cl.Action(name="starter_action", payload={"value": "Điều kiện để đăng ký và được xét công nhận tốt nghiệp là gì?"}, label="🎓 Quy chế đào tạo"),
        cl.Action(name="starter_action", payload={"value": "Hướng dẫn tôi cách xin giấy chứng nhận sinh viên tạm thời."}, label="📄 Thủ tục hành chính"),
        cl.Action(name="starter_action", payload={"value": "Điều kiện để được xét học bổng là gì ?"}, label="🎓 Học bổng")
    ]

    await cl.Message(
        content="👋 Xin chào! Tôi là chatbot của Đại học Bách khoa Hà Nội. Bạn có thể gõ câu hỏi hoặc chọn một trong các gợi ý dưới đây:",
        author="Chatbot",
        actions=starter_actions
    ).send()

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

@cl.on_message
async def handle_message(message: cl.Message):
    await process_user_query(message.content)

@cl.action_callback("starter_action")
async def on_starter_click(action: cl.Action):
    await action.remove()
    query_text = action.payload.get("value")
    await cl.Message(content=query_text, author="User").send()
    await process_user_query(query_text)

# (Tùy chọn) Kích hoạt hàm này khi user bấm vào lịch sử cũ ở sidebar
@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    # Đồng bộ lại thread_id cũ vào RAGAgent của bạn
    cl.user_session.set("thread_id", thread["id"])

    # $env:PYTHONPATH = "C:\university_chatbot"