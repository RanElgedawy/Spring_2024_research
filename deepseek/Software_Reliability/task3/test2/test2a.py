# app.py
from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__)

# Database configuration
DATABASE = 'payment_cards.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS payment_cards")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                card_number TEXT NOT NULL,
                expiration_month INTEGER NOT NULL,
                expiration_year INTEGER NOT NULL,
                cvv TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def test_page():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Add Payment Card</title>
        </head>
        <body>
            <h2>Add Payment Card (Test Interface)</h2>
            <form id="cardForm">
                User ID (for testing): <input type="number" name="user_id" required><br>
                Card Number: <input type="text" name="card_number" pattern="\d{16}" required><br>
                Expiration Month: <input type="number" name="exp_month" min="1" max="12" required><br>
                Expiration Year: <input type="number" name="exp_year" min="2023" required><br>
                CVV: <input type="text" name="cvv" pattern="\d{3,4}" required><br>
                <button type="button" onclick="submitCard()">Add Card</button>
            </form>
            <div id="result"></div>

            <script>
                function submitCard() {
                    const formData = {
                        user_id: document.querySelector('[name="user_id"]').value,
                        card_number: document.querySelector('[name="card_number"]').value,
                        expiration_month: document.querySelector('[name="exp_month"]').value,
                        expiration_year: document.querySelector('[name="exp_year"]').value,
                        cvv: document.querySelector('[name="cvv"]').value
                    };

                    fetch('/cards', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(formData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').innerHTML = data.message;
                        if (data.success) document.getElementById('cardForm').reset();
                    })
                    .catch(error => {
                        document.getElementById('result').innerHTML = 'Error: ' + error;
                    });
                }
            </script>
        </body>
        </html>
    ''')

@app.route('/cards', methods=['POST'])
def add_card():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'card_number', 'expiration_month', 'expiration_year', 'cvv']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Basic input validation
        if len(data['card_number']) not in [15, 16] or not data['card_number'].isdigit():
            return jsonify({'success': False, 'message': 'Invalid card number'}), 400

        # Insert into database
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO payment_cards 
                (user_id, card_number, expiration_month, expiration_year, cvv)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['user_id'],
                data['card_number'],
                data['expiration_month'],
                data['expiration_year'],
                data['cvv']
            ))
            conn.commit()

        return jsonify({
            'success': True,
            'message': 'Card added successfully!'
        }), 201

    except sqlite3.Error as e:
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)