from pydantic import BaseModel

class ConversationCreate(BaseModel):
    title: str | None = None

class ConversationOut(BaseModel):
    id: int
    user_id: int
    title: str | None = None

    class Config:
        from_attributes = True