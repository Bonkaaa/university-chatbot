from email_validator import EmailNotValidError, validate_email
import re
from html import escape
from urllib.parse import quote

# Configuration for password validation
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIREMENTS_MSG = (
    "Mật khẩu phải có ít nhất 8 ký tự, gồm chữ hoa, chữ thường và chữ số."
)

def validate_register_input(email: str, password: str, display_name: str) -> tuple[str, str | None]:
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

def build_change_password_html(user_id: str, email: str) -> str:
    safe_email = escape(email)
    safe_user_id = escape(str(user_id))
    
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
                <input type="hidden" name="user_id" value="{safe_user_id}" />
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