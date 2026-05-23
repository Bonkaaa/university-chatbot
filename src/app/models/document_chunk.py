from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy import UUID
from ..db import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(UUID, ForeignKey("document_metadata.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    source = Column(String, nullable=True)
    chuong = Column(String, nullable=True)
    dieu = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    external_vector_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
