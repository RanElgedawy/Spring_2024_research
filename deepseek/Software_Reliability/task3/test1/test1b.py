from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this in production!
DATABASE = 'ecommerce.db'

# Security Note: This is a simplified example. In production:
# - Never store raw card data (use payment gateways like Stripe)
# - Use HTTPS
# - Implement proper authentication
# - Follow PCI DSS compliance standards

def init_db():
    with app.app_context():
        conn = sqlite3.connect(DATABASE)
        # Create users table (simplified)
        conn.execute("DROP TABLE IF EXISTS users")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create payment_cards table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                expiration TEXT NOT NULL,
                cvv TEXT NOT NULL,
                nickname TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        # Add test user if not exists
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                        ('testuser', 'testpass'))
        except sqlite3.IntegrityError:
            pass
        conn.commit()

@app.route('/test-login')
def test_login():
    """Simulate login for testing purposes"""
    session['user_id'] = 1  # testuser's ID
    return redirect(url_for('add_card'))

@app.route('/add-card', methods=['GET'])
def add_card():
    if 'user_id' not in session:
        return redirect(url_for('test_login'))  # Redirect to login in real implementation
    return render_template('add_card2.html')

@app.route('/api/add-card', methods=['POST'])
def api_add_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    required_fields = ['card_number', 'expiration', 'cvv']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields'}), 400

    try:
        conn = sqlite3.connect(DATABASE)
        conn.execute('''
            INSERT INTO payment_cards (user_id, card_number, expiration, cvv, nickname)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data['card_number'],
            data['expiration'],
            data['cvv'],
            data.get('nickname', '')
        ))
        conn.commit()
        return jsonify({'message': 'Card added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/cards')
def view_cards():
    """Testing endpoint - disable in production!"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = sqlite3.connect(DATABASE)
    cur = conn.execute('''
        SELECT id, card_number, expiration, cvv, nickname
        FROM payment_cards
        WHERE user_id = ?
    ''', (session['user_id'],))
    cards = [dict(row) for row in cur.fetchall()]
    return jsonify(cards)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)