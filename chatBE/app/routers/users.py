from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User, ConversationParticipant, Conversation, Message
from ..schemas import UserCreate, UserOut, UserLogin, Token, AccountDeleteRequest
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user.id})
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    payload: AccountDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    result = await db.execute(
        select(ConversationParticipant.conversation_id).where(
            ConversationParticipant.user_id == current_user.id
        )
    )
    conversation_ids = [row[0] for row in result.all()]

    await db.execute(
        ConversationParticipant.__table__.delete().where(
            ConversationParticipant.user_id == current_user.id
        )
    )

    for convo_id in conversation_ids:
        remaining = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == convo_id
            )
        )
        if remaining.scalar_one_or_none() is None:
            await db.execute(
                Message.__table__.delete().where(Message.conversation_id == convo_id)
            )
            await db.execute(
                Conversation.__table__.delete().where(Conversation.id == convo_id)
            )

    await db.execute(User.__table__.delete().where(User.id == current_user.id))
    await db.commit()