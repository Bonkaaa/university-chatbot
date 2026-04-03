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
from dotenv import load_dotenv

load_dotenv()

logger = setup_logger("document_loader.log", "document_loader")


class UniversityDocumentLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path

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
                docs = self.load_file(file_path)
                all_documents.extend(docs)

        return all_documents
    

if __name__ == "__main__":
    # Example usage
    loader = UniversityDocumentLoader("data/raw_documents")
    documents = loader.load_all_documents()
    print(f"Loaded {len(documents)} documents.")
    # write the documents to a file for testing
    with open("loaded_documents.txt", "w") as f:
        for doc in documents:
            f.write(f"{doc.page_content}\n\n")

        