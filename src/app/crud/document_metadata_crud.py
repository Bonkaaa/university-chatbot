from sqlalchemy.orm import Session
from ..models import DocumentMetadata
import uuid
from typing import Optional
from sqlalchemy import or_


def create_document_metadata(db: Session, title: str, file_name: str, file_type: str, file_size: int, uploaded_by: int, id: Optional[uuid.UUID] = None) -> DocumentMetadata:
    doc_id = id or uuid.uuid4()
    new_metadata = DocumentMetadata(
        id=doc_id,
        title=title,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        uploaded_by=uploaded_by
    )
    db.add(new_metadata)
    db.commit()
    db.refresh(new_metadata)
    return new_metadata


def get_number_of_documents(db: Session, include_deleted: bool = False) -> int:
    q = db.query(DocumentMetadata)
    if not include_deleted:
        q = q.filter(DocumentMetadata.is_deleted == 0)
    return q.count()


def list_document_metadata(db: Session, query: str = "", include_deleted: bool = False) -> list[DocumentMetadata]:
    q = db.query(DocumentMetadata)
    if not include_deleted:
        q = q.filter(DocumentMetadata.is_deleted == 0)
    if query.strip():
        like = f"%{query.strip()}%"
        q = q.filter(or_(DocumentMetadata.title.ilike(like), DocumentMetadata.file_name.ilike(like)))
    return q.order_by(DocumentMetadata.uploaded_at.desc()).all()


def get_document_metadata_by_id(db: Session, doc_id: str) -> Optional[DocumentMetadata]:
    try:
        parsed_doc_id = uuid.UUID(str(doc_id))
    except (TypeError, ValueError, AttributeError):
        return None
    return db.query(DocumentMetadata).filter(DocumentMetadata.id == parsed_doc_id).first()

def remove_document_metadata(db: Session, metadata: DocumentMetadata) -> DocumentMetadata:
    metadata.is_deleted = 1
    db.commit()
    db.refresh(metadata)
    return metadata

def get_total_documents_uploaded_today(db: Session) -> int:
    from datetime import datetime, timedelta
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)
    return db.query(DocumentMetadata).filter(DocumentMetadata.uploaded_at >= today_start, DocumentMetadata.uploaded_at < today_end).count()
