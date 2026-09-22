from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.api.messages import router as message_router
from app.api.users import router as user_router
from app.api.websocket import router as websocket_router


app = FastAPI(
    title="Chat System API",
    description="Backend API for a real-time chat application.",
    version="0.1.0",
)

# allows the Vite dev server (different origin/port) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","https://chatsystem-fe.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(message_router)
app.include_router(websocket_router)


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Chat System API is running"}
