from sqlalchemy.orm import Session
from ..models import DocumentMetadata
import uuid

def create_document_metadata(db: Session, title: str, file_name: str, file_type: str, file_size: int, uploaded_by: int) -> DocumentMetadata:
    new_metadata = DocumentMetadata(
        id=uuid.uuid4(),
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