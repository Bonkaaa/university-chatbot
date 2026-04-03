import hashlib
from langchain_core.documents import Document

def convert_to_ranked_results(docs: list[Document]):
    ranked_results = []
    for doc in docs:
        doc_id = _get_doc_id(doc)
        
        ranked_results.append(
            (doc_id, doc.page_content, doc)
        )
    return ranked_results
    

def _get_doc_id(doc):
    text = doc.page_content
    int_id = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    return str(int_id)

