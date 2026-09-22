"""Standalone script to delete a user (and their messages) by username.

Usage:
    python scripts/delete_user.py <username>
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models import Message, User


def delete_user(username: str) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            print(f"No user found with username '{username}'")
            return

        user_id = user.id

        # remove messages first since they reference the user via foreign keys
        db.query(Message).filter(
            (Message.sender_id == user_id) | (Message.receiver_id == user_id)
        ).delete(synchronize_session=False)

        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        db.commit()
        print(f"Deleted user '{username}' (id={user_id}) and their messages")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/delete_user.py <username>")
        sys.exit(1)

    delete_user(sys.argv[1])
