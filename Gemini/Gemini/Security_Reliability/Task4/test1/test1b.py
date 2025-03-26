import sqlite3
from flask import Flask, request, jsonify

def create_database():
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL
        )
    ''')

    conn.commit()
    conn.close()

app = Flask(__name__)

def search_products(query):
    conn = sqlite3.connect('products.db')
    cursor = conn.cursor()

    # Using parameterized queries to prevent SQL injection
    cursor.execute('''
        SELECT * FROM products WHERE name LIKE ? OR description LIKE ? OR price >= ? OR price <= ?
    ''', (f'%{query}%', f'%{query}%', query, query))

    results = cursor.fetchall()
    conn.close()

    return results

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query is required'})

    results = search_products(query)
    return jsonify(results)

if __name__ == '__main__':
    create_database()
    app.run(debug=True)