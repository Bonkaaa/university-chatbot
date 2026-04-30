# 🎓 Chatbot Đại Học - University Chatbot 

Một ứng dụng chatbot AI tiên tiến được thiết kế để hỗ trợ sinh viên và người dùng trả lời các câu hỏi liên quan đến các chương trình đào tạo, quy định, thông tin tuyển sinh, và chính sách của trường đại học.

[Link tới website deploy](https://university-chatbot-d4di.onrender.com)
## ✨ Tính Năng Chính

- **RAG (Retrieval Augmented Generation)**: Kết hợp tìm kiếm mật độ (dense) và thưa thớt (sparse) để truy xuất thông tin chính xác
- **Quản lý Người Dùng**: Đăng ký, đăng nhập, và quản lý hồ sơ người dùng
- **Lịch Sử Cuộc Trò Chuyện**: Lưu trữ tất cả các cuộc hội thoại cho mỗi người dùng
- **Xử Lý Tài Liệu**: Hỗ trợ nhiều định dạng (PDF, DOCX, TXT)
- **Giao Diện Thân Thiện**: Hệ thống chat trực tuyến với Chainlit
- **API REST**: Backend FastAPI cho tích hợp bên thứ ba
- **Bảo Mật**: Xác thực người dùng với JWT, mã hóa mật khẩu

## 🛠️ Tech Stack

| Thành Phần | Công Nghệ |
|-----------|-----------|
| **Frontend** | Chainlit 2.11.0 |
| **Backend** | FastAPI, SQLAlchemy |
| **LLM & RAG** | LangChain, LangGraph, Ollama |
| **Vector Store** | ChromaDB |
| **Database** | SQLite, SQLAlchemy |
| **Embeddings** | BGE-M3 (HuggingFace) |
| **LLM Model** | Xiaomi MIMO-v2-Omni |
| **Security** | JWT, Passlib, Bcrypt |
| **Utilities** | PyPDF, Docx2txt, Rank-BM25 |

## 📁 Cấu Trúc Dự Án

```
university_chatbot/
├── src/
│   ├── main.py                 # Entry point - Chainlit app
│   ├── config.py               # Cấu hình toàn cục
│   ├── agent/                  # RAG Agent logic
│   │   ├── agent.py           # Agent chính
│   │   └── graph.py           # LangGraph workflow
│   ├── app/                    # Backend application
│   │   ├── main.py            # FastAPI routes
│   │   ├── db.py              # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── crud/              # Database operations
│   │   ├── routes/            # API routes
│   │   └── core/              # Core utilities (auth, security)
│   ├── rag_core/              # RAG components
│   │   ├── utils.py           # RAG utilities
│   │   └── components/        # Retriever, prompt engineering
│   └── ui/                    # UI components & forms
├── data/
│   ├── raw_documents/         # Tài liệu gốc để upload
│   ├── processed_documents/   # Tài liệu đã xử lý
│   ├── chroma_db/             # Vector store
│   ├── embedding_cache/       # Cache embeddings
│   ├── chat_history_db/       # Lịch sử chat Chainlit
│   └── conversation_db/       # Lịch sử cuộc hội thoại
├── database/                  # SQLite databases
├── logs/                      # Application logs
├── public/                    # Chainlit public assets
├── requirements.txt           # Python dependencies
├── chainlit.md               # Chainlit welcome message
└── README.md                 # File này
```

## 📋 Yêu Cầu

- Python 3.8+
- pip hoặc conda
- Virtual Environment

## 🚀 Cài Đặt

### 1. Clone Repository
```bash
cd c:\university_chatbot
```

### 2. Tạo Virtual Environment
```bash
python -m venv .venv
```

### 3. Kích Hoạt Virtual Environment (Windows PowerShell)
```powershell
.venv\Scripts\Activate.ps1
```

### 4. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 5. Tạo File `.env`
```bash
# Tạo file .env trong thư mục root
PYTHONPATH=C:\university_chatbot
```

## ⚙️ Cấu Hình

Chỉnh sửa `src/config.py` để cấu hình:

```python
# Model LLM
MODEL_NAME = "xiaomi/mimo-v2-omni"
EMBED_MODEL_NAME = "hf.co/CompendiumLabs/bge-m3-gguf:latest"

# Retriever strategy
RETRIEVER_TYPE = "hybrid"  # "dense", "sparse", hoặc "hybrid"

# Conversation history
MAX_CONVERSATION_HISTORY = 5

# Thư mục dữ liệu
RAW_DOCS_DIR = "data/raw_documents"
PROCESSED_DOCS_DIR = "data/processed_documents"
CHROMA_DB_DIR = "data/chroma_db"
```

## ▶️ Chạy Ứng Dụng

### Chạy Chainlit Frontend
```bash
# Đảm bảo PYTHONPATH được đặt
$env:PYTHONPATH = "C:\university_chatbot"

# Chạy Chainlit
chainlit run src/main.py -w
```

Ứng dụng sẽ khởi động tại: `http://localhost:8000`

### Chạy FastAPI Backend
```bash
uvicorn src.app.main:app --reload --port 8001
```

Backend API sẽ có sẵn tại: `http://localhost:8001`

## 🔐 Quản Lý PYTHONPATH

### Cách 1: Thiết Lập Trong Terminal (Tạm Thời)
```powershell
$env:PYTHONPATH = "C:\university_chatbot"
```

### Cách 2: Tệp `.env` (Khuyên Dùng)
Tạo file `.env` trong thư mục gốc:
```
PYTHONPATH=C:\university_chatbot
```

### Cách 3: Biến Môi Trường Hệ Thống
- Nhấp phải trên **This PC** → **Properties**
- Click **Advanced system settings**
- Nhấp **Environment Variables**
- Tạo biến mới: `PYTHONPATH = C:\university_chatbot`

## 📊 Quy Trình RAG

1. **Nhập Tài Liệu**: Tải tài liệu (PDF, DOCX, TXT) vào `data/raw_documents/`
2. **Xử Lý**: Tài liệu được chia thành chunks và xử lý
3. **Embedding**: Tạo embeddings và lưu vào ChromaDB
4. **Truy Xuất Khi Trả Lời**: 
   - Hybrid retrieval kết hợp dense + sparse search
   - Trả lại các documents liên quan nhất
5. **Tạo Phản Hồi**: LLM tổng hợp thông tin và trả lời câu hỏi

## 🔗 API Endpoints (FastAPI)

- `POST /auth/register` - Đăng ký người dùng mới
- `POST /auth/login` - Đăng nhập
- `GET /users/profile` - Lấy hồ sơ người dùng
- `PUT /users/profile` - Cập nhật hồ sơ
- `GET /conversations` - Danh sách cuộc trò chuyện
- `GET /conversations/{id}/messages` - Lấy tin nhắn trong cuộc hội thoại

## 📝 Ghi Chú Phát Triển

### Thêm Tài Liệu Mới
1. Đặt tài liệu vào `data/raw_documents/`
2. Khởi động lại ứng dụng để tự động xử lý và embedding
3. Hoặc chạy script xử lý tài liệu thủ công

### Tùy Chỉnh Prompt
- Chỉnh sửa prompt trong `src/rag_core/components/`
- Cập nhật hệ thống prompt cho agent

### Debug
- Kiểm tra logs trong thư mục `logs/`
- Sử dụng `-v` flag cho verbose mode

## 🤝 Đóng Góp

Nếu gặp vấn đề hoặc có câu hỏi, bạn có thể tạo PR để được hỗ trợ

## 📄 License

Dự án này được phân phối dưới MIT License. Xem `LICENSE` file để biết chi tiết.

---

**Lần cập nhật cuối**: April 2026  
**Phiên bản**: 1.0.0
