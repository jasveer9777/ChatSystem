from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User, Conversation, ConversationParticipant, Message
from ..schemas import MessageCreate, MessageOut
from ..auth import get_current_user

router = APIRouter(prefix="/conversations/{conversation_id}/messages", tags=["messages"])


async def _ensure_participant(conversation_id: str, user_id: str, db: AsyncSession):
    """Raise 404 if the user isn't a participant of this conversation."""
    result = await db.execute(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you're not a participant",
        )


@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_participant(conversation_id, current_user.id, db)

    new_message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=message_in.content,
    )
    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)
    return new_message


@router.get("/", response_model=list[MessageOut])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    before: str | None = None,  # message ID to paginate backwards from (optional, for later)
):
    await _ensure_participant(conversation_id, current_user.id, db)

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    return list(reversed(messages))  # oldest-first for natural chat display