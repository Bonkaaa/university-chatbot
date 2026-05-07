from sqlalchemy import Integer, Column, String, ForeignKey, UUID, DateTime
from sqlalchemy.sql import func
from ..db import Base

class DocumentMetadata(Base):
    __tablename__ = "document_metadata"

    id = Column(UUID, primary_key=True, index=True)
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)

    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    status = Column(String, default="uploaded", nullable=False)  # uploaded/processed/failed
    is_deleted = Column(Integer, default=0, nullable=False)  # 0: not deleted, 1: deleted
