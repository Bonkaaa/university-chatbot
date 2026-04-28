import sqlite3
import re
import uuid
from html import escape
from pathlib import Path
from urllib.parse import quote

import chainlit as cl
from chainlit.config import config as chainlit_config
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from email_validator import EmailNotValidError, validate_email
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


PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS_MSG = (
    "Mật khẩu phải có ít nhất 8 ký tự, gồm chữ hoa, chữ thường và chữ số."
)


def _validate_register_input(email: str, password: str, display_name: str) -> tuple[str, str | None]:
    try:
        normalized_email = validate_email(email.strip(), check_deliverability=False).email.lower()
    except EmailNotValidError:
        return "", "Email không hợp lệ. Vui lòng nhập đúng định dạng email."

    cleaned_display_name = display_name.strip()
    if not cleaned_display_name:
        return "", "Tên hiển thị không được để trống."

    if len(password) < PASSWORD_MIN_LENGTH:
        return "", PASSWORD_REQUIREMENTS_MSG

    has_upper = bool(re.search(r"[A-Z]", password))
    has_lower = bool(re.search(r"[a-z]", password))
    has_digit = bool(re.search(r"\d", password))

    if not (has_upper and has_lower and has_digit):
        return "", PASSWORD_REQUIREMENTS_MSG

    return normalized_email, None


# -----------------------------
# 3) Register pagez
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
        # Trong chuỗi f-string nhỏ này cũng cần gấp đôi ngoặc nhọn cho CSS inline
        notice = f"""
        <div style="margin-bottom:16px;padding:10px 12px;border-radius:8px;background:#f8fafc;color:{color};font-size:14px;">
          {safe_message}
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Đăng ký</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #121212; 
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }}

            .container {{
                width: 100%;
                max-width: 420px;
                padding: 30px;
                box-sizing: border-box;
            }}

            h2 {{
                margin: 0 0 10px 0;
                color: #ffffff;
                font-size: 24px;
                font-weight: 600;
            }}

            p.subtitle {{
                margin: 0 0 24px 0;
                color: #94a3b8;
                font-size: 14px;
            }}

            label {{
                font-size: 13px;
                color: #e2e8f0;
                display: block;
                margin-bottom: 8px;
            }}

            input {{
                width: 100%;
                box-sizing: border-box;
                padding: 12px 14px;
                margin-bottom: 18px;
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 8px;
                color: #fff;
                font-size: 15px;
                outline: none;
                transition: border-color 0.2s;
            }}

            input:focus {{
                border-color: #ff1a66; 
            }}

            .btn-register {{
                width: 100%;
                padding: 12px;
                background-color: #ff1a66;
                color: #fff;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }}

            .btn-register:hover {{
                background-color: #e6005c;
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(255, 26, 102, 0.3);
            }}

            .btn-register:active {{
                transform: translateY(0);
                background-color: #cc0052;
            }}

            .footer {{
                margin-top: 20px;
                font-size: 14px;
                color: #94a3b8;
            }}

            .footer a {{
                color: #3b82f6;
                text-decoration: none;
                font-weight: 600;
            }}

            .footer a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Đăng ký tài khoản</h2>
            <p class="subtitle">Tạo tài khoản để sử dụng chatbot.</p>
            
            {notice}

            <form action="/register" method="post">
                <label for="email">Email</label>
                <input id="email" type="email" name="email" required placeholder="me@example.com" />

                <label for="display_name">Tên hiển thị</label>
                <input id="display_name" type="text" name="display_name" required placeholder="Nhập tên của bạn" />

                <label for="password">Mật khẩu</label>
                <input id="password" type="password" name="password" minlength="6" required placeholder="••••••••" />

                <button type="submit" class="btn-register">
                    Tạo tài khoản
                </button>
            </form>

            <div class="footer">
                Đã có tài khoản? <a href="/">Quay lại đăng nhập</a>
            </div>
        </div>
    </body>
    </html>
    """

def _current_user_email_from_cookies(request: Request) -> str | None:
    cookie_header = request.headers.get("cookie", "")
    cookies = {}
    for pair in cookie_header.split(";"):
        if "=" in pair:
            key, value = pair.strip().split("=", 1)
            cookies[key] = value

    token = cookies.get("token")
    if not token:
        return None

    # Chainlit lưu token dưới dạng "Bearer <token_value>"
    if token.startswith("Bearer "):
        token = token[len("Bearer "):]

    # Token có thể được URL-encoded, cần decode trước khi giải mã JWT
    try:
        decoded_token = cl.security.decode_jwt(quote(token))
        email = decoded_token.get("sub")
        if isinstance(email, str):
            return email
    except Exception:
        return None

    return None

