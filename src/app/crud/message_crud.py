from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Message

def create_message(db: Session, conversation_id: int, user_id: int | None, role: str, content: str, response_time: int | None = None) -> Message:
    max_seq = db.query(func.max(Message.sequence_no)).filter(Message.conversation_id == conversation_id).scalar()
    next_seq = (max_seq or 0) + 1
    msg = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
        sequence_no=next_seq,
        response_time=response_time
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

# Calculate the average message of a conversation then return the average message of all conversations
def get_average_message_per_conversation(db: Session):
    message_counts_subquery = (
        db.query(
            Message.conversation_id,
            func.count(Message.id).label('message_count')
        )
        .group_by(Message.conversation_id)
        .subquery()
    )

    average = db.query(func.avg(message_counts_subquery.c.message_count)).scalar()
    
    return float(average) if average is not None else 0.0

# Calcute the average response time of all messages with role assistant
def get_average_response_time(db: Session):
    average = db.query(func.avg(Message.response_time)).filter(Message.role == 'assistant').scalar()
    return float(average) if average is not None else 0.0