import sqlite3
import uuid
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
DATABASE = 'newsletter_subscriptions.db'

# Configure the server name for generating external URLs
app.config['SERVER_NAME'] = 'localhost:5000'
app.config['PREFERRED_URL_SCHEME'] = 'http'

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS newsletter_subscriptions")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real application, use proper hashing
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
            user_id INTEGER PRIMARY KEY,
            subscribed BOOLEAN NOT NULL DEFAULT 1,
            unsubscribe_reason TEXT,
            unsubscribe_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            unsubscribe_token TEXT UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the application starts
with app.app_context():
    init_db()

# --- User Authentication Simulation (for testing purposes) ---
CURRENT_LOGGED_IN_USER_ID = None

def set_logged_in_user(user_id):
    global CURRENT_LOGGED_IN_USER_ID
    CURRENT_LOGGED_IN_USER_ID = user_id

def get_logged_in_user_id():
    return CURRENT_LOGGED_IN_USER_ID

# --- Database Helper Functions ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

def create_user(email, password):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        user_id = cursor.lastrowid
        unsubscribe_token = str(uuid.uuid4())
        cursor.execute("INSERT INTO newsletter_subscriptions (user_id, unsubscribe_token) VALUES (?, ?)", (user_id, unsubscribe_token))
        conn.commit()
        return user_id, unsubscribe_token
    except sqlite3.IntegrityError:
        return None, None  # Email already exists
    finally:
        conn.close()

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def get_subscription_status(user_id):
    conn = get_db()
    cursor = conn.cursor()
    subscription = cursor.execute("SELECT subscribed, unsubscribe_reason, unsubscribe_token FROM newsletter_subscriptions WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return subscription

def unsubscribe_user(user_id, reason=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE newsletter_subscriptions SET subscribed = 0, unsubscribe_reason = ?, unsubscribe_timestamp = CURRENT_TIMESTAMP WHERE user_id = ?",
        (reason, user_id)
    )
    conn.commit()
    conn.close()

def unsubscribe_user_by_token(token, reason=None):
    conn = get_db()
    cursor = conn.cursor()
    user_subscription = cursor.execute("SELECT user_id FROM newsletter_subscriptions WHERE unsubscribe_token = ?", (token,)).fetchone()
    if user_subscription:
        user_id = user_subscription['user_id']
        cursor.execute(
            "UPDATE newsletter_subscriptions SET subscribed = 0, unsubscribe_reason = ?, unsubscribe_timestamp = CURRENT_TIMESTAMP WHERE user_id = ?",
            (reason, user_id)
        )
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def unsubscribe_all():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE newsletter_subscriptions SET subscribed = 0, unsubscribe_reason = 'Unsubscribed via Unsubscribe All', unsubscribe_timestamp = CURRENT_TIMESTAMP"
    )
    conn.commit()
    conn.close()

def get_unsubscribe_link(user_id):
    subscription = get_subscription_status(user_id)
    if subscription and subscription['unsubscribe_token']:
        return url_for('unsubscribe_with_token', token=subscription['unsubscribe_token'], _external=True)
    return None

# --- Web Routes ---
@app.route('/')
def index():
    logged_in_user_id = get_logged_in_user_id()
    if logged_in_user_id:
        user = get_user_by_id(logged_in_user_id)
        subscription_status = get_subscription_status(logged_in_user_id)
        unsubscribe_link = get_unsubscribe_link(logged_in_user_id)
        return render_template('dashboard.html', user=user, subscription=subscription_status, unsubscribe_link=unsubscribe_link)
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    conn = get_db()
    cursor = conn.cursor()
    user = cursor.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
    conn.close()
    if user:
        set_logged_in_user(user['id'])
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error="Invalid credentials")

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    logged_in_user_id = get_logged_in_user_id()
    if not logged_in_user_id:
        return "Error: Not logged in."

    user = get_user_by_id(logged_in_user_id)
    if not user:
        return "Error: User not found."

    if request.method == 'POST':
        reason = request.form.get('reason')
        unsubscribe_user(logged_in_user_id, reason)
        return render_template('unsubscribed.html', user=user)

    return render_template('unsubscribe_form.html', user=user)

@app.route('/unsubscribe_all')
def unsubscribe_all_route():
    # Consider if this action should be restricted to certain user roles (e.g., administrators)
    logged_in_user_id = get_logged_in_user_id()
    if not logged_in_user_id:
        return "Error: Not logged in." # Or redirect to login with a message

    unsubscribe_all()
    return redirect(url_for('index')) # Redirect back to the dashboard with a message

