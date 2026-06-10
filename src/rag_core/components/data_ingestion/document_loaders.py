import os 
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    WebBaseLoader,
)
from ...utils import setup_logger
import os 
import json
from dotenv import load_dotenv
from ....config import PROCESSED_DOCS_DIR, RAW_DOCS_DIR

load_dotenv()

logger = setup_logger("document_loader.log", "document_loader")

import re
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from pathlib import Path

# Get project root directory and direct to data folder
# ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent
# DATA_DIR = ROOT_DIR / "data" / "processed_documents"


def process_and_chunk_hust_documents(docs: List[Document]) -> List[Document]:
    """
    Nhận List[Document] (đã bị chia theo trang bởi PyPDFLoader), 
    gộp lại và cấu trúc hóa thành các chunk theo ngữ nghĩa Chương -> Điều.
    """
    if not docs:
        return []

    # 1. GỘP TEXT TỪ TẤT CẢ CÁC TRANG THUỘC CÙNG 1 FILE
    full_text = "\n".join([doc.page_content for doc in docs])
    
    # Giữ lại thông tin nguồn (đường dẫn file) từ trang đầu tiên
    base_source = docs[0].metadata.get("source", "Unknown_Source")
    cache_file_name = os.path.splitext(os.path.basename(base_source))[0]

    # Try to extract a leading UUID document id from the filename if present
    doc_id = None
    m = re.match(r'^([0-9a-fA-F-]{36})_', cache_file_name)
    if m:
        doc_id = m.group(1)

    # 2. TIỀN XỬ LÝ (CLEANING RÁC TỪ FILE CỦA BẠN)
    text = re.sub(r'\\s*', '', full_text)
    text = re.sub(r'--- PAGE \d+ ---', '', text)
    
    # 3. TÁCH THEO CHƯƠNG ĐỂ LÀM METADATA
    chuong_splits = re.split(r'(CHƯƠNG\s+[IVXLCDM]+)', text)
    
    new_documents = []
    current_chuong_meta = "Chưa xác định"
    
    for i in range(len(chuong_splits)):
        segment = chuong_splits[i].strip()
        if not segment: 
            continue
            
        if re.match(r'^CHƯƠNG\s+[IVXLCDM]+', segment):
            current_chuong_meta = segment
            # Bắt tên chương ở dòng tiếp theo
            if i + 1 < len(chuong_splits):
                title_match = re.search(r'^(.*?)\n', chuong_splits[i+1].strip())
                if title_match:
                    current_chuong_meta += " - " + title_match.group(1).strip()
        else:
            # 4. TÁCH THEO ĐIỀU
            dieu_splits = re.split(r'(?=\nĐiều\s+\d+\.)', segment)
            
            for dieu_content in dieu_splits:
                dieu_content = dieu_content.strip()
                if not dieu_content or len(dieu_content) < 20: 
                    continue
                
                # Lấy tên Điều
                dieu_match = re.match(r'^(Điều\s+\d+\.[^\n]+)', dieu_content)
                dieu_title_meta = dieu_match.group(1).strip() if dieu_match else "Nội dung chung"
                
                # Giữ nội dung sạch, ngữ cảnh nằm ở metadata để tránh làm nhiễu LLM
                doc = Document(
                    page_content=dieu_content,
                    metadata={
                        "source": base_source,
                        "chuong": current_chuong_meta,
                        "dieu": dieu_title_meta,
                    }
                )
                new_documents.append(doc)

    # 5. CẮT NHỎ CÁC ĐIỀU DÀI (Bảo toàn metadata)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,      
        chunk_overlap=150,    
        separators=["\n\n", "\n", ".", " ", ""] 
    )
    
    final_docs = text_splitter.split_documents(new_documents)

    # Attach document_id and chunk_index metadata for provenance
    for idx, doc in enumerate(final_docs):
        if not isinstance(doc.metadata, dict):
            doc.metadata = dict(doc.metadata or {})
        if doc_id:
            doc.metadata["document_id"] = doc_id
        doc.metadata["chunk_index"] = idx

    docs_dict = [doc.model_dump() for doc in final_docs]
    
    # Save the processed documents to a JSON file for caching and inspection
    with open(os.path.join(PROCESSED_DOCS_DIR, f"{cache_file_name}.json"), 'w') as f:
        json.dump(docs_dict, f, ensure_ascii=False, indent=4)

    return final_docs


