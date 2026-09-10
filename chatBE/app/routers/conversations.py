from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import User, Conversation, ConversationParticipant
from ..schemas import ConversationCreate, ConversationOut
from ..auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    convo_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Combine creator + given participant_ids, dedupe
    all_participant_ids = set(convo_in.participant_ids) | {current_user.id}

    # Validate all participant user IDs actually exist
    result = await db.execute(select(User).where(User.id.in_(all_participant_ids)))
    found_users = result.scalars().all()
    if len(found_users) != len(all_participant_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more participant_ids do not exist",
        )

    new_convo = Conversation(
        name=convo_in.name,
        is_group="true" if convo_in.is_group else "false",
    )
    db.add(new_convo)
    await db.flush()  # get new_convo.id without committing yet

    for user_id in all_participant_ids:
        db.add(ConversationParticipant(conversation_id=new_convo.id, user_id=user_id))

    await db.commit()
    await db.refresh(new_convo)
    return new_convo


@router.get("/", response_model=list[ConversationOut])
async def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Ensure the current user is a participant before returning anything
    result = await db.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(
            Conversation.id == conversation_id,
            ConversationParticipant.user_id == current_user.id,
        )
    )
    convo = result.scalar_one_or_none()
    if not convo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or you're not a participant",
        )
    return convo