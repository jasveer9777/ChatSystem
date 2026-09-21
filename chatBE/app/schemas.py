from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Request payload for creating a new user."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Request payload for login."""

    username: str
    password: str


class UserRead(BaseModel):
    """Response payload returned to clients after user creation or lookup."""

    id: int
    username: str
    email: EmailStr

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Request payload for sending a private message."""

    receiver_id: int
    content: str = Field(..., min_length=1, max_length=2000)


class MessageRead(BaseModel):
    """Response payload for a message returned to the client."""

    id: int
    sender_id: int
    receiver_id: int
    content: str

    model_config = {"from_attributes": True}
