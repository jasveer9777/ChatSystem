from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from . import models  # noqa: F401 -- ensures models are registered with Base
from .routers import users, conversations, messages, ws_chat, user_list

app = FastAPI(title="Chat System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(messages.router)
app.include_router(ws_chat.router)
app.include_router(user_list.router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/")
async def root():
    return {"message": "Chat System API is running"}

from sqlalchemy import text


@app.get("/debug/tables")
async def debug_tables():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public';")
        )
        tables = [row[0] for row in result.fetchall()]
    return {"tables": tables}