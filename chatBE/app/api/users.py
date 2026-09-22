from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user, security
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_SECRET
from app.database import SessionLocal
from app.models import RevokedToken, User
from app.schemas import UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password before storing it in the database."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether a plain-text password matches the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(username: str, user_id: int) -> str:
    """Create a JWT token that represents a valid login session."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "username": username, "exp": expire, "jti": str(uuid4())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)



@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate) -> User:
    db: Session = SessionLocal()

    try:
        existing_user = db.query(User).filter(
            (User.username == user.username) | (User.email == user.email)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists",
            )

        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hash_password(user.password),
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )
    finally:
        db.close()


@router.post("/login")
def login_user(user: UserLogin) -> dict[str, str]:
    db: Session = SessionLocal()

    try:
        db_user = db.query(User).filter(User.username == user.username).first()

        if not db_user or not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        token = create_access_token(db_user.username, db_user.id)
        return {"access_token": token, "token_type": "bearer"}
    finally:
        db.close()


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout")
def logout_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    jti = payload["jti"]
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    db: Session = SessionLocal()
    try:
        if not db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
            db.add(RevokedToken(jti=jti, expires_at=expires_at))
            db.commit()
    finally:
        db.close()

    return {"detail": "Logged out"}


@router.get("/", response_model=list[UserRead])
def list_users() -> list[User]:
    db: Session = SessionLocal()
    try:
        users = db.query(User).all()
        return users
    finally:
        db.close()
