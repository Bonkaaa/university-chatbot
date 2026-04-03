from langchain_text_splitters import RecursiveCharacterTextSplitter

from .document_loaders import UniversityDocumentLoader

def create_splitter(chunk_size, chunk_overlap) -> RecursiveCharacterTextSplitter:
    separators=[
            "\n\n",
            "\n",
            r"\n\d+\.\s",  # đôi khi khoản "1. ... 2. ..."
            ". ",
            "! ",
            "? ",
            "; ",
            ": ",
            ", ",
            " ",
            "",
        ]
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        separators=separators
    )

if __name__ == "__main__":
    # Example usage
    loader = UniversityDocumentLoader("data/raw_documents")
    docs = loader.load_all_documents()

    text_splitter = create_splitter(chunk_size=500, chunk_overlap=50)
    split_docs = text_splitter.split_documents(docs)

    # Save split_docs to a file for inspection
    with open("split_docs.txt", "w", encoding="utf-8") as f:
        for i, doc in enumerate(split_docs):
            f.write(f"--- Document {i+1} ---\n")
            f.write(doc.page_content + "\n\n")