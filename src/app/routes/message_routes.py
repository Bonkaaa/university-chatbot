from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..core import get_current_user
from ..models import User, Conversation
from ..schemas import MessageCreate, MessageOut
from ..crud import create_message, list_messages

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["Messages"])

@router.post("/", response_model=MessageOut)
def add_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not conv:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    
    uid = user.id if payload.role == "user" else None
    return create_message(db, conversation_id, uid, payload.role, payload.content)

@router.post("/", response_model=list[MessageOut])
def get_messages(
    conversation_id: int, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
    if not conv:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
    return list_messages(db, conversation_id)
