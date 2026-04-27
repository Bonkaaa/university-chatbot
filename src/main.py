import sqlite3
import uuid
from html import escape
from pathlib import Path

import chainlit as cl
from chainlit.config import config as chainlit_config
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from src.agent import RAGAgent
from src.app.core.security import hash_password, verify_password
from src.app.crud.conversation_crud import create_conversation, list_conversations_for_user
from src.app.crud.message_crud import create_message
from src.app.crud.user_crud import create_user, get_user_by_email
from src.app.db import Base, SessionLocal, engine
from src.app.models import conversation, message, session, user  # noqa: F401
from src.config import (
    CONVERSATION_DB_DIR,
    EMBED_MODEL_NAME,
    MODEL_NAME,
    RAW_DOCS_DIR,
    USER_CHAT_HISTORY_DATA,
)


# -----------------------------
# 0) Init backend DB
# -----------------------------
Base.metadata.create_all(bind=engine)


# -----------------------------
# 1) Init Chainlit history DB (for sidebar thread history)
# -----------------------------
Path(USER_CHAT_HISTORY_DATA).mkdir(parents=True, exist_ok=True)
chainlit_history_db = Path(USER_CHAT_HISTORY_DATA) / "chat_history.db"


def _init_chainlit_history_schema(db_file: Path) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      identifier TEXT UNIQUE,
      "createdAt" TEXT,
      metadata TEXT
    );

    CREATE TABLE IF NOT EXISTS threads (
      id TEXT PRIMARY KEY,
      "createdAt" TEXT,
      name TEXT,
      "userId" TEXT,
      "userIdentifier" TEXT,
      tags TEXT,
      metadata TEXT
    );

    CREATE TABLE IF NOT EXISTS steps (
      id TEXT PRIMARY KEY,
      name TEXT,
      type TEXT,
      "threadId" TEXT,
      "parentId" TEXT,
      streaming INTEGER,
      "waitForAnswer" INTEGER,
      "isError" INTEGER,
      metadata TEXT,
      tags TEXT,
      input TEXT,
      output TEXT,
      "createdAt" TEXT,
      start TEXT,
      "end" TEXT,
      generation TEXT,
      "showInput" TEXT,
      language TEXT
    );

    CREATE TABLE IF NOT EXISTS elements (
      id TEXT PRIMARY KEY,
      "threadId" TEXT,
      type TEXT,
      "chainlitKey" TEXT,
      url TEXT,
      "objectKey" TEXT,
      name TEXT,
      display TEXT,
      size TEXT,
      language TEXT,
      page INTEGER,
      "forId" TEXT,
      mime TEXT,
      props TEXT,
      "autoPlay" INTEGER,
      "playerConfig" TEXT
    );

    CREATE TABLE IF NOT EXISTS feedbacks (
      id TEXT PRIMARY KEY,
      "forId" TEXT,
      value INTEGER,
      comment TEXT
    );
    """
    with sqlite3.connect(db_file) as conn:
        conn.executescript(ddl)
        conn.commit()


_init_chainlit_history_schema(chainlit_history_db)

cl.data._data_layer = SQLAlchemyDataLayer(
    conninfo=f"sqlite+aiosqlite:///{chainlit_history_db.as_posix()}"
)

# UI customizations
chainlit_config.ui.default_sidebar_state = "open"
if not chainlit_config.ui.custom_css:
    chainlit_config.ui.custom_css = "/public/auth.css"
if not chainlit_config.ui.custom_js:
    chainlit_config.ui.custom_js = "/public/auth.js"


# -----------------------------
# 2) Agent
# -----------------------------
agent = RAGAgent(
    conversation_db_path=CONVERSATION_DB_DIR,
    path_to_docs=RAW_DOCS_DIR,
    embed_model=EMBED_MODEL_NAME,
    main_model=MODEL_NAME,
)


# -----------------------------
# 3) Register page
# -----------------------------
def _build_register_html(message: str = "", kind: str = "info") -> str:
    safe_message = escape(message)
    color_map = {
        "info": "#1849a9",
        "error": "#b42318",
        "success": "#1f8f5f",
    }
    color = color_map.get(kind, "#1849a9")

    notice = ""
    if safe_message:
        notice = f"""
        <div style="margin-bottom:16px;padding:10px 12px;border-radius:8px;background:#f8fafc;color:{color};font-size:14px;">
          {safe_message}
        </div>
        """

    return f"""
    <html>
      <head>
        <title>Đăng ký</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body style="margin:0;font-family:Segoe UI,Arial,sans-serif;background:linear-gradient(160deg,#f0f9ff,#f8fafc 60%,#ecfeff);">
        <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px;">
          <div style="width:100%;max-width:420px;background:#fff;border-radius:14px;box-shadow:0 12px 35px rgba(2,6,23,.12);padding:26px;">
            <h2 style="margin:0 0 8px 0;color:#0f172a;">Đăng ký tài khoản</h2>
            <p style="margin:0 0 18px 0;color:#475467;font-size:14px;">Tạo tài khoản để sử dụng chatbot.</p>
            {notice}
            <form action="/register" method="post">
              <label for="email" style="font-size:13px;color:#344054;">Email</label>
              <input id="email" type="email" name="email" required
                style="width:100%;box-sizing:border-box;padding:11px 12px;margin:6px 0 12px;border:1px solid #d0d5dd;border-radius:8px;" />

              <label for="display_name" style="font-size:13px;color:#344054;">Tên hiển thị</label>
              <input id="display_name" type="text" name="display_name" required
                style="width:100%;box-sizing:border-box;padding:11px 12px;margin:6px 0 12px;border:1px solid #d0d5dd;border-radius:8px;" />

              <label for="password" style="font-size:13px;color:#344054;">Mật khẩu</label>
              <input id="password" type="password" name="password" minlength="6" required
                style="width:100%;box-sizing:border-box;padding:11px 12px;margin:6px 0 14px;border:1px solid #d0d5dd;border-radius:8px;" />

              <button type="submit"
                style="width:100%;padding:11px 12px;background:#0b6bcb;color:#fff;border:none;border-radius:8px;font-weight:600;cursor:pointer;">
                Tạo tài khoản
              </button>
            </form>
            <p style="margin:14px 0 0 0;font-size:14px;color:#475467;">
              Đã có tài khoản? <a href="/" style="color:#0b6bcb;text-decoration:none;font-weight:600;">Quay lại đăng nhập</a>
            </p>
          </div>
        </div>
      </body>
    </html>
    """


@cl.server.app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return HTMLResponse(content=_build_register_html())


@cl.server.app.post("/register")
async def process_register(
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
):
    db: Session = SessionLocal()
    try:
        normalized_email = email.strip().lower()
        if get_user_by_email(db, normalized_email):
            return HTMLResponse(
                content=_build_register_html(
                    "Email đã tồn tại. Vui lòng dùng email khác.",
                    kind="error",
                )
            )

        create_user(
            db=db,
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        return HTMLResponse(
            content=_build_register_html(
                "Đăng ký thành công. Hãy quay lại trang đăng nhập.",
                kind="success",
            )
        )
    finally:
        db.close()


def _prioritize_register_route() -> None:
    routes = cl.server.app.router.routes

    promoted = []
    remaining = []
    for route in routes:
        if getattr(route, "path", None) == "/register":
            promoted.append(route)
        else:
            remaining.append(route)

    if not promoted:
        return

    insert_at = len(remaining)
    for idx, route in enumerate(remaining):
        if getattr(route, "path", None) == "/{full_path:path}":
            insert_at = idx
            break

    cl.server.app.router.routes = remaining[:insert_at] + promoted + remaining[insert_at:]


_prioritize_register_route()


# -----------------------------
# 4) Auth callback
# -----------------------------
@cl.password_auth_callback
async def auth_callback(username: str, password: str):
    db: Session = SessionLocal()
    try:
        user_obj = get_user_by_email(db, username.strip().lower())
        if not user_obj:
            return None
        if not verify_password(password, user_obj.password_hash):
            return None

        return cl.User(
            identifier=str(user_obj.id),
            metadata={
                "user_id": user_obj.id,
                "email": user_obj.email,
                "display_name": user_obj.display_name or user_obj.email,
            },
        )
    finally:
        db.close()


# -----------------------------
# 5) Helpers
# -----------------------------
def _current_user_id() -> int | None:
    user_obj = cl.user_session.get("user")
    if not user_obj:
        return None

    metadata = getattr(user_obj, "metadata", {}) or {}
    candidate = metadata.get("user_id") or getattr(user_obj, "identifier", None)
    if candidate is None:
        return None

    try:
        return int(candidate)
    except (TypeError, ValueError):
        return None


def _display_name() -> str:
    user_obj = cl.user_session.get("user")
    if not user_obj:
        return "Bạn"
    metadata = getattr(user_obj, "metadata", {}) or {}
    return metadata.get("display_name") or metadata.get("email") or "Bạn"


def _thread_id() -> str:
    thread_id = cl.user_session.get("id")
    if not thread_id:
        thread_id = cl.user_session.get("thread_id")
    if not thread_id:
        thread_id = str(uuid.uuid4())
    cl.user_session.set("thread_id", thread_id)
    return str(thread_id)


def _conversation_title_for_thread(thread_id: str) -> str:
    return f"thread:{thread_id}"


def _get_or_create_conversation_for_thread(db: Session, user_id: int, thread_id: str) -> int:
    expected_title = _conversation_title_for_thread(thread_id)
    conversations = list_conversations_for_user(db, user_id)
    for conv in conversations:
        if conv.title == expected_title:
            return conv.id

    conv = create_conversation(db, user_id=user_id, title=expected_title)
    return conv.id


async def _generate_assistant_answer(user_text: str, thread_id: str) -> str:
    streamed_message = cl.Message(content="", author="Chatbot")
    await streamed_message.send()

    final_text = ""
    final_answer = None

    async for event in agent.astream_chat(user_text, thread_id):
        if event.get("type") == "token":
            token = event.get("content", "")
            if token:
                final_text += token
                await streamed_message.stream_token(token)
        elif event.get("type") == "final":
            final_answer = event.get("final_answer")

    if not final_text and isinstance(final_answer, dict):
        final_text = final_answer.get("answer", "") or ""

    if not final_text:
        final_text = "Xin lỗi, tôi chưa thể tạo câu trả lời lúc này."
        streamed_message.content = final_text

    await streamed_message.update()
    return final_text


# -----------------------------
# 6) Chat handlers
# -----------------------------
@cl.on_chat_start
async def on_chat_start():
    user_id = _current_user_id()
    if not user_id:
        await cl.Message(content="Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.", author="Hệ thống").send()
        return

    thread_id = _thread_id()

    db: Session = SessionLocal()
    try:
        conversation_id = _get_or_create_conversation_for_thread(db, user_id, thread_id)
        cl.user_session.set("conversation_id", conversation_id)
    finally:
        db.close()

    starter_actions = [
        cl.Action(
            name="Điều kiện xét tốt nghiệp",
            payload={"value": "Điều kiện để đăng ký và được xét công nhận tốt nghiệp là gì?"},
            label="🎓 Quy chế đào tạo",
        ),
        cl.Action(
            name="Hướng dẫn xin giấy chứng nhận sinh viên tạm thời",
            payload={"value": "Hướng dẫn tôi cách xin giấy chứng nhận sinh viên tạm thời."},
            label="📄 Thủ tục hành chính",
        ),
        cl.Action(
            name="Điều kiện xét học bổng",
            payload={"value": "Điều kiện để được xét học bổng là gì ?"},
            label="🎓 Học bổng",
        ),
    ]

    await cl.Message(
        content=f"👋 Xin chào {_display_name()}! Tôi là trợ lý ảo của đại học Bách khoa Hà Nội, tôi có thể giúp bạn trả lời các câu hỏi liên quan đến trường. Bạn muốn hỏi về điều gì?",
        author="Chatbot",
        actions=starter_actions,
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    user_id = _current_user_id()
    if not user_id:
        await cl.Message(content="Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.", author="Hệ thống").send()
        return

    thread_id = _thread_id()

    db: Session = SessionLocal()
    try:
        conversation_id = cl.user_session.get("conversation_id")
        if not conversation_id:
            conversation_id = _get_or_create_conversation_for_thread(db, user_id, thread_id)
            cl.user_session.set("conversation_id", conversation_id)

        create_message(
            db=db,
            conversation_id=int(conversation_id),
            user_id=user_id,
            role="user",
            content=message.content,
        )
    finally:
        db.close()

    assistant_text = await _generate_assistant_answer(message.content, thread_id)

    db = SessionLocal()
    try:
        conversation_id = cl.user_session.get("conversation_id")
        if conversation_id:
            create_message(
                db=db,
                conversation_id=int(conversation_id),
                user_id=None,
                role="assistant",
                content=assistant_text,
            )
    finally:
        db.close()


@cl.action_callback("starter_action")
async def on_starter_action(action: cl.Action):
    await action.remove()
    query_text = action.payload.get("value", "")
    if not query_text:
        return

    await cl.Message(content=query_text, author="Bạn").send()
    await on_message(cl.Message(content=query_text))


@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    user_id = _current_user_id()
    if not user_id:
        return

    thread_id = str(thread.get("id", ""))
    if not thread_id:
        return

    cl.user_session.set("thread_id", thread_id)

    db: Session = SessionLocal()
    try:
        conversation_id = _get_or_create_conversation_for_thread(db, user_id, thread_id)
        cl.user_session.set("conversation_id", conversation_id)
    finally:
        db.close()
