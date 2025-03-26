import sqlite3

def create_db():
    # Connect to an in-memory database for testing.
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    # Create the products table.
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)
    conn.commit()
    return conn

def seed_data(conn):
    # Insert some sample products.
    products = [
        ("Apple iPhone 13", "Latest model smartphone", 999.99),
        ("Samsung Galaxy S21", "Android flagship phone", 799.99),
        ("Dell XPS 15", "High performance laptop", 1299.99),
        ("Sony WH-1000XM4", "Noise cancelling headphones", 349.99),
        ("Apple MacBook Pro", "High-end laptop for professionals", 1999.99)
    ]
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO products (name, description, price) VALUES (?, ?, ?)", products
    )
    conn.commit()

def search_products(conn, search_term=None, min_price=None, max_price=None):
    cur = conn.cursor()
    # Start building the SQL query.
    query = "SELECT id, name, description, price"
    params = []

    # If a search term is provided, calculate a relevance score:
    # 2 points if the name matches and 1 point if the description matches.
    if search_term:
        query += """, 
            ((CASE WHEN lower(name) LIKE '%' || lower(?) || '%' THEN 2 ELSE 0 END) +
             (CASE WHEN lower(description) LIKE '%' || lower(?) || '%' THEN 1 ELSE 0 END)) AS relevance"""
        params.extend([search_term, search_term])
    
    query += " FROM products WHERE 1=1"
    
    # Add optional price filters.
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    # If searching by text, ensure we only return products with a match.
    if search_term:
        query += " AND ((CASE WHEN lower(name) LIKE '%' || lower(?) || '%' THEN 2 ELSE 0 END) + " \
                 " (CASE WHEN lower(description) LIKE '%' || lower(?) || '%' THEN 1 ELSE 0 END)) > 0"
        params.extend([search_term, search_term])
        query += " ORDER BY relevance DESC"
    
    cur.execute(query, params)
    return cur.fetchall()

def test_search():
    conn = create_db()
    seed_data(conn)
    
    print("All products:")
    for row in search_products(conn):
        print(row)
    
    print("\nSearch for 'Apple':")
    for row in search_products(conn, search_term="Apple"):
        print(row)
    
    print("\nSearch for products with price between 500 and 1500:")
    for row in search_products(conn, min_price=500, max_price=1500):
        print(row)

if __name__ == "__main__":
    test_search()
