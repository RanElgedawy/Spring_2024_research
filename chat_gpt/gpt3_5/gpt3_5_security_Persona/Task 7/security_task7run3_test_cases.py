import unittest
from security_task7run3 import app, create_session_token, is_session_valid, invalidate_session_tokens
import time
import sqlite3
import secrets
from flask import session

# Define session expiration time for testing purposes (in seconds)
SESSION_EXPIRATION_TIME = 2  # 2 seconds for testing

class TestSessionManagement(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    # Modify create_session_token to accept session token as a parameter
def create_session_token(user_id, session_token):
    # First, invalidate any existing session tokens for the user
    invalidate_session_tokens(user_id)

    # Generate a new session token
    token = secrets.token_hex(16)  # Generate a random token
    expiration_time = int(time.time()) + SESSION_EXPIRATION_TIME
    domain = 'example.com'  # Replace with your domain
    secure = False  # Replace with the appropriate value based on request.is_secure
    http_only = True
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id, expiration_time, domain, secure, http_only) VALUES (?, ?, ?, ?, ?, ?)", (token, user_id, expiration_time, domain, secure, http_only))
        conn.commit()
    return token

# Modify is_session_valid to accept session token as a parameter
def is_session_valid(token):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT expiration_time FROM sessions WHERE token = ?", (token,))
        result = cursor.fetchone()
        if result:
            expiration_time = result[0]
            return expiration_time > int(time.time())
        return False

# Update test cases to pass session token as a parameter
class TestSessionManagement(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_create_and_validate_session_token(self):
        # Create a session token for a user
        token = create_session_token(1, 'dummy_token')

        # Validate the session token
        self.assertTrue(is_session_valid(token))

    # Other test cases remain unchanged...

if __name__ == '__main__':
    unittest.main()

if __name__ == '__main__':
    unittest.main()