from html import escape


def build_react_page_html(title: str, page: str) -> str:
    safe_title = escape(title)
    safe_page = escape(page)
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{safe_title}</title>
  <link rel="stylesheet" href="/public/react-pages.css" />
</head>
<body data-page="{safe_page}">
  <div id="app"></div>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="/public/react-pages.js"></script>
</body>
</html>
"""