def process_and_chunk_markdown_documents(docs: List[Document]) -> List[Document]:
    if not docs:
        return []

    # 1. Trích xuất thông tin định danh
    source = docs[0].metadata.get("source", "Unknown_Source")
    cache_file_name = os.path.splitext(os.path.basename(source))[0]

    # 2. Gộp và làm sạch văn bản
    full_text = "\n".join(doc.page_content for doc in docs)
    text = re.sub(r'--- PAGE \d+ ---', '', full_text)

    # 3. TỰ CHIA CHUNK THEO HEADING BẰNG REGEX (Pure Python)
    # Dùng Lookahead (?=...) để cắt ngay trước các dòng bắt đầu bằng **Số.
    split_pattern = r'(?m)^(?=\*\*(?:\d+|[A-Z]+)\.\s+)'
    raw_chunks = re.split(split_pattern, text)
    
    md_docs = []
    for chunk in raw_chunks:
        if not chunk.strip():
            continue
            
        # Tìm tiêu đề để đưa vào Metadata
        heading_match = re.match(r'^\*\*((?:\d+|[A-Z]+)\.\s+.*?)\*\*', chunk)
        if heading_match:
            heading_title = heading_match.group(1).strip()
            # Đổi **1. Text** thành chuẩn Markdown # 1. Text để LLM dễ đọc ngữ cảnh
            # CHÚ Ý: Đã bỏ .*$ để KHÔNG ăn mất phần text đằng sau
            clean_chunk_content = re.sub(r'^\*\*((?:\d+|[A-Z]+)\.\s+.*?)\*\*', r'# \1', chunk)
        else:
            heading_title = "Thông tin chung"
            clean_chunk_content = chunk

        # Gói vào Document với metadata chứa Heading
        md_docs.append(Document(
            page_content=clean_chunk_content.strip(),
            metadata={"source": source, "Header_1": heading_title}
        ))

    # 4. Cắt các section quá dài bằng Recursive Splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    
    # Splitter này sẽ giữ nguyên metadata Header_1 của md_docs
    final_docs = text_splitter.split_documents(md_docs)

    # 5. Xử lý Metadata hệ thống và lưu JSON
    m = re.match(r'^([0-9a-fA-F-]{36})_', cache_file_name)
    doc_id = m.group(1) if m else None

    for idx, doc in enumerate(final_docs):
        if not isinstance(doc.metadata, dict):
            doc.metadata = dict(doc.metadata or {})
        if doc_id:
            doc.metadata["document_id"] = doc_id
        doc.metadata["chunk_index"] = idx

    # Export ra JSON
    os.makedirs(PROCESSED_DOCS_DIR, exist_ok=True)
    docs_dict = [doc.model_dump() for doc in final_docs]

    with open(os.path.join(PROCESSED_DOCS_DIR, f"{cache_file_name}.json"), 'w', encoding='utf-8') as f:
        json.dump(docs_dict, f, ensure_ascii=False, indent=4)

    return final_docs


class UniversityDocumentLoader:
    def __init__(self, file_path: str, file_cache_path: str = PROCESSED_DOCS_DIR):
        self.file_path = file_path
        self.file_cache_path = file_cache_path

    def load_file(self, file_path: str) -> List[Document]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = os.path.splitext(file_path)[1].lower() # Get the file extension

        try: 
            if extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif extension in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            elif extension in [".txt", ".md"]:
                loader = TextLoader(file_path)
            else:
                logger.warning(f"Unsupported file type: {extension}. Skipping file: {file_path}")
                return []
            
            documents = loader.load()
            logger.info(f"Successfully loaded documents from {file_path}")
            return documents
        
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            return []
        
    def load_web_page(self, url: str) -> List[Document]:
        try:
            loader = WebBaseLoader(url)
            documents = loader.load()
            logger.info(f"Successfully loaded documents from {url}")
            return documents
        except Exception as e:
            logger.error(f"Error loading web page {url}: {str(e)}")
            return []
        
    def load_all_documents(self) -> List[Document]:
        all_documents = []

        if not os.path.exists(self.file_path):
            logger.error(f"File path does not exist: {self.file_path}")
            os.makedirs(self.file_path, exist_ok=True)
            return all_documents
        
        for file_name in os.listdir(self.file_path):
            file_path = os.path.join(self.file_path, file_name)
            if os.path.isfile(file_path):
                # Check for cache
                cache_file_name = os.path.splitext(file_name)[0] + ".json"
                cache_file_path = os.path.join(self.file_cache_path, cache_file_name)

                if os.path.exists(cache_file_path):
                    logger.info(f"Loading cached processed documents from {cache_file_path}")
                    with open(cache_file_path, 'r') as f:
                        cached_docs_dict = json.load(f)
                        cached_docs = [Document(**doc) for doc in cached_docs_dict]
                        # Attach document_id from filename if missing
                        m = re.match(r'^([0-9a-fA-F-]{36})_', os.path.splitext(file_name)[0])
                        if m:
                            cached_doc_id = m.group(1)
                            for d in cached_docs:
                                if not isinstance(d.metadata, dict):
                                    d.metadata = dict(d.metadata or {})
                                if "document_id" not in d.metadata:
                                    d.metadata["document_id"] = cached_doc_id
                        all_documents.extend(cached_docs)
                
                else:
                    # Load từng file (docs lúc này đang bị chia theo TRANG)
                    raw_docs = self.load_file(file_path)
                    # Extract document_id from filename if present and attach to raw docs
                    m = re.match(r'^([0-9a-fA-F-]{36})_', os.path.splitext(file_name)[0])
                    raw_doc_id = m.group(1) if m else None
                
                    # Nếu là file PDF quy chế hoặc markdown, đưa qua bộ lọc chunking
                    if file_name.endswith(".pdf"):
                        processed_docs = process_and_chunk_hust_documents(raw_docs)
                        all_documents.extend(processed_docs)
                    elif file_name.endswith(".md"):
                        processed_docs = process_and_chunk_markdown_documents(raw_docs)
                        all_documents.extend(processed_docs)
                    else:
                        # Các file khác giữ nguyên hoặc dùng RecursiveCharacterTextSplitter cơ bản
                        if raw_doc_id:
                            for d in raw_docs:
                                if not isinstance(d.metadata, dict):
                                    d.metadata = dict(d.metadata or {})
                                d.metadata["document_id"] = raw_doc_id
                        all_documents.extend(raw_docs)

        return all_documents

if __name__ == "__main__":
    loader = UniversityDocumentLoader(RAW_DOCS_DIR)
    documents= loader.load_all_documents()
    print(f"Đã tạo ra {len(documents)} semantic chunks.")

        