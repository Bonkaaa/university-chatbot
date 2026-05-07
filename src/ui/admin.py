from html import escape

def build_admin_upload_html(message: str | None = None, kind: str = "success") -> str:
    notice = ""
    if message:
        color = "#1f8f5f" if kind == "success" else "#b42318"
        notice = f"""
        <div style="background:{color};padding:12px;border-radius:8px;margin-bottom:16px;color:#fff;">
            {escape(message)}
        </div>
        """

    return f"""
    <html>
    <head>
        <title>Admin - Upload Document</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{ margin:0;background:#121212;color:#fff;font-family:Segoe UI,Arial,sans-serif; }}
            .container {{ max-width:520px;margin:40px auto;padding:24px; }}
            h2 {{ margin-bottom:8px; }}
            p.subtitle {{ color:#94a3b8;margin:0 0 20px 0;font-size:14px; }}
            label {{ font-size:13px;color:#e2e8f0;display:block;margin-bottom:8px; }}
            input[type="file"] {{
                width:100%;padding:10px;background:#1e1e1e;color:#fff;border:1px solid #333;border-radius:8px;
                margin-bottom:16px;
            }}
            .btn-upload {{
                width:100%;padding:12px;background:#ff1a66;color:#fff;border:none;border-radius:8px;
                font-weight:600;font-size:16px;cursor:pointer;
            }}
            .btn-upload:hover {{ background:#e6005c; }}
            .footer a {{ color:#60a5fa;text-decoration:none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Upload tài liệu</h2>
            <p class="subtitle">Chỉ chấp nhận file PDF hoặc Markdown (.md).</p>

            {notice}

            <form action="/admin/upload" method="post" enctype="multipart/form-data">
                <label for="file">Chọn file</label>
                <input id="file" type="file" name="file" accept=".pdf,.md" required />
                <button class="btn-upload" type="submit">Tải lên</button>
            </form>

            <p class="footer" style="margin-top:16px">
                <a href="/">Quay lại chat</a>
            </p>
        </div>
    </body>
    </html>
    """

def build_admin_dashboard_html(admin_name: str = "Admin") -> str:
    safe_name = escape(admin_name)

    return f"""
    <html>
    <head>
        <title>Admin Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{ margin:0;background:#121212;color:#fff;font-family:Segoe UI,Arial,sans-serif; }}
            .container {{ max-width:900px;margin:40px auto;padding:24px; }}
            .card {{
                background:#1e1e1e;border:1px solid #333;border-radius:12px;
                padding:16px;margin-bottom:16px;
            }}
            h1 {{ margin:0 0 8px 0; }}
            p.subtitle {{ color:#94a3b8;margin:0 0 24px 0;font-size:14px; }}
            .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; }}
            .stat {{ font-size:28px; font-weight:700; }}
            .label {{ color:#94a3b8; font-size:13px; }}
            .link-btn {{
                display:inline-block;margin-right:12px;margin-top:8px;
                padding:10px 14px;background:#ff1a66;color:#fff;
                border-radius:8px;text-decoration:none;font-weight:600;
            }}
            .link-btn:hover {{ background:#e6005c; }}
            .muted {{ color:#94a3b8; font-size:13px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Xin chào, {safe_name} 👋</h1>
            <p class="subtitle">Tổng quan hệ thống chatbot và công cụ quản trị.</p>

            <div class="card">
                <h3>Truy cập nhanh</h3>
                <a class="link-btn" href="/admin/upload">Upload tài liệu</a>
                <a class="link-btn" href="/admin/users">Quản lý người dùng</a>
                <a class="link-btn" href="/chat?1">Quay lại chat</a>
                <p class="muted">* Các trang quản trị chỉ dành cho admin.</p>
            </div>

            <div class="card">
                <h3>Tổng quan hệ thống (demo)</h3>
                <div class="grid">
                    <div>
                        <div class="stat">—</div>
                        <div class="label">Tổng số người dùng</div>
                    </div>
                    <div>
                        <div class="stat">—</div>
                        <div class="label">Tài liệu đã tải</div>
                    </div>
                    <div>
                        <div class="stat">—</div>
                        <div class="label">Lần cập nhật gần nhất</div>
                    </div>
                    <div>
                        <div class="stat">—</div>
                        <div class="label">Trạng thái index</div>
                    </div>
                </div>
                <p class="muted" style="margin-top:12px;">
                    Bạn có thể cập nhật các số liệu này sau bằng cách truy vấn DB.
                </p>
            </div>

            <div class="card">
                <h3>Gợi ý</h3>
                <ul>
                    <li>Kiểm tra danh sách tài liệu sau mỗi lần upload.</li>
                    <li>Quản lý user theo vai trò admin/user.</li>
                    <li>Chạy re-index nếu chatbot không phản hồi đúng tài liệu mới.</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
