import sqlite3
import uuid
import jwt
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime

import chainlit as cl
from dotenv import load_dotenv
from chainlit.config import config as chainlit_config
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from fastapi import Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage

from src.agent import RAGAgent
from src.app.core.security import hash_password, verify_password
from src.app.core import LocalPublicStorageClient
from src.app.models.document_metadata import DocumentMetadata
from src.app.models.document_chunk import DocumentChunk
from src.app.models.user import User
# from src.app.models.user import User
# from src.app.models.conversation import Conversation
# from src.app.models.message import Message
# from src.app.models.session import Session
from src.app.crud.conversation_crud import create_conversation, list_conversations_for_user, get_conversation_by_id, get_number_of_conversations, get_total_conversations_today
from src.app.crud.message_crud import create_message, list_assistant_messages, get_average_message_per_conversation, get_average_response_time, get_messages_by_hour_today, get_total_messages_today
from src.app.crud.user_crud import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
    get_number_of_users,
    get_number_of_active_users,
    list_users,
    deactivate_user,
    get_total_users_today
)
from src.app.crud.document_metadata_crud import (
    create_document_metadata,
    get_number_of_documents,
    list_document_metadata,
    get_document_metadata_by_id,
    get_total_documents_uploaded_today
)
from src.app.db import Base, SessionLocal, engine
from src.config import (
    CONVERSATION_DB_DIR,
    EMBED_MODEL_NAME,
    MODEL_NAME,
    RAW_DOCS_DIR,
    USER_CHAT_HISTORY_DATA,
)
from src.ui import (
    build_error_html,
    build_change_password_html,
    validate_register_input,
    build_profile_html,
    build_register_html,
    build_admin_upload_html,
    build_admin_dashboard_html,
    build_react_page_html,
)
from src.rag_core.utils import setup_logger

logger = setup_logger("main.log", "main")
load_dotenv()


# -----------------------------
# 0) Init backend DB
# -----------------------------
Base.metadata.create_all(bind=engine)

# Ensure there's an admin account for testing and management purposes
@cl.on_app_startup
async def ensure_admin_account():
    logger.info("Startup hook ensure_admin_account triggered.")
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "").strip()
    admin_display_name = os.getenv("ADMIN_DISPLAY_NAME", "Admin").strip()

    if not admin_email or not admin_password:
        logger.warning(
            "Skipping admin creation: missing ADMIN_EMAIL or ADMIN_PASSWORD. "
            "ADMIN_EMAIL present=%s, ADMIN_PASSWORD present=%s",
            bool(admin_email),
            bool(admin_password),
        )
        return
    
    db: Session = SessionLocal()
    try:
        existing = get_user_by_email(db, admin_email)
        if existing:
            logger.info(f"Admin account with email {admin_email} already exists. Skipping creation.")
            return
        create_user(
            db=db, 
            email=admin_email, 
            password_hash=hash_password(admin_password), 
            display_name=admin_display_name, 
            role="admin"
        )
        logger.info(f"Admin account created with email: {admin_email}")
    except Exception:
        logger.exception("Failed during ensure_admin_account.")
        raise
    finally:
        db.close()

# -----------------------------
# 1) Init Chainlit history DB (for sidebar thread history)
# -----------------------------
Path(USER_CHAT_HISTORY_DATA).mkdir(parents=True, exist_ok=True)
chainlit_history_db = Path(USER_CHAT_HISTORY_DATA) / "chat_history.db"


def _init_chainlit_history_schema(db_file: Path) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS users (
    "id" UUID PRIMARY KEY,
    "identifier" TEXT NOT NULL UNIQUE,
    "metadata" JSONB NOT NULL,
    "createdAt" TEXT
    );

    CREATE TABLE IF NOT EXISTS threads (
        "id" UUID PRIMARY KEY,
        "createdAt" TEXT,
        "name" TEXT,
        "userId" UUID,
        "userIdentifier" TEXT,
        "tags" TEXT[],
        "metadata" JSONB,
        FOREIGN KEY ("userId") REFERENCES users("id") ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS steps (
        "id" UUID PRIMARY KEY,
        "name" TEXT NOT NULL,
        "type" TEXT NOT NULL,
        "threadId" UUID NOT NULL,
        "parentId" UUID,
        "streaming" BOOLEAN NOT NULL,
        "waitForAnswer" BOOLEAN,
        "isError" BOOLEAN,
        "metadata" JSONB,
        "tags" TEXT[],
        "input" TEXT,
        "output" TEXT,
        "createdAt" TEXT,
        "command" TEXT,
        "start" TEXT,
        "end" TEXT,
        "generation" JSONB,
        "showInput" TEXT,
        "language" TEXT,
        "indent" INT,
        "defaultOpen" BOOLEAN,
        "modes" JSONB,
        "autoCollapse" BOOLEAN,
        FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS elements (
        "id" UUID PRIMARY KEY,
        "threadId" UUID,
        "type" TEXT,
        "url" TEXT,
        "chainlitKey" TEXT,
        "name" TEXT NOT NULL,
        "display" TEXT,
        "objectKey" TEXT,
        "size" TEXT,
        "page" INT,
        "language" TEXT,
        "forId" UUID,
        "mime" TEXT,
        "props" JSONB,
        FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS feedbacks (
        "id" UUID PRIMARY KEY,
        "forId" UUID NOT NULL,
        "threadId" UUID NOT NULL,
        "value" INT NOT NULL,
        "comment" TEXT,
        FOREIGN KEY ("threadId") REFERENCES threads("id") ON DELETE CASCADE
    );
    """
    with sqlite3.connect(db_file) as conn:
        conn.executescript(ddl)
        conn.commit()


_init_chainlit_history_schema(chainlit_history_db)


@cl.data_layer
def get_data_layer():
    return SQLAlchemyDataLayer(conninfo=f"sqlite+aiosqlite:///{chainlit_history_db.as_posix()}", storage_provider=LocalPublicStorageClient())

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
        logger.error("jwt verify failed:", exc_info=True)
        return None

def _current_user_info_from_cookies(request: Request) -> tuple[str, str] | tuple[None, None]:
    token = request.cookies.get("token") or request.cookies.get("access_token")
    if not token:
        logger.warning("No token found in cookies")
        return None, None
    
    try:
        token = unquote(token)
    except Exception:
        pass

    try: 
        decoded_token = _decode_and_verify_jwt(token)
        metadata = decoded_token.get("metadata", {}) or {}
        user_id = metadata.get("user_id")
        email = metadata.get("email") or decoded_token.get("sub")

        normalized_email = email.strip().lower() if isinstance(email, str) and email.strip() else None
        normalized_user_id = user_id if isinstance(user_id, (str, int)) else None

        if normalized_user_id is None and isinstance(decoded_token.get("sub"), str) and decoded_token.get("sub").isdigit():
            normalized_user_id = int(decoded_token.get("sub"))

        if normalized_user_id is None and normalized_email is None:
            logger.warning("Invalid token payload. email=%s, user_id=%s", email, user_id)
            return None, None
        return normalized_user_id, normalized_email
    except Exception as e:
        logger.error("Error occurred while decoding JWT token: %s", repr(e))
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
    
def _current_user_role() -> str | None:
    user_obj = cl.user_session.get("user")
    if not user_obj:
        return None

    metadata = getattr(user_obj, "metadata", {}) or {}
    role = metadata.get("role")
    if isinstance(role, str):
        return role.strip().lower()
    return None


def _display_name() -> str:
    user_obj = cl.user_session.get("user")
    if not user_obj:
        return "Bạn"
    metadata = getattr(user_obj, "metadata", {}) or {}
    return metadata.get("display_name") or metadata.get("email") or "Bạn"


def _thread_id() -> str:
    if cl.context.session.thread_id:
        return str(cl.context.session.thread_id)

    thread_id = None

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
    final_text = ""
    final_answer = None

    async with cl.Step(name="Chatbot", type="assistant_message") as step:
        step.output = ""
        
        async for event in agent.astream_chat(user_text, thread_id):
            if event.get("type") == "token":
                token = event.get("content", "")
                if token:
                    final_text += token
                    await step.stream_token(token)
            elif event.get("type") == "final":
                final_answer = event.get("final_answer")

        if not final_text and isinstance(final_answer, dict):
            final_text = final_answer.get("answer", "") or ""
        if not final_text:
            final_text = "Xin lỗi, tôi chưa thể tạo câu trả lời lúc này."

        step.output = final_text

    return final_text

# -----------------------------
# 4) Register, authentication, profile, and change password routes and auth callback
# -----------------------------

## Register routes

@cl.server.app.get("/api/me")
async def get_me(request: Request):
    user_id, email = _current_user_info_from_cookies(request)
    if not user_id and not email:
        return JSONResponse(content={"role": None})

    db: Session = SessionLocal()
    try:
        user = get_user_by_id(db, user_id) if user_id else get_user_by_email(db, email.strip().lower())
        return JSONResponse(content={"role": user.role if user else None})
    finally:
        db.close()

@cl.server.app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return HTMLResponse(content=build_react_page_html("Đăng ký", "register"))


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
            return JSONResponse(
                content={"status": "error", "message": validation_error},
                status_code=400,
            )

        if get_user_by_email(db, normalized_email):
            return JSONResponse(
                content={"status": "error", "message": "Email đã tồn tại. Vui lòng dùng email khác."},
                status_code=400,
            )

        create_user(
            db=db,
            email=normalized_email,
            password_hash=hash_password(password),
            display_name=display_name.strip(),
        )
        return JSONResponse(content={"status": "success", "message": "Đăng ký thành công. Hãy quay lại trang đăng nhập."})
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
        if not user_obj.is_active:
            return None
        if not verify_password(password, user_obj.password_hash):
            return None

        return cl.User(
            identifier=str(user_obj.id),
            metadata={
                "user_id": user_obj.id,
                "email": user_obj.email,
                "display_name": user_obj.display_name or user_obj.email,
                "role": user_obj.role,
            },
        )
    finally:
        db.close()


## Profile routes
@cl.server.app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    db: Session = SessionLocal()
    try:
        user = _resolve_current_user(request, db)
        if not user:
            return RedirectResponse(url="/")
    finally:
        db.close()
    return HTMLResponse(content=build_react_page_html("Hồ sơ", "profile"))

@cl.server.app.post("/profile")
async def profile_update(email: str = Form(...), display_name: str = Form(...)):
    db: Session = SessionLocal()
    try:
        u = get_user_by_email(db, email.strip().lower())
        if not u:
            return JSONResponse(content={"status": "error", "message": "Không tìm thấy tài khoản."})
            
        new_name = display_name.strip()
        if not new_name:
            return JSONResponse(content={"status": "error", "message": "Tên hiển thị không được để trống."})

        # Cập nhật DB
        update_user(db, u, display_name=new_name)
        db.commit() # Nhớ commit nếu update_user của bạn chưa làm việc này

        return JSONResponse(content={"status": "success", "message": "Cập nhật tên hiển thị thành công."})
    finally:
        db.close()


# Change password routes
@cl.server.app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request):
    db: Session = SessionLocal()
    try:
        user = _resolve_current_user(request, db)
        if not user:
            return RedirectResponse(url="/")
    finally:
        db.close()
    return HTMLResponse(content=build_react_page_html("Đổi mật khẩu", "change-password"))


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
    except Exception:
        return JSONResponse(content={"status": "error", "message": "Có lỗi xảy ra, vui lòng thử lại."}, status_code=500)
    finally:
        db.close()


def _resolve_current_user(request: Request, db: Session) -> User | None:
    user_id, email = _current_user_info_from_cookies(request)
    if user_id is None and not email:
        return None
    if user_id is not None:
        try:
            by_id = get_user_by_id(db, int(user_id))
            if by_id and by_id.is_active:
                return by_id
        except (TypeError, ValueError):
            pass
    if email:
        user = get_user_by_email(db, email.strip().lower())
        if user and user.is_active:
            return user
    return None


def _require_admin_user(request: Request, db: Session) -> User | None:
    user = _resolve_current_user(request, db)
    if not user or user.role != "admin":
        return None
    return user


@cl.server.app.get("/api/profile")
async def get_profile_api(request: Request):
    db: Session = SessionLocal()
    try:
        user = _resolve_current_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Vui lòng đăng nhập lại."}, status_code=401)
        return JSONResponse(
            content={
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name or "",
                "role": user.role,
                "is_active": user.is_active,
            }
        )
    finally:
        db.close()


@cl.server.app.patch("/api/profile")
async def patch_profile_api(request: Request):
    payload = await request.json()
    new_name = (payload.get("display_name") or "").strip()
    if not new_name:
        return JSONResponse(content={"message": "Tên hiển thị không được để trống."}, status_code=400)

    db: Session = SessionLocal()
    try:
        user = _resolve_current_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Vui lòng đăng nhập lại."}, status_code=401)
        update_user(db, user, display_name=new_name)
        return JSONResponse(content={"status": "success", "message": "Cập nhật tên hiển thị thành công."})
    finally:
        db.close()


@cl.server.app.post("/api/change-password")
async def change_password_api(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
):
    db: Session = SessionLocal()
    try:
        user = _resolve_current_user(request, db)
        if not user:
            return JSONResponse(content={"status": "error", "message": "Vui lòng đăng nhập lại."}, status_code=401)
        if not verify_password(current_password, user.password_hash):
            return JSONResponse(content={"status": "error", "message": "Mật khẩu hiện tại không chính xác."})
        _, validation_error = validate_register_input(user.email, new_password, user.display_name or "User")
        if validation_error:
            return JSONResponse(content={"status": "error", "message": validation_error})
        user.password_hash = hash_password(new_password)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Đổi mật khẩu thành công!"})
    finally:
        db.close()

# @cl.server.app.get("/")
# async def root_redirect(Request: Request):
#     user_id, email = _current_user_info_from_cookies(Request)
#     if not user_id and not email:
#         return RedirectResponse(url="/login")
    
#     db: Session = SessionLocal()
#     try:
#         user = get_user_by_id(db, user_id) if user_id else get_user_by_email(db, email.strip().lower())

#         if user and user.role == "admin":
#             return RedirectResponse(url="/admin")
#     finally:
#         db.close()
    
#     return RedirectResponse(url="/")

@cl.server.app.middleware("http")
async def admin_root_redirect(request: Request, call_next):
    if request.url.path == "/":
        if request.query_params.get("chat") == "1":
            return await call_next(request)


        user_id, email = _current_user_info_from_cookies(request)
        if user_id or email:
            db: Session = SessionLocal()
            try:
                user = get_user_by_id(db, user_id) if user_id else get_user_by_email(db, email.strip().lower())
                if user and user.role == "admin":
                    return RedirectResponse(url="/admin")
            finally:
                db.close()
    return await call_next(request)


## Prioritize the /register, /profile, and /change-password routes so they are matched before the default Chainlit auth routes
def _prioritize_register_route() -> None:
    routes = cl.server.app.router.routes

    # Các đường dẫn cần ưu tiên để tránh catch-all của Chainlit trả về trang chính
    promote_paths = {
        "/register",
        "/profile",
        "/change-password",
        "/admin",
        "/admin/upload",
        "/admin/users",
        "/api/me",
        "/api/profile",
        "/api/change-password",
        "/api/admin/overview",
        "/api/admin/dashboard-stats",
        "/api/admin/documents",
        "/api/admin/documents/{doc_id}",
        "/api/admin/users",
        "/api/admin/users/{user_id}/active",
    }

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


# -----------------------------
# 5) Admin routes (for uploading documents and managing users)
# -----------------------------

## Admin dashboard route
@cl.server.app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return RedirectResponse(url="/")
    finally:
        db.close()
    return HTMLResponse(content=build_react_page_html("Admin Dashboard", "admin-dashboard"))

        
## Admin upload document route
@cl.server.app.get("/admin/upload", response_class=HTMLResponse)
async def admin_upload_page(request: Request):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return RedirectResponse(url="/")
    finally:
        db.close()
    return HTMLResponse(content=build_react_page_html("Quản lý tài liệu", "admin-documents"))


@cl.server.app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return RedirectResponse(url="/")
    finally:
        db.close()
    return HTMLResponse(content=build_react_page_html("Quản lý người dùng", "admin-users"))

@cl.server.app.post("/admin/upload", response_class=HTMLResponse)
async def admin_upload_document(request: Request, file: UploadFile = File(...)):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)
        
        filename = (file.filename or "uploaded_file").strip().replace(" ", "_")
        if not filename:
            return JSONResponse(content={"message": "Tên file không hợp lệ."}, status_code=400)
        
        ext = os.path.splitext(filename)[1].lower()

        if ext not in [".pdf", ".md", ".docx"]:
            return JSONResponse(content={"message": "Định dạng file không được hỗ trợ. Chỉ nhận .pdf, .md, .docx."}, status_code=400)
        
        os.makedirs(RAW_DOCS_DIR, exist_ok=True)
        # Generate a single UUID to use for both the saved filename and the DB record
        doc_uuid = uuid.uuid4()
        save_path = os.path.join(RAW_DOCS_DIR, f"{doc_uuid}_{filename}")

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # Save metadata to DB (use same UUID so loader can link chunks back to this row)
        create_document_metadata(
            db=db,
            title=os.path.splitext(filename)[0],
            file_name=filename,
            file_type=ext,
            file_size=len(content),
            uploaded_by=user.id,
            id=doc_uuid,
        )

        # Run document loaders to process the newly uploaded document and add to vector store
        subprocess.run(["python", "-m", "src.rag_core.components.data_ingestion.document_loader"], check=True)

        # Re-sync the agent's index to include the new document
        subprocess.run(["python", "-m", "src.rag_core.components.retriever"], check=True)


        return JSONResponse(content={"status": "success", "message": "Tải lên thành công và tài liệu đã được xử lý."})
    except Exception as e:
        logger.error("Error during file upload: %s", repr(e))
        return JSONResponse(content={"message": "Có lỗi xảy ra trong quá trình tải lên. Vui lòng thử lại."}, status_code=500)
    finally:
        db.close()


@cl.server.app.get("/api/admin/overview")
async def admin_overview_api(request: Request):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)
        total_users = get_number_of_users(db)
        total_docs = get_number_of_documents(db, include_deleted=False)
        active_users = get_number_of_active_users(db)
        return JSONResponse(content={"total_users": total_users, "active_users": active_users, "total_documents": total_docs})
    finally:
        db.close()

@cl.server.app.get("/api/admin/dashboard-stats")
async def admin_dashboard_stats_api(request: Request):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return JSONResponse(
                content={"message": "Bạn không có quyền truy cập trang này."},
                status_code=403,
            )
 
        # ── Tổng quan (all-time) ──────────────────────────────
        total_users        = get_number_of_users(db)
        active_users       = get_number_of_active_users(db)
        total_documents    = get_number_of_documents(db, include_deleted=False)
        total_conversations = get_number_of_conversations(db)
 
        # ── Hôm nay ──────────────────────────────────────────
        new_users_today    = get_total_users_today(db)
        messages_today     = get_total_messages_today(db)
        convs_today        = get_total_conversations_today(db)
        docs_today         = get_total_documents_uploaded_today(db)
 
        # ── Hiệu suất ─────────────────────────────────────────
        avg_response_ms    = get_average_response_time(db)          # milliseconds, float
        avg_msg_per_conv   = get_average_message_per_conversation(db)  # float
 
        # ── Live chart: messages/user theo giờ hôm nay ────────
        # get_messages_by_hour_today trả về list[{"hour": int, "count": int}]
        # Đảm bảo đủ 24 giờ (giờ không có message sẽ là 0)
        raw_hours = get_messages_by_hour_today(db)
        hour_map  = {item["hour"]: item["count"] for item in raw_hours}
        messages_by_hour = [
            {"hour": h, "count": hour_map.get(h, 0)}
            for h in range(24)
        ]
 
        return JSONResponse(content={
            # all-time
            "total_users":         total_users,
            "active_users":        active_users,
            "total_documents":     total_documents,
            "total_conversations": total_conversations,
            # today
            "new_users_today":     new_users_today,
            "messages_today":      messages_today,
            "conversations_today": convs_today,
            "docs_today":          docs_today,
            # performance
            "avg_response_ms":     round(avg_response_ms or 0, 1),
            "avg_msg_per_conv":    round(avg_msg_per_conv or 0, 1),
            # chart
            "messages_by_hour":    messages_by_hour,
        })
    finally:
        db.close()

@cl.server.app.get("/api/admin/documents")
async def list_documents_api(request: Request, query: str = "", include_deleted: int = 0):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)

        rows = list_document_metadata(db, query=query, include_deleted=(include_deleted == 1))
        return JSONResponse(
            content=[
                {
                    "id": str(r.id),
                    "title": r.title,
                    "file_name": r.file_name,
                    "file_type": r.file_type,
                    "file_size": r.file_size,
                    "status": r.status,
                    "is_deleted": r.is_deleted,
                    "uploaded_by": r.uploaded_by,
                    "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
                }
                for r in rows
            ]
        )
    finally:
        db.close()


@cl.server.app.get("/api/admin/documents/{doc_id}")
async def document_detail_api(request: Request, doc_id: str):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)
        row = get_document_metadata_by_id(db, doc_id)
        if not row:
            return JSONResponse(content={"message": "Không tìm thấy tài liệu."}, status_code=404)
        chunk_count = db.query(DocumentChunk).filter(DocumentChunk.document_id == row.id).count()
        uploader = get_user_by_id(db, row.uploaded_by)
        return JSONResponse(
            content={
                "id": str(row.id),
                "title": row.title,
                "file_name": row.file_name,
                "file_type": row.file_type,
                "file_size": row.file_size,
                "status": row.status,
                "is_deleted": row.is_deleted,
                "uploaded_by": row.uploaded_by,
                "uploader_name": uploader.display_name if uploader else None,
                "created_at": row.uploaded_at.isoformat() if row.uploaded_at else None,
                "chunk_count": chunk_count,
            }
        )
    finally:
        db.close()


@cl.server.app.delete("/api/admin/documents/{doc_id}")
async def delete_document_api(request: Request, doc_id: str):
    db: Session = SessionLocal()
    try:
        user = _require_admin_user(request, db)
        if not user:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)
        row = get_document_metadata_by_id(db, doc_id)
        if not row:
            return JSONResponse(content={"message": "Không tìm thấy tài liệu."}, status_code=404)
        row.is_deleted = 1
        row.status = "deleted"
        db.query(DocumentChunk).filter(DocumentChunk.document_id == row.id).delete(synchronize_session=False)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Đã xóa tài liệu."})
    finally:
        db.close()


@cl.server.app.get("/api/admin/users")
async def list_users_api(request: Request, query: str = "", role: str = "", active: str = "all"):
    db: Session = SessionLocal()
    try:
        admin = _require_admin_user(request, db)
        if not admin:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)
        users = list_users(db, query=query, role=role, active=active)
        return JSONResponse(
            content=[
                {
                    "id": u.id,
                    "email": u.email,
                    "display_name": u.display_name,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ]
        )
    finally:
        db.close()


@cl.server.app.patch("/api/admin/users/{user_id}/active")
async def toggle_user_active_api(request: Request, user_id: int):
    payload = await request.json()
    is_active = bool(payload.get("is_active"))

    db: Session = SessionLocal()
    try:
        admin = _require_admin_user(request, db)
        if not admin:
            return JSONResponse(content={"message": "Bạn không có quyền truy cập trang này."}, status_code=403)
        target = get_user_by_id(db, user_id)
        if not target:
            return JSONResponse(content={"message": "Không tìm thấy người dùng."}, status_code=404)
        if target.id == admin.id and not is_active:
            return JSONResponse(content={"message": "Không thể tự vô hiệu hóa tài khoản admin hiện tại."}, status_code=400)
        update_user(db, target, is_active=is_active)
        return JSONResponse(content={"status": "success", "message": "Cập nhật trạng thái người dùng thành công."})
    finally:
        db.close()




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
    display_name = _display_name()

    # Ensure message has proper author set for Chainlit tracking
    if not message.author:
        message.author = display_name

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

    # Set up time measurement for assistant response time
    start_time = time.perf_counter()

    assistant_text = await _generate_assistant_answer(message.content, thread_id)

    # Measure response time and update the last assistant message in DB
    end_time = time.perf_counter()
    response_time = int((end_time - start_time) * 1000)  # Convert to milliseconds

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
                response_time=response_time
            )
    finally:
        db.close()


@cl.action_callback("starter_action")
async def on_starter_action(action: cl.Action):
    await action.remove()
    query_text = action.payload.get("value", "")
    if not query_text:
        return

    await cl.Message(content=query_text, author=_display_name(), type="user_message").send()
    await on_message(cl.Message(content=query_text))


@cl.on_chat_resume
async def on_chat_resume(thread: dict):
    user_id = _current_user_id()
    if not user_id:
        return

    thread_id = str(thread.get("id", ""))
    if not thread_id:
        return

    db: Session = SessionLocal()
    try:
        conversation_id = _get_or_create_conversation_for_thread(db, user_id, thread_id)
        
        cl.user_session.set("thread_id", thread_id)
        cl.user_session.set("conversation_id", conversation_id)
    finally:
        db.close()
    
    # # Put context into agent
    # steps = thread.get("steps", [])

    # messages = []

    # for step in steps:
    #     content = step.get("output", "")

    #     if not content:
    #         continue

    #     step_type = step.get("type", "")
        
    #     if step_type == "user_message":
    #         messages.append(HumanMessage(content=content))
    #     elif step_type == "assistant_message":
    #         messages.append(AIMessage(content=content))

    # cl.user_session.set("messages", messages)


# Run after all app routes are declared so promoted paths actually exist.
_prioritize_register_route()
