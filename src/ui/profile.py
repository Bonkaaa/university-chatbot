from html import escape
from urllib.parse import quote

def build_profile_html(user_id: int, email: str, display_name: str) -> str:
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