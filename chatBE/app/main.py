from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    return {"message": "ChatSystem API is running"}

@app.get("/info")
async def info():
    return


# for demo 
# DATABASE_URL=sqlite+aiosqlite:///./chat.db

# SECRET_KEY=ad6b6f1ef765f7eddf0570f75ccabd34e26f9b84294c980a2f1fa13688a2d97b