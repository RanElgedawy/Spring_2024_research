from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Create database and table if they don't exist
def create_database():
    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 description TEXT
                 )''')
    conn.commit()
    conn.close()

# Function to search products
@app.route('/search', methods=['GET'])
def search():
    create_database()  # Ensure database and table exist

    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    conn = sqlite3.connect('products.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM products WHERE name LIKE ? OR description LIKE ?''', (f'%{query}%', f'%{query}%'))
    results = c.fetchall()
    conn.close()

    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(debug=True)