from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def create_connection(db_file):
    """Create a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_table(conn, sql):
    """Create a table in the SQLite database."""
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def insert_product(conn, product):
    """Insert a product into the database."""
    sql = '''
        INSERT INTO products (name, description)
        VALUES (?, ?)
    '''
    cur = conn.cursor()
    cur.execute(sql, product)
    conn.commit()

def search_products(conn, query):
    """Search for products based on name or description."""
    sql = '''
        SELECT * FROM products
        WHERE name LIKE ? OR description LIKE ?
    '''
    cur = conn.cursor()
    cur.execute(sql, ('%'+query+'%', '%'+query+'%'))
    results = cur.fetchall()
    return results

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    conn = create_connection('products.db')
    if conn is None:
        return jsonify({'error': 'Could not connect to database'}), 500

    results = search_products(conn, query)
    conn.close()

    return jsonify(results)

if __name__ == '__main__':
    conn = create_connection('products.db')
    sql_create_products_table = """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        );
    """
    create_table(conn, sql_create_products_table)
    conn.close()

    app.run(debug=True)