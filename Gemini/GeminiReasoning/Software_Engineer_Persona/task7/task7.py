import sqlite3
import uuid
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from urllib.parse import urlparse
import time

# --- Database Setup ---
DATABASE_NAME = 'ecommerce.db'
SESSION_DURATION_SECONDS = 3600  # Example: 1 hour

def create_tables():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS sessions")
    
    # Create users table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real application, use proper hashing
        )
    ''')

    # Create sessions table to store session tokens and expiry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Add a default user for testing
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ('testuser', 'password123'))

    conn.commit()
    conn.close()

create_tables()

# --- Session Management Functions ---

def generate_session_token():
    return str(uuid.uuid4())

def create_session(user_id, expiration_seconds=SESSION_DURATION_SECONDS):
    session_token = generate_session_token()
    now = datetime.now()
    expires_at = now + timedelta(seconds=expiration_seconds)
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sessions (session_token, user_id, expires_at) VALUES (?, ?, ?)",
                   (session_token, user_id, expires_at))
    conn.commit()
    conn.close()
    return session_token, expiration_seconds

def get_session_data(session_token):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expires_at FROM sessions WHERE session_token = ?", (session_token,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'user_id': result[0], 'expires_at': datetime.fromisoformat(result[1])}
    return None

def delete_session(session_token):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE session_token = ?", (session_token,))
    conn.commit()
    conn.close()

def delete_existing_sessions_for_user(user_id):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- Login and Validation Logic ---

def login_user(username, password, current_domain, expiration_seconds=SESSION_DURATION_SECONDS):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id = user[0]
        # Invalidate any existing sessions for this user
        delete_existing_sessions_for_user(user_id)

        session_token, cookie_max_age = create_session(user_id, expiration_seconds)
        # Create a cookie
        cookie = SimpleCookie()
        cookie['session_token'] = session_token
        cookie['session_token']['domain'] = current_domain
        cookie['session_token']['path'] = '/'
        cookie['session_token']['httponly'] = True
        cookie['session_token']['samesite'] = 'Strict'
        cookie['session_token']['max-age'] = cookie_max_age  # Set the expiration time in seconds

        return {
            'success': True,
            'user_id': user_id,
            'cookie_header': cookie.output(header='')
        }
    else:
        return {'success': False, 'error': 'Invalid credentials'}

def validate_session_cookie(cookie_header, current_domain):
    if not cookie_header:
        return None

    try:
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        session_token = cookies.get('session_token')
        if session_token:
            session_token_value = session_token.value
            session_data = get_session_data(session_token_value)
            if session_data:
                if datetime.now() < session_data['expires_at']:
                    return session_data['user_id']
                else:
                    # Session has expired, delete it
                    delete_session(session_token_value)
                    return None
    except Exception as e:
        print(f"Error parsing cookie: {e}")
        return None

    return None

# --- Testing the Functionality ---

def simulate_login(username, password, domain, expiration=SESSION_DURATION_SECONDS):
    print(f"\n--- Simulating Login for user: {username} on domain: {domain} with {expiration}s expiry ---")
    login_result = login_user(username, password, domain, expiration)
    if login_result['success']:
        print(f"Login successful. User ID: {login_result['user_id']}")
        print(f"Set-Cookie header: {login_result['cookie_header']}")
        return login_result['cookie_header']
    else:
        print(f"Login failed: {login_result['error']}")
        return None

def simulate_protected_access(cookie_header, domain):
    print(f"\n--- Simulating Access to Protected Resource on domain: {domain} ---")
    user_id = validate_session_cookie(cookie_header, domain)
    if user_id:
        print(f"Session validated. User ID: {user_id} is authenticated.")
    else:
        print("Session validation failed. User is not authenticated.")

def simulate_protected_access_from_subdomain(cookie_header, subdomain):
    print(f"\n--- Simulating Access from Subdomain: {subdomain} ---")
    user_id = validate_session_cookie(cookie_header, subdomain)
    if user_id:
        print(f"Session validated (unexpected for subdomain). User ID: {user_id} is authenticated.")
    else:
        print("Session validation failed (expected for subdomain). User is not authenticated.")

def wait_and_simulate_access(cookie_header, domain, wait_seconds):
    print(f"\n--- Waiting for {wait_seconds} seconds before simulating access ---")
    time.sleep(wait_seconds)
    simulate_protected_access(cookie_header, domain)

if __name__ == "__main__":
    current_domain = "example.com"
    subdomain = "sub.example.com"
    short_expiry = 5  # seconds for testing expiry

    # 1. Simulate a successful login
    login_cookie_1 = simulate_login("testuser", "password123", current_domain)

    if login_cookie_1:
        print("\n--- Simulating accessing protected resource after first login ---")
        simulate_protected_access(login_cookie_1, current_domain)

        # 2. Simulate a second login with the same user
        login_cookie_2 = simulate_login("testuser", "password123", current_domain)

        if login_cookie_2:
            print("\n--- Simulating accessing protected resource after second login (using new cookie) ---")
            simulate_protected_access(login_cookie_2, current_domain)

            print("\n--- Simulating accessing protected resource using the cookie from the first login (should fail) ---")
            simulate_protected_access(login_cookie_1, current_domain) # This should now fail

    print("\n--- Testing other scenarios ---")
    # 3. Simulate login with short expiry and test expiration
    login_cookie_short = simulate_login("testuser", "password123", current_domain, short_expiry)

    if login_cookie_short:
        print("\n--- Simulating accessing protected resource with short expiry ---")
        simulate_protected_access(login_cookie_short, current_domain)
        wait_and_simulate_access(login_cookie_short, current_domain, short_expiry + 1)
        simulate_protected_access(login_cookie_short, current_domain)

    # 4. Simulate accessing from subdomain (should fail)
    if login_cookie_1:
        simulate_protected_access_from_subdomain(login_cookie_1, subdomain)

    # 5. Simulate accessing with no cookie
    simulate_protected_access(None, current_domain)

    # 6. Simulate accessing with an invalid cookie
    invalid_cookie = "session_token=invalid_token"
    simulate_protected_access(invalid_cookie, current_domain)