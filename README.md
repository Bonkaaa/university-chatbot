# 🎓 Chatbot Đại Học - University Chatbot 

Một ứng dụng chatbot AI tiên tiến được thiết kế để hỗ trợ sinh viên và người dùng trả lời các câu hỏi liên quan đến các chương trình đào tạo, quy định, thông tin tuyển sinh, và chính sách của trường đại học.

[Link tới website deploy](https://university-chatbot-d4di.onrender.com)

!!! Hiện tại do đã xoá api keycủa LLM (Do hết tiền ạ) nên web chỉ có thể dùng làm mẫu chứ không thể dùng được chức năng Chatbot

## ✨ Tính Năng Chính

- **RAG (Retrieval Augmented Generation)**: Kết hợp tìm kiếm mật độ (dense) và thưa thớt (sparse) để truy xuất thông tin chính xác.
- **Quản lý Người Dùng**: Đăng ký, đăng nhập, và quản lý hồ sơ người dùng.
- **Lịch Sử Cuộc Trò Chuyện**: Lưu trữ tất cả các cuộc hội thoại cho mỗi người dùng.
- **Xử Lý Tài Liệu**: Hỗ trợ nhiều định dạng tài liệu (PDF, DOCX, TXT) và trích xuất dữ liệu trực tiếp từ các trang web/API trường học.
- **Giao Diện Thân Thiện**: Giao diện chat trực tuyến trực quan qua Chainlit, tích hợp sẵn các trang quản lý hồ sơ cá nhân, cập nhật mật khẩu và trang quản trị (Admin).
- **API REST**: Backend FastAPI mạnh mẽ và linh hoạt cho tích hợp bên thứ ba.
- **Bảo Mật**: Xác thực người dùng bằng JSON Web Token (JWT), mã hóa mật khẩu bằng bcrypt.

## 🛠️ Tech Stack

| Thành Phần       | Công Nghệ                                                |
| ------------------| ----------------------------------------------------------|
| **Frontend**     | Chainlit 2.11.0, ReactJS                                 |
| **Backend**      | FastAPI, SQLAlchemy, Uvicorn                             |
| **LLM & RAG**    | LangChain, LangGraph, Ollama, OpenRouter, Groq           |
| **Vector Store** | ChromaDB, LangChain Chroma                               |
| **Database**     | SQLite, SQLAlchemy, AioSQLite                            |
| **Embeddings**   | Paraphrase Multilingual MiniLM L12 v2 / BGE-M3           |
| **LLM Model**    | GPT-OSS-120B / các model tương thích qua OpenRouter/Groq |
| **Security**     | JWT (python-jose), Passlib, Bcrypt                       |
| **Utilities**    | PyPDF, Docx2txt, Rank-BM25, BeautifulSoup4, Markdownify  |

## 📁 Cấu Trúc Dự Án

Chi tiết cấu trúc thư mục và các file cốt lõi trong dự án:

```
university_chatbot/
├── .chainlit/                  # Cấu hình giao diện và giao diện người dùng của Chainlit
│   ├── config.toml             # File cấu hình chính của Chainlit (theme, port, auth...)
│   └── translations/           # Các bản dịch ngôn ngữ cho giao diện Chainlit
├── data/                       # Thư mục chứa cơ sở dữ liệu và dữ liệu RAG
│   ├── chat_history_db/        # Lưu trữ lịch sử chat của Chainlit
│   ├── chroma_db/              # Vector store chứa các embeddings tài liệu đã xử lý
│   ├── conversation_db/        # SQLite database lưu thông tin cuộc trò chuyện
│   ├── embedding_cache/        # Bộ nhớ đệm cache cho embeddings để tăng tốc độ xử lý
│   ├── processed_documents/    # Tài liệu văn bản sau khi đã được chunk và tiền xử lý
│   ├── raw_docs_for_scrape/    # Chứa tài liệu tạm phục vụ việc crawl/scrape dữ liệu web
│   └── raw_documents/          # Tài liệu gốc (PDF, DOCX, TXT) được tải lên làm tri thức nền
├── database/                   # Thư mục cơ sở dữ liệu SQLite của ứng dụng backend
├── logs/                       # Ghi lại hoạt động hệ thống và thông tin lỗi (logs)
├── public/                     # Thư mục lưu trữ tài nguyên tĩnh (images, css, js) của Chainlit
├── scripts/                    # Chứa các script cài đặt nhanh cho hệ thống
│   ├── run.sh                  # Script khởi chạy ứng dụng nhanh trên Linux/macOS
│   └── setup.sh                # Script thiết lập môi trường ảo ban đầu
├── src/                        # Thư mục mã nguồn chính của ứng dụng
│   ├── main.py                 # Entry point chính của ứng dụng Chainlit Frontend
│   ├── config.py               # Cấu hình dự án (đường dẫn dữ liệu, tên LLM/Embedding model, cài đặt RAG)
│   ├── agent/                  # Logic điều phối RAG Agent
│   │   ├── __init__.py
│   │   ├── agent.py            # Cấu hình logic RAG Agent chính
│   │   └── graph.py            # Workflow của Agent được xây dựng qua LangGraph
│   ├── app/                    # Ứng dụng Backend API (FastAPI)
│   │   ├── main.py             # Entry point FastAPI, định nghĩa và đăng ký các routes
│   │   ├── backend.py          # Script cấu hình cơ sở dữ liệu và khởi tạo ứng dụng FastAPI
│   │   ├── db.py               # Thiết lập SessionLocal và engine SQLite với SQLAlchemy
│   │   ├── core/               # Các chức năng cốt lõi cho Backend
│   │   │   ├── deps.py         # FastAPI dependencies (lấy DB session, lấy current user)
│   │   │   ├── local_storage.py# Tiện ích quản lý và lưu trữ tài liệu tải lên cục bộ
│   │   │   └── security.py     # Xử lý băm mật khẩu và mã hóa/giải mã JWT token
│   │   ├── crud/               # Các thao tác CRUD dữ liệu với Database
│   │   │   ├── conversation_crud.py
│   │   │   ├── document_metadata_crud.py
│   │   │   ├── message_crud.py
│   │   │   └── user_crud.py
│   │   ├── models/             # Định nghĩa cấu trúc các bảng dữ liệu (SQLAlchemy ORM models)
│   │   │   ├── conversation.py
│   │   │   ├── document_chunk.py
│   │   │   ├── document_metadata.py
│   │   │   ├── message.py
│   │   │   ├── session.py
│   │   │   └── user.py
│   │   ├── routes/             # Thiết lập endpoints cho API
│   │   │   ├── auth_routes.py  # Đăng ký, đăng nhập và xác thực JWT
│   │   │   ├── conversation_routes.py # Quản lý hội thoại
│   │   │   └── message_routes.py    # Quản lý tin nhắn
│   │   └── schemas/            # Schemas Pydantic dùng để xác thực dữ liệu đầu vào/ra
│   │       ├── auth.py
│   │       ├── conversation.py
│   │       ├── message.py
│   │       └── user.py
│   ├── rag_core/               # Thành phần cốt lõi của RAG
│   │   ├── __init__.py
│   │   ├── utils.py            # Các hàm tiện ích hỗ trợ (đếm token, tiền xử lý văn bản)
│   │   └── components/         # Các thành phần chi tiết của RAG pipeline
│   │       ├── data_ingestion/ # Nhập và xử lý tài liệu tri thức
│   │       │   ├── document_loaders.py # Hỗ trợ load tài liệu PDF, DOCX, TXT
│   │       │   ├── scraper.py  # Crawl dữ liệu từ các trang thông tin hoặc API đại học
│   │       │   └── text_splitter.py # Phân tách tài liệu thành các chunks tối ưu
│   │       ├── generate_answer.py # Thiết lập prompt và gửi truy vấn tới LLM để sinh câu trả lời
│   │       ├── model.py        # Khởi tạo mô hình LLM và Embedding model dựa trên config
│   │       ├── retriever.py    # Bộ truy xuất kết hợp (Dense + BM25 Sparse Retriever)
│   │       └── templates.py    # Định nghĩa các system prompt templates
│   └── ui/                     # Giao diện người dùng Chainlit tùy chỉnh
│       ├── admin.py            # Giao diện quản lý của Admin (quản lý file tài liệu, người dùng)
│       ├── error.py            # Giao diện thông báo lỗi hệ thống
│       ├── password.py         # Giao diện đổi mật khẩu người dùng
│       ├── profile.py          # Giao diện trang cá nhân người dùng
│       ├── react_page.py       # Tích hợp trang React tùy chỉnh
│       └── register.py         # Giao diện đăng ký tài khoản Chainlit
├── .env                        # File chứa các biến môi trường cấu hình API keys (Không đẩy lên Git)
├── .env.example                # File mẫu cấu hình biến môi trường
├── .gitattributes
├── .gitignore
├── Dockerfile                  # Cấu hình build Docker image cho ứng dụng
├── README.md                   # Hướng dẫn chi tiết về dự án (file này)
├── chainlit.md                 # Nội dung hiển thị tại trang Welcome của ứng dụng Chat
├── requirements.txt            # Danh sách các thư viện Python phụ thuộc
├── setup_dir.py                # Script thiết lập tự động các thư mục dữ liệu và khởi tạo DB ban đầu
├── test_scrape.py              # Script test crawl dữ liệu từ API trường học
└── testing.ipynb               # Jupyter notebook dùng để test nhanh và debug tính năng RAG
```

## 📋 Yêu Cầu

- Python 3.8+
- pip hoặc conda
- Môi trường ảo (Virtual Environment)
- Tài khoản và API Key của các dịch vụ LLM (OpenRouter, Groq, hoặc LangChain nếu cần tracing)

## 🚀 Hướng Dẫn Cài Đặt

### 1. Clone Repository
```bash
git clone <repo_url>
cd university_chatbot
```

### 2. Tạo Môi Trường Ảo (Virtual Environment)
```bash
python -m venv .venv
```

### 3. Kích Hoạt Môi Trường Ảo
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (Git Bash/CMD):**
  ```bash
  source .venv/Scripts/activate
  ```
- **Linux/macOS:**
  ```bash
  source .venv/bin/activate
  ```

### 4. Cài Đặt Các Thư Viện Phụ Thuộc
```bash
pip install -r requirements.txt
```

### 5. Cấu Hình File Môi Trường `.env`
Sao chép file `.env.example` thành `.env` và cập nhật các thông tin API key của bạn:
```bash
cp .env.example .env
```
Các biến cấu hình quan trọng trong `.env`:
```env
PYTHONPATH=C:\university_chatbot
GROQ_API_KEY=<your_groq_api_key>
OPENROUTER_API_KEY=<your_openrouter_api_key>
GOOGLE_API_KEY=<your_google_api_key>
HUGGINGFACEHUB_API_TOKEN=<your_huggingface_token>
CHAINLIT_AUTH_SECRET=<chuỗi_bí_mật_tùy_ý>
SECRET_KEY=<chuỗi_bí_mật_cho_jwt>
```

### 6. Khởi Tạo Thư Mục Và Cơ Sở Dữ Liệu
Chạy script `setup_dir.py` để tự động tạo toàn bộ thư mục dữ liệu (`data/`, `database/`...) và khởi tạo cơ sở dữ liệu SQLite ban đầu:
```bash
python setup_dir.py
```

## ⚙️ Cấu Hình Hệ Thống

Bạn có thể điều chỉnh cấu hình toàn cục tại file `src/config.py`:

```python
# Tên LLM và Embedding model sử dụng
MODEL_NAME = "openai/gpt-oss-120b"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Phương thức truy xuất thông tin (Retriever Strategy)
RETRIEVER_TYPE = "hybrid"  # Hỗ trợ: "dense", "sparse" hoặc "hybrid"

# Số lượng hội thoại tối đa được lưu trữ trong bộ nhớ đệm lịch sử
MAX_CONVERSATION_HISTORY = 5
```

## ▶️ Hướng Dẫn Chạy Ứng Dụng

Ứng dụng chạy song song hai thành phần: FastAPI Backend (API & Database) và Chainlit Frontend (Giao diện Chat).

### Bước 1: Khởi Chạy FastAPI Backend
Chạy lệnh uvicorn từ thư mục gốc dự án:
```bash
uvicorn src.app.main:app --reload --port 8001
```
Backend API và tài liệu Swagger sẽ có tại:
- API endpoints: `http://localhost:8001`
- Swagger UI docs: `http://localhost:8001/docs`

### Bước 2: Khởi Chạy Chainlit Frontend
Mở một terminal mới (đã kích hoạt môi trường ảo) và đặt biến môi trường `PYTHONPATH` trước khi khởi chạy:

- **Windows (PowerShell):**
  ```powershell
  $env:PYTHONPATH = "C:\university_chatbot"
  chainlit run src/main.py -w
  ```
- **Linux/macOS / Git Bash:**
  ```bash
  export PYTHONPATH="."
  chainlit run src/main.py -w
  ```

Giao diện chat sẽ tự động mở tại địa chỉ: `http://localhost:8000`

## 📊 Quy Trình Hoạt Động RAG (Retrieval-Augmented Generation)

1. **Nhập & Thu Thập Tài Liệu**: Tài liệu gốc (PDF, DOCX, TXT) được tải vào thư mục `data/raw_documents/` hoặc crawl qua API/website với `scraper.py`.
2. **Tiền Xử Lý & Phân Tách**: Tài liệu được trích xuất văn bản và phân nhỏ thành các đoạn ngắn (chunks) bằng `text_splitter.py`.
3. **Mã Hóa & Lưu Trữ (Embedding)**: Chunks tài liệu được chuyển đổi thành vector thông qua embedding model và lưu trữ tập trung vào vector database ChromaDB (`data/chroma_db/`).
4. **Truy Xuất (Retrieval)**: Khi người dùng gửi câu hỏi, hệ thống thực hiện tìm kiếm kết hợp (Hybrid Search):
   - **Dense Retrieval**: Sử dụng ChromaDB tìm kiếm ngữ nghĩa theo Vector.
   - **Sparse Retrieval**: Sử dụng thuật toán Rank-BM25 tìm kiếm theo từ khóa.
   - Kết quả từ cả hai phương thức được tổng hợp và xếp hạng lại nhằm lấy ra ngữ cảnh (context) chính xác nhất.
5. **Sinh Câu Trả Lời (Generation)**: Tổng hợp câu hỏi và ngữ cảnh đã tìm được gửi vào Prompt template, LLM sẽ phân tích và sinh ra câu trả lời chính xác, đáng tin cậy.

## 🔗 Các API Endpoints Chính (FastAPI Backend)

- `POST /auth/register` - Đăng ký tài khoản người dùng mới.
- `POST /auth/login` - Đăng nhập nhận JWT Access Token.
- `GET /users/profile` - Lấy thông tin cá nhân của người dùng hiện tại.
- `PUT /users/profile` - Cập nhật thông tin cá nhân.
- `GET /conversations` - Xem danh sách các cuộc trò chuyện của người dùng.
- `GET /conversations/{id}/messages` - Lấy toàn bộ tin nhắn thuộc một cuộc trò chuyện.

## 📝 Ghi Chú Phát Triển & Debug

### Thêm Tài Liệu Tri Thức Mới
1. Đặt tài liệu mới dạng `.pdf`, `.docx` hoặc `.txt` vào thư mục `data/raw_documents/`.
2. Chạy lại `python setup_dir.py` để đồng bộ metadata tài liệu vào cơ sở dữ liệu.
3. Khi khởi động ứng dụng Chainlit, RAG pipeline sẽ tự động phát hiện, chunk tài liệu mới và tiến hành index vào ChromaDB.

### Debug & Theo Dõi Logs
- Toàn bộ logs trong quá trình chạy sẽ được lưu trữ trong thư mục `logs/`.
- Nếu có lỗi trong quá trình nhúng tài liệu hoặc sinh câu trả lời, hãy kiểm tra file log hoặc theo dõi console của terminal chạy Chainlit/FastAPI.

## 🤝 Đóng Góp

Mọi đóng góp, báo lỗi hoặc đề xuất tính năng mới, vui lòng tạo **Issue** hoặc gửi **Pull Request (PR)** trực tiếp trong dự án.

## 📄 License

Dự án này được phân phối dưới MIT License. Chi tiết vui lòng tham khảo file `LICENSE`.

---

**Cập nhật lần cuối**: Tháng 6, 2026  
**Phiên bản**: 1.0.1
