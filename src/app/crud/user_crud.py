from sqlalchemy.orm import Session
from ..models import User

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password_hash: str, display_name: str) -> User:
    new_user = User(email=email, password_hash=password_hash, display_name=display_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user_by_id(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()