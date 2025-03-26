import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# Create a database connection
conn = sqlite3.connect('products.db')
c = conn.cursor()

# Create a table if it doesn't exist
c.execute("DROP TABLE IF EXISTS products")
c.execute('''CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                description TEXT
            )''')
c.executemany("INSERT INTO products (name, description) VALUES (?, ?)", [
        ("Laptop", "A powerful laptop for work and play"),
        ("Smartphone", "A high-end smartphone with a great camera"),
        ("Tablet", "A versatile tablet for entertainment and productivity"),
        ("Headphones", "Wireless headphones with excellent sound quality"),
        ("Mouse", "Ergonomic mouse for comfortable computing"),
])
conn.commit()

@app.route('/search', methods=['POST'])
def search():
    query = request.json['query']

    # Full-text search using LIKE operator
    c.execute("SELECT * FROM products WHERE name LIKE ? OR description LIKE ?", (f'%{query}%', f'%{query}%'))
    results = c.fetchall()

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)