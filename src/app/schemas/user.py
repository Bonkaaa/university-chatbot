from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str | None = None
    is_active: bool

    class Config:
        from_attributes = True