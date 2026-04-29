from sqlalchemy.orm import Session
from ..models import User
import uuid

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password_hash: str, display_name: str) -> User:
    id = uuid.uuid4()
    new_user = User(id=id, email=email, password_hash=password_hash, display_name=display_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_id(db: Session, user_id: uuid.UUID) -> User:
    return db.query(User).filter(User.id == user_id).first()

def update_user(db: Session, user: User, display_name: str = None, password_hash: str = None) -> User:
    if display_name is not None:
        user.display_name = display_name
    if password_hash is not None:
        user.password_hash = password_hash
    db.commit()
    db.refresh(user)
    return user