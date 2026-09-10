import sqlite3

USERNAME_OR_EMAIL = "alice"  # <-- change this

conn = sqlite3.connect("chat.db")
cursor = conn.cursor()

# Find the user
cursor.execute(
    "SELECT id, username, email FROM users WHERE username = ? OR email = ?",
    (USERNAME_OR_EMAIL, USERNAME_OR_EMAIL),
)
user = cursor.fetchone()

if not user:
    print(f"No user found matching '{USERNAME_OR_EMAIL}'")
else:
    user_id, username, email = user
    print(f"Deleting user: {username} ({email}) [{user_id}]")

    # Find conversations this user is part of
    cursor.execute(
        "SELECT conversation_id FROM conversation_participants WHERE user_id = ?",
        (user_id,),
    )
    conversation_ids = [row[0] for row in cursor.fetchall()]

    # Remove this user's participant rows
    cursor.execute(
        "DELETE FROM conversation_participants WHERE user_id = ?", (user_id,)
    )

    # For each conversation, if now empty of participants, delete it + its messages
    for convo_id in conversation_ids:
        cursor.execute(
            "SELECT COUNT(*) FROM conversation_participants WHERE conversation_id = ?",
            (convo_id,),
        )
        remaining = cursor.fetchone()[0]
        if remaining == 0:
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (convo_id,))
            cursor.execute("DELETE FROM conversations WHERE id = ?", (convo_id,))
            print(f"  Also deleted now-empty conversation {convo_id}")

    # Delete the user
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    print("Done.")

conn.close()