@app.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe_with_token(token):
    unsubscribed = False
    user_email = None
    if request.method == 'POST':
        reason = request.form.get('reason')
        unsubscribed = unsubscribe_user_by_token(token, reason)
        if unsubscribed:
            conn = get_db()
            cursor = conn.cursor()
            user_data = cursor.execute("SELECT u.email FROM users u JOIN newsletter_subscriptions ns ON u.id = ns.user_id WHERE ns.unsubscribe_token = ?", (token,)).fetchone()
            if user_data:
                user_email = user_data['email']
            conn.close()
            return render_template('unsubscribed_via_link.html', user_email=user_email)
        else:
            return render_template('unsubscribe_failed.html')
    else:
        conn = get_db()
        cursor = conn.cursor()
        user_data = cursor.execute("SELECT u.email FROM users u JOIN newsletter_subscriptions ns ON u.id = ns.user_id WHERE ns.unsubscribe_token = ?", (token,)).fetchone()
        conn.close()
        if user_data:
            return render_template('unsubscribe_form_via_link.html', token=token, user_email=user_data['email'])
        else:
            return render_template('unsubscribe_failed.html')

@app.route('/logout')
def logout():
    set_logged_in_user(None)
    return redirect(url_for('index'))

# --- Test Functions ---
def test_unsubscribe_functionality():
    # 1. Create a test user
    test_email = "test@example.com"
    test_password = "password123"
    user_id, unsubscribe_token = create_user(test_email, test_password)
    assert user_id is not None, f"Failed to create test user with email: {test_email}"
    assert unsubscribe_token is not None, "Failed to generate unsubscribe token"

    # 2. Simulate user login
    set_logged_in_user(user_id)
    assert get_logged_in_user_id() == user_id, "Failed to simulate user login"

    # 3. Verify initial subscription status and token
    subscription_status = get_subscription_status(user_id)
    assert subscription_status is not None and subscription_status['subscribed'] == 1, "Initial subscription status is incorrect"
    assert subscription_status['unsubscribe_token'] == unsubscribe_token, "Unsubscribe token in DB does not match generated token"

    # 4. Get the unsubscribe link
    with app.app_context():  # Activate application context
        unsubscribe_link = get_unsubscribe_link(user_id)
        assert unsubscribe_link is not None and unsubscribe_token in unsubscribe_link, "Unsubscribe link is incorrect"
        print(f"Generated Unsubscribe Link for testing: {unsubscribe_link}") # For debugging

    # 5. Unsubscribe the user using the token
    unsubscribe_reason = "No longer interested via link"
    unsubscribed_by_token = unsubscribe_user_by_token(unsubscribe_token, unsubscribe_reason)
    assert unsubscribed_by_token is True, "Failed to unsubscribe user using the token"

    # 6. Verify the updated subscription status
    updated_subscription_status = get_subscription_status(user_id)
    assert updated_subscription_status is not None and updated_subscription_status['subscribed'] == 0, "Failed to unsubscribe the user via token"
    assert updated_subscription_status['unsubscribe_reason'] == unsubscribe_reason, "Unsubscribe reason via token was not saved correctly"

    print("Unsubscribe functionality with unique link test completed successfully!")

def test_unsubscribe_all_functionality():
    # 1. Create multiple test users
    user_ids =[]
    for i in range(3):
        test_email = f"test_all_{i}@example.com"
        test_password = f"password_all_{i}"
        user_id, _ = create_user(test_email, test_password)
        assert user_id is not None, f"Failed to create test user with email: {test_email}"
        user_ids.append(user_id)

    # 2. Simulate login (optional, but good practice for testing route access)
    set_logged_in_user(user_ids[0]) # Log in as the first user

    # 3. Verify initial subscription status of all users
    for user_id in user_ids:
        subscription_status = get_subscription_status(user_id)
        assert subscription_status is not None and subscription_status['subscribed'] == 1, f"Initial subscription status is incorrect for user ID: {user_id}"

    # 4. Call the unsubscribe_all function
    unsubscribe_all()

    # 5. Verify the updated subscription status of all users
    for user_id in user_ids:
        updated_subscription_status = get_subscription_status(user_id)
        assert updated_subscription_status is not None and updated_subscription_status['subscribed'] == 0, f"Failed to unsubscribe user ID: {user_id} via unsubscribe_all"
        assert updated_subscription_status['unsubscribe_reason'] == 'Unsubscribed via Unsubscribe All', f"Unsubscribe reason incorrect for user ID: {user_id}"

    print("Unsubscribe All functionality test completed successfully for all users!")

def run_tests():
    init_db() # Ensure the database exists for testing
    with app.app_context(): # Activate application context for the entire test run
        test_unsubscribe_functionality()
        test_unsubscribe_all_functionality()

if __name__ == '__main__':
    run_tests()  # Run tests when the script is executed

    # Run the Flask development server
    app.run(debug=True)