def _build_profile_html(email: str, display_name: str) -> str:
    safe_email = escape(email)
    safe_display = escape(display_name or "")

    return f"""
    <html><head><title>Hồ sơ</title><meta name="viewport" content="width=device-width, initial-scale=1" /></head>
    <body style="margin:0;background:#121212;color:#fff;font-family:Segoe UI,Arial,sans-serif">
      <div style="max-width:520px;margin:40px auto;padding:24px">
        <h2>Thông tin tài khoản</h2>
        
        <div id="toast" style="display:none; margin:10px 0; padding:10px; border-radius:8px; font-weight: 500;"></div>
        
        <form id="profileForm">
          <label>Email</label>
          <input value="{safe_email}" disabled style="width:100%;padding:10px;margin:8px 0 14px;background:#1e1e1e;color:#aaa;border:1px solid #333;border-radius:8px;" />
          <input type="hidden" name="email" value="{safe_email}" />
          
          <label>Tên hiển thị</label>
          <input name="display_name" value="{safe_display}" required style="width:100%;padding:10px;margin:8px 0 14px;background:#1e1e1e;color:#fff;border:1px solid #333;border-radius:8px;" />
          
          <button type="submit" style="padding:10px 14px;background:#ff1a66;color:white;border:none;border-radius:8px; cursor: pointer;">Lưu thay đổi</button>
        </form>
        
        <p style="margin-top:16px"><a target="_top" rel="noopener" href="/change-password?email={quote(email)}" style="color:#60a5fa">Đổi mật khẩu</a></p>
        <p><a target="_top" rel="noopener" href="/" style="color:#60a5fa">Quay lại chat</a></p>
      </div>

      <script>
        document.getElementById('profileForm').addEventListener('submit', async (e) => {{
            // 1. Chặn trình duyệt chuyển trang
            e.preventDefault(); 
            
            // 2. Gom dữ liệu form
            const formData = new FormData(e.target);
            
            // 3. Gửi ngầm qua Fetch
            const res = await fetch('/profile', {{ method: 'POST', body: formData }});
            const data = await res.json();
            
            // 4. Hiển thị thông báo ngay tại trang
            const toast = document.getElementById('toast');
            toast.style.display = 'block';
            toast.textContent = data.message;
            
            if (data.status === 'success') {{
                toast.style.background = '#1f8f5f'; // Màu xanh lá
                toast.style.color = '#fff';
            }} else {{
                toast.style.background = '#b42318'; // Màu đỏ
                toast.style.color = '#fff';
            }}

            // Tự động ẩn thông báo sau 3 giây
            setTimeout(() => {{
                toast.style.display = 'none';
            }}, 3000);
        }});
      </script>
    </body></html>
    """


def _build_change_password_html(email: str) -> str:
    safe_email = escape(email)
    
    return f"""
    <html><head>
        <title>Đổi mật khẩu</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{ margin:0; background:#121212; color:#fff; font-family:Segoe UI,Arial,sans-serif; }}
            .container {{ max-width:520px; margin:40px auto; padding:24px; }}
            
            /* CSS cho Pop-up Notification (Toast) */
            #toast-container {{
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
            }}
            .toast {{
                min-width: 250px;
                padding: 16px 20px;
                margin-bottom: 10px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                transition: all 0.4s ease;
                opacity: 0;
                transform: translateX(100%); /* Bay từ bên phải vào */
            }}
            .toast.show {{
                opacity: 1;
                transform: translateX(0);
            }}
            .toast-success {{ background-color: #1f8f5f; border-left: 5px solid #064e3b; }}
            .toast-error {{ background-color: #b42318; border-left: 5px solid #7a150a; }}

            /* Style cho Form */
            input {{ width:100%; padding:12px; margin:8px 0 20px; background:#1e1e1e; color:#fff; border:1px solid #333; border-radius:8px; outline:none; box-sizing: border-box; }}
            button {{ width:100%; padding:12px; background:#ff1a66; color:white; border:none; border-radius:8px; font-weight:600; cursor:pointer; }}
            button:disabled {{ background:#555; cursor: not-allowed; }}
        </style>
    </head>
    <body>
        <div id="toast-container"></div>

        <div class="container">
            <h2>Đổi mật khẩu</h2>
            <form id="passwordForm">
                <input type="hidden" name="email" value="{safe_email}" />
                <label>Mật khẩu hiện tại</label>
                <input type="password" name="current_password" required />
                <label>Mật khẩu mới</label>
                <input type="password" name="new_password" required />
                <button type="submit" id="submitBtn">Cập nhật mật khẩu</button>
            </form>
            <p style="margin-top:20px"><a target="_top" href="/profile?email={quote(email)}" style="color:#60a5fa; text-decoration:none;">← Quay lại hồ sơ</a></p>
        </div>

        <script>
            // Hàm tạo và hiển thị Pop-up
            function showToast(message, type = 'success') {{
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = `toast toast-${{type}}`;
                toast.textContent = message;
                
                container.appendChild(toast);
                
                // Kích hoạt hiệu ứng bay vào
                setTimeout(() => toast.classList.add('show'), 10);
                
                // Tự động xóa sau 4 giây
                setTimeout(() => {{
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 400);
                }}, 4000);
            }}

            // Xử lý gửi Form bằng Fetch (AJAX)
            document.getElementById('passwordForm').addEventListener('submit', async (e) => {{
                e.preventDefault(); // QUAN TRỌNG: Ngăn chặn trình duyệt load lại trang
                
                const btn = document.getElementById('submitBtn');
                btn.disabled = true;
                btn.textContent = 'Đang xử lý...';

                try {{
                    const formData = new FormData(e.target);
                    const res = await fetch('/change-password', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await res.json(); // Nhận dữ liệu JSON từ Backend
                    
                    if (data.status === 'success') {{
                        showToast(data.message, 'success');
                        e.target.reset(); // Xóa trắng form khi thành công
                    }} else {{
                        showToast(data.message, 'error');
                    }}
                }} catch (err) {{
                    showToast('Lỗi kết nối server', 'error');
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = 'Cập nhật mật khẩu';
                }}
            }});
        </script>
    </body></html>
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
        normalized_email, validation_error = _validate_register_input(email, password, display_name)
        if validation_error:
            return HTMLResponse(
                content=_build_register_html(validation_error, kind="error")
            )

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
# 4.5) Profile and change password routes
# -----------------------------
def _build_error_html(message: str) -> str:
    safe_message = escape(message)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Thông báo lỗi</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #121212; 
                color: #ffffff;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
            }}
            .container {{
                width: 100%;
                max-width: 420px;
                padding: 40px;
                box-sizing: border-box;
                text-align: center;
                background: #1e1e1e;
                border-radius: 12px;
                border: 1px solid #333;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            }}
            .icon {{
                font-size: 48px;
                color: #ff4d4d;
                margin-bottom: 20px;
            }}
            h2 {{
                margin: 0 0 16px 0;
                font-size: 22px;
            }}
            p {{
                color: #94a3b8;
                line-height: 1.6;
                margin-bottom: 24px;
            }}
            .btn-back {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #3b82f6;
                color: #fff;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                transition: background 0.3s;
            }}
            .btn-back:hover {{
                background-color: #2563eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">⚠️</div>
            <h2>Rất tiếc!</h2>
            <p>{safe_message}</p>
            <a href="/" class="btn-back">Quay lại trang chủ</a>
        </div>
    </body>
    </html>
    """



@cl.server.app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    email = _current_user_email_from_cookies(request)
    # Nếu không lấy được email từ cookie (ví dụ client không set session),
    # cho phép fallback sang query param để các link direct hoạt động.
    if not email:
        email = request.query_params.get("email")
    if not email:
        return HTMLResponse(_build_error_html("Không xác định được người dùng. Vui lòng đăng nhập lại."))
    db: Session = SessionLocal()
    try:
        u = get_user_by_email(db, email)
        if not u:
            return HTMLResponse(_build_error_html("Không tìm thấy tài khoản."))
        return HTMLResponse(_build_profile_html(u.email, u.display_name or ""))
    finally:
        db.close()


@cl.server.app.post("/profile")
async def profile_update(email: str = Form(...), display_name: str = Form(...)):
    db: Session = SessionLocal()
    try:
        u = get_user_by_email(db, email.strip().lower())
        if not u:
            return HTMLResponse(_build_error_html("Không tìm thấy tài khoản."))
            
        new_name = display_name.strip()
        if not new_name:
            return HTMLResponse(_build_error_html("Tên hiển thị không được để trống."))

        # Cập nhật DB
        update_user(db, u.id, display_name=new_name)
        db.commit() # Nhớ commit nếu update_user của bạn chưa làm việc này

        return JSONResponse(content={"status": "success", "message": "Cập nhật tên hiển thị thành công."})
    finally:
        db.close()


@cl.server.app.get("/change-password", response_class=HTMLResponse)
async def change_password_page(request: Request):
    # Ưu tiên lấy từ query param vì cookie trong Chainlit không ổn định
    email = request.query_params.get("email")
    
    if not email:
        # Fallback thử lấy từ cookie nếu có
        email = _current_user_email_from_cookies(request)
        
    if not email:
        # Nếu vẫn không có thì yêu cầu đăng nhập lại
        return HTMLResponse(_build_error_html("Không xác định được người dùng. Vui lòng đăng nhập lại."))
        
    return HTMLResponse(_build_change_password_html(email))


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
        _, validation_error = _validate_register_input(u.email, new_password, u.display_name or "User")
        if validation_error:
            return JSONResponse(content={"status": "error", "message": validation_error})

        # Cập nhật mật khẩu mới
        u.password_hash = hash_password(new_password)
        db.commit()

        return JSONResponse(content={"status": "success", "message": "Đổi mật khẩu thành công!"})
    except Exception as e:
        return HTMLResponse(_build_error_html("Có lỗi xảy ra, vui lòng thử lại."))
    finally:
        db.close()

# Prioritize the /register, /profile, and /change-password routes so they are matched before the default Chainlit auth routes
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
