from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Create a database connection
def get_db_connection():
    conn = sqlite3.connect('products.db')
    conn.row_factory = sqlite3.Row
    return conn

# Create a table if it doesn't exist
def create_table():
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Search function
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    conn = get_db_connection()

    # Simple search based on name and description
    cursor = conn.execute('''
        SELECT * FROM products
        WHERE name LIKE ? OR description LIKE ?
    ''', (f'%{query}%', f'%{query}%'))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify(results)

# Test data
if __name__ == '__main__':
    create_table()

    # Add some sample products
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO products (name, description) VALUES
        ('Laptop', 'A powerful laptop for work and play'),
        ('Smartphone', 'A sleek smartphone with advanced features'),
        ('Headphones', 'High-quality headphones for music and gaming')
    ''')
    conn.commit()
    conn.close()

    app.run(debug=True)