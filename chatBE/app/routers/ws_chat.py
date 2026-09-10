import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import ConversationParticipant, Message
from ..auth import decode_access_token
from ..ws.manager import manager

router = APIRouter()


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(...),
):
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001)
        return

    user_id = payload.get("sub")
    if user_id is None:
        await websocket.close(code=4001)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ConversationParticipant).where(
                ConversationParticipant.conversation_id == conversation_id,
                ConversationParticipant.user_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            await websocket.close(code=4003)
            return

    await manager.connect(conversation_id, websocket)

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)

            if data.get("type") == "ping":
                continue  # heartbeat only, not a real message

            content = data.get("content")
            if not content:
                continue

            async with AsyncSessionLocal() as db:
                new_message = Message(
                    conversation_id=conversation_id,
                    sender_id=user_id,
                    content=content,
                )
                db.add(new_message)
                await db.commit()
                await db.refresh(new_message)

            await manager.broadcast(
                conversation_id,
                {
                    "id": new_message.id,
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": content,
                    "created_at": new_message.created_at.isoformat(),
                },
                exclude=websocket,
            )

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)