from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import SessionLocal
from app.models import Message, User
from app.schemas import MessageCreate, MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
) -> Message:
    db: Session = SessionLocal()
    try:
        receiver = db.query(User).filter(User.id == message.receiver_id).first()
        if receiver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Receiver not found",
            )

        new_message = Message(
            sender_id=current_user.id,
            receiver_id=message.receiver_id,
            content=message.content,
        )
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return new_message
    finally:
        db.close()


@router.get("/{other_user_id}", response_model=list[MessageRead])
def get_conversation(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
) -> list[Message]:
    db: Session = SessionLocal()
    try:
        # messages sent by either side of this specific 1:1 conversation
        conversation = (
            db.query(Message)
            .filter(
                or_(
                    and_(Message.sender_id == current_user.id, Message.receiver_id == other_user_id),
                    and_(Message.sender_id == other_user_id, Message.receiver_id == current_user.id),
                )
            )
            .order_by(Message.created_at.asc())
            .all()
        )
        return conversation
    finally:
        db.close()
