from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..models import Conversation

def create_conversation(db: Session, user_id: int, title: str = None) -> Conversation:
    new_conversation = Conversation(user_id=user_id, title=title)
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation

def get_conversation_by_id(db: Session, conversation_id: int) -> Conversation:
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()

def list_conversations_for_user(db: Session, user_id: int) -> list[Conversation]:
    return db.query(Conversation).filter(Conversation.user_id == user_id).all()

def get_number_of_conversations(db: Session) -> int:
    return db.query(Conversation).count()

def get_total_conversations_today(db: Session) -> int:
    today_start = datetime.combine(datetime.today(), datetime.min.time())
    today_end = today_start + timedelta(days=1)
    return db.query(Conversation).filter(Conversation.created_at >= today_start, Conversation.created_at < today_end).count()