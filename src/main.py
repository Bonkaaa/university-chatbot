import sqlite3
import uuid
import jwt
import os
from pathlib import Path
from urllib.parse import unquote

import chainlit as cl
from chainlit.config import config as chainlit_config
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from fastapi import Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session

from src.agent import RAGAgent
from src.app.core.security import hash_password, verify_password
from src.app.core import LocalPublicStorageClient
from src.app.crud.conversation_crud import create_conversation, list_conversations_for_user
from src.app.crud.message_crud import create_message
from src.app.crud.user_crud import create_user, get_user_by_email, get_user_by_id, update_user
from src.app.db import Base, SessionLocal, engine
from src.config import (
    CONVERSATION_DB_DIR,
    EMBED_MODEL_NAME,
    MODEL_NAME,
    RAW_DOCS_DIR,
    USER_CHAT_HISTORY_DATA,
)
from src.ui import build_change_password_html, build_error_html, build_profile_html, build_register_html, validate_register_input


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
    conninfo=f"sqlite+aiosqlite:///{chainlit_history_db.as_posix()}",
    storage_provider=LocalPublicStorageClient(),
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
# 3) Helpers
# -----------------------------
def _decode_and_verify_jwt(token: str) -> dict | None:
    secret = os.getenv("CHAINLIT_AUTH_SECRET")
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except Exception as e:
        print("jwt verify failed:", repr(e))
        return None

def _current_user_info_from_cookies(request: Request) -> tuple[str, str] | tuple[None, None]:
    token = request.cookies.get("token") or request.cookies.get("access_token")
    if not token:
        return None, None
    
    try:
        token = unquote(token)
    except Exception:
        pass

    try: 
        decoded_token = _decode_and_verify_jwt(token)
        print("Decoded JWT token:", decoded_token)
        user_id = decoded_token.get("metadata", {}).get("user_id")
        email = decoded_token.get("metadata", {}).get("email") or decoded_token.get("sub")
        if isinstance(email, str) or isinstance(user_id, (str, int)):
            return user_id, email.strip().lower()
    except Exception as e:
        print("Error occurred while decoding JWT token:", repr(e))
        return None, None

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
# 4) Register, authentication, profile, and change password routes and auth callback
# -----------------------------

## Register routes

@cl.server.app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return HTMLResponse(content=build_register_html())


@cl.server.app.post("/register")
async def process_register(
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
):
    db: Session = SessionLocal()
    try:
        normalized_email, validation_error = validate_register_input(email, password, display_name)
        if validation_error:
            return HTMLResponse(
                content=build_register_html(validation_error, kind="error")
            )

        if get_user_by_email(db, normalized_email):
            return HTMLResponse(
                content=build_register_html(
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
            content=build_register_html(
                "Đăng ký thành công. Hãy quay lại trang đăng nhập.",
                kind="success",
            )
        )
    finally:
        db.close()


## Auth callback for Chainlit to validate user credentials during login
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


## Profile routes
@cl.server.app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    user_id, email = _current_user_info_from_cookies(request)

    if not user_id and not email:
        return HTMLResponse(build_error_html("Không xác định được người dùng. Vui lòng đăng nhập lại."))
    elif user_id:
        db: Session = SessionLocal()
        try:
            u = get_user_by_id(db, user_id)
            if not u:
                return HTMLResponse(build_error_html("Không tìm thấy tài khoản."))
            return HTMLResponse(build_profile_html(u.id, u.email, u.display_name or ""))
        finally:
            db.close()
    else:  # email có nhưng user_id không có -> fallback tìm bằng email
        db: Session = SessionLocal()
        try:
            u = get_user_by_email(db, email.strip().lower())
            if not u:
                return HTMLResponse(build_error_html("Không tìm thấy tài khoản."))
            return HTMLResponse(build_profile_html(u.id, u.email, u.display_name or ""))
        finally:
            db.close()

@cl.server.app.post("/profile")
async def profile_update(email: str = Form(...), display_name: str = Form(...)):
    db: Session = SessionLocal()
    try:
        u = get_user_by_email(db, email.strip().lower())
        if not u:
            return HTMLResponse(build_error_html("Không tìm thấy tài khoản."))
            
        new_name = display_name.strip()
        if not new_name:
            return HTMLResponse(build_error_html("Tên hiển thị không được để trống."))

        # Cập nhật DB
        update_user(db, u, display_name=new_name)
        db.commit() # Nhớ commit nếu update_user của bạn chưa làm việc này

        return JSONResponse(content={"status": "success", "message": "Cập nhật tên hiển thị thành công."})
    finally:
        db.close()


# Change password routes
@cl.server.app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request):
    user_id, email = _current_user_info_from_cookies(request)

    if not user_id and not email:
        return HTMLResponse(build_error_html("Không xác định được người dùng. Vui lòng đăng nhập lại."))
    elif user_id:
        db: Session = SessionLocal()
        try:
            u = get_user_by_id(db, user_id)
            if not u:
                return HTMLResponse(build_error_html("Không tìm thấy tài khoản."))
            return HTMLResponse(build_change_password_html(u.id, u.email))
        finally:
            db.close()
    else:  # email có nhưng user_id không có -> fallback tìm bằng email
        db: Session = SessionLocal()
        try:
            u = get_user_by_email(db, email.strip().lower())
            if not u:
                return HTMLResponse(build_error_html("Không tìm thấy tài khoản."))
            return HTMLResponse(build_change_password_html(u.id, u.email))
        finally:
            db.close()


