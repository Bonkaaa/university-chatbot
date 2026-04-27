from pydantic import BaseModel

class MessageCreate(BaseModel):
    role: str
    content: str

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    user_id: int | None
    role: str
    content: str
    sequence_no: int

    class Config:
        from_attributes = True