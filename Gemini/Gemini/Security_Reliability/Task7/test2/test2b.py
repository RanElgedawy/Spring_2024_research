import secrets
import jwt
from datetime import datetime, timedelta

# ... (other imports)

def create_session(user_id):
    session_id = secrets.token_urlsafe(32)
    data = {
        "user_id": user_id,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    expires_at = datetime.utcnow() + timedelta(days=1)  # Adjust expiration time as needed
    data["expires_at"] = expires_at.strftime("%Y-%m-%d %H:%M:%S")

    # Store session data in the database
    cursor.execute("INSERT INTO sessions (session_id, user_id, created_at, expires_at, data) VALUES (?, ?, ?, ?, ?)",
                   (session_id, user_id, data["created_at"], data["expires_at"], json.dumps(data)))
    connection.commit()

    # Set the secure cookie
    response.set_cookie("session_id", session_id, secure=True, httponly=True, samesite="Lax")
    return session_id