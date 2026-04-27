from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from ..db import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=False)  # system/user/assistant/tool
    content = Column(Text, nullable=False)
    sequence_no = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