@cl.server.app.post("/change-password")
async def change_password(
    email: str = Form(...),
    current_password: str = Form(...),
    new_password: str = Form(...),
):
    db: Session = SessionLocal()
    try:
        # Tìm người dùng
        u = get_user_by_email(db, email.strip().lower())
        if not u:
            return JSONResponse(content={"status": "error", "message": "Không tìm thấy tài khoản."})

        # Kiểm tra mật khẩu cũ
        if not verify_password(current_password, u.password_hash):
            return JSONResponse(content={"status": "error", "message": "Mật khẩu hiện tại không chính xác."})

        # Validate mật khẩu mới (dùng lại hàm check format đã có của bạn)
        _, validation_error = validate_register_input(u.email, new_password, u.display_name or "User")
        if validation_error:
            return JSONResponse(content={"status": "error", "message": validation_error})

        # Cập nhật mật khẩu mới
        u.password_hash = hash_password(new_password)
        db.commit()

        return JSONResponse(content={"status": "success", "message": "Đổi mật khẩu thành công!"})
    except Exception as e:
        return HTMLResponse(build_error_html("Có lỗi xảy ra, vui lòng thử lại."))
    finally:
        db.close()


## Prioritize the /register, /profile, and /change-password routes so they are matched before the default Chainlit auth routes
def _prioritize_register_route() -> None:
    routes = cl.server.app.router.routes

    # Các đường dẫn cần ưu tiên để tránh catch-all của Chainlit trả về trang chính
    promote_paths = {"/register", "/profile", "/change-password"}

    promoted = []
    remaining = []
    for route in routes:
        if getattr(route, "path", None) in promote_paths:
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
# 5) Chat handlers
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
            name="starter_action",
            payload={"value": "Điều kiện để đăng ký và được xét công nhận tốt nghiệp là gì?"},
            label="🎓 Quy chế đào tạo",
        ),
        cl.Action(
            name="starter_action",
            payload={"value": "Hướng dẫn tôi cách xin giấy chứng nhận sinh viên tạm thời."},
            label="📄 Thủ tục hành chính",
        ),
        cl.Action(
            name="starter_action",
            payload={"value": "Điều kiện để được xét học bổng là gì ?"},
            label="🎓 Học bổng",
        ),
    ]

    await cl.Message(
        content=f"👋 Xin chào {_display_name()}! Bạn có thể đặt câu hỏi hoặc chọn một gợi ý bên dưới. Lịch sử hội thoại nằm ở thanh bên trái.",
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
