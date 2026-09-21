from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import SessionLocal
from app.models import Message

router = APIRouter(prefix="/ws", tags=["websocket"])

active_connections: dict[int, WebSocket] = {}


@router.websocket("/chat/{user_id}")
async def chat_websocket(websocket: WebSocket, user_id: int) -> None:
    await websocket.accept()
    active_connections[user_id] = websocket

    try:
        while True:
            raw_data = await websocket.receive_text()

            try:
                payload = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "invalid JSON payload"})
                continue

            receiver_id = payload.get("receiver_id")
            content = payload.get("content")

            if receiver_id is None or content is None:
                await websocket.send_json({"error": "receiver_id and content are required"})
                continue

            db = SessionLocal()
            try:
                message = Message(sender_id=user_id, receiver_id=receiver_id, content=content)
                db.add(message)
                db.commit()
                db.refresh(message)
            finally:
                db.close()

            message_payload = {
                "message_id": message.id,
                "sender_id": user_id,
                "receiver_id": receiver_id,
                "content": content,
            }

            if receiver_id in active_connections:
                await active_connections[receiver_id].send_json(message_payload)

            await websocket.send_json(message_payload)
    except WebSocketDisconnect:
        active_connections.pop(user_id, None)
