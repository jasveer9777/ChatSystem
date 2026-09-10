from datetime import datetime
from pydantic import BaseModel, EmailStr


from typing import List

class AccountDeleteRequest(BaseModel):
    password: str

class ConversationCreate(BaseModel):
    participant_ids: List[str]   # user IDs to add to the conversation
    name: str | None = None       # optional, mainly for group chats
    is_group: bool = False


class MessageCreate(BaseModel):
    content: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: str
    name: str | None
    is_group: str
    created_at: datetime

    class Config:
        from_attributes = True