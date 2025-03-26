# app.py
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key in production

DATABASE = 'ecommerce.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Create reviews table
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            review_score INTEGER NOT NULL CHECK (review_score BETWEEN 1 AND 5),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, product_id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('add_review'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # In a real application, verify credentials properly
        session['user_id'] = request.form['user_id']
        return redirect(url_for('add_review'))
    return render_template('login.html')

@app.route('/add-review', methods=['GET', 'POST'])
def add_review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    error = None
    success = None
    
    if request.method == 'POST':
        user_id = session['user_id']
        product_id = request.form['product_id']
        review_text = request.form['review_text']
        review_score = request.form['review_score']
        
        try:
            review_score = int(review_score)
            if not (1 <= review_score <= 5):
                raise ValueError()
        except ValueError:
            error = 'Please enter a valid rating between 1 and 5'
            return render_template('add_review.html', error=error)
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        try:
            c.execute('''
                INSERT INTO reviews (user_id,