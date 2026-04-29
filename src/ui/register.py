from html import escape


def build_register_html(message: str = "", kind: str = "info") -> str:
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