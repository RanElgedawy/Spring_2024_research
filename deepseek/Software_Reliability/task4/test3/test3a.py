from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'ecommerce.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        db = get_db()
        
        # Create products table
        db.execute("DROP TABLE IF EXISTS products")
        db.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock INTEGER NOT NULL
            )
        ''')

        # Create virtual table for full-text search
        db.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS product_search 
            USING fts5(name, description, content='products', content_rowid='id')
        ''')

        # Create triggers to maintain the FTS index
        db.execute('''
            CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products
            BEGIN
                INSERT INTO product_search(rowid, name, description)
                VALUES (NEW.id, NEW.name, NEW.description);
            END
        ''')
        
        db.execute('''
            CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products
            BEGIN
                DELETE FROM product_search WHERE rowid = OLD.id;
            END
        ''')
        
        db.execute('''
            CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products
            BEGIN
                DELETE FROM product_search WHERE rowid = OLD.id;
                INSERT INTO product_search(rowid, name, description)
                VALUES (NEW.id, NEW.name, NEW.description);
            END
        ''')
        
        db.commit()

@app.route('/search')
def search():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])

    try:
        db = get_db()
        
        # Search using FTS5 with relevance ranking
        results = db.execute('''
            SELECT p.id, p.name, p.description, p.price, p.stock
            FROM product_search ps
            JOIN products p ON ps.rowid = p.id
            WHERE product_search MATCH ?
            ORDER BY rank
            LIMIT 20
        ''', (query,)).fetchall()

        return jsonify([dict(row) for row in results])
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

@app.route('/init_db')
def initialize_db():
    try:
        init_db()
        
        # Insert sample data
        db = get_db()
        sample_products = [
            ('Organic Cotton T-Shirt', 'Comfortable organic cotton t-shirt', 29.99, 100),
            ('Wireless Bluetooth Headphones', 'Noise-cancelling wireless headphones', 199.99, 50),
            ('Stainless Steel Water Bottle', 'Eco-friendly 1L insulated bottle', 39.99, 75),
            ('Yoga Mat', 'Eco-friendly non-slip yoga mat', 49.99, 30),
            ('LED Desk Lamp', 'Adjustable smart LED lamp with wireless charging', 89.99, 40)
        ]
        db.executemany('''
            INSERT INTO products (name, description, price, stock)
            VALUES (?, ?, ?, ?)
        ''', sample_products)
        db.commit()
        return 'Database initialized with sample data!'
    except sqlite3.Error as e:
        return f'Error initializing database: {str(e)}', 500

@app.route('/test_search')
def test_search():
    return render_template_string('''
        <h1>Search Test</h1>
        <form action="/search" method="GET">
            <input type="text" name="query" placeholder="Search products...">
            <button type="submit">Search</button>
        </form>
        <p>Try searching for: "organic", "eco-friendly", "wireless", or "lamp"</p>
    ''')

if __name__ == '__main__':
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    init_db()
    app.run(debug=True)