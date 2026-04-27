from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Message

def create_message(db: Session, conversation_id: int, user_id: int | None, role: str, content: str):
    max_seq = db.query(func.max(Message.sequence_no)).filter(Message.conversation_id == conversation_id).scalar()
    next_seq = (max_seq or 0) + 1
    msg = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
        sequence_no=next_seq,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def list_messages(db: Session, conversation_id: int):
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.sequence_no.asc())
        .all()
    )