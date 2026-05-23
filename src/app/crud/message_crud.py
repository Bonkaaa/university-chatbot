from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import Message
from datetime import datetime, timedelta

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

def list_assistant_messages(db: Session, conversation_id: int):
    # return (
    #     db.query(Message)
    #     .filter(Message.conversation_id == conversation_id)
    #     .order_by(Message.sequence_no.asc())
    #     .all()
    # )
    
    # Get assistant message 
    assistant_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id, Message.role == 'assistant')
        .order_by(Message.sequence_no.asc())
        .all()
    )
    return assistant_messages


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

def get_messages_by_hour_today(db: Session) -> list[dict[str, int]]:
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)

    messages_by_hour = (
        db.query(
            func.extract('hour', Message.created_at).label('hour'),
            func.count(Message.id).label('count')
        )
        .filter(Message.created_at >= today_start, Message.created_at < today_end)
        .group_by(func.extract('hour', Message.created_at))
        .order_by(func.extract('hour', Message.created_at))
        .all()
    )

    # Convert to a dictionary with hour as key and message_count as value
    return [{ "hour": int(hour), "count": count } for hour, count in messages_by_hour]

def get_total_messages_today(db: Session) -> int:
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)

    total_messages = (
        db.query(func.count(Message.id))
        .filter(Message.created_at >= today_start, Message.created_at < today_end)
        .scalar()
    )

    return total_messages or 0