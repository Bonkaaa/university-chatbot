from sqlalchemy.orm import Session
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