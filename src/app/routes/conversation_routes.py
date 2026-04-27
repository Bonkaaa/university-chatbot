from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..core import get_current_user
from ..models import User
from ..schemas import ConversationCreate, ConversationOut
from ..crud import create_conversation, list_conversations_for_user as list_conversations

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("/", response_model=ConversationOut)
def add_conversation(payload: ConversationCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return create_conversation(db, user.id, payload.title)

@router.get("/", response_model=list[ConversationOut])
def get_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list_conversations(db, user.id)