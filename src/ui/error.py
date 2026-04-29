from html import escape

def build_error_html(message: str) -> str:
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