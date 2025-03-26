import sqlite3

def initialize_database():
    # Connect to SQLite database
    conn = sqlite3.connect(':memory:')  # Use an in-memory database for testing
    cursor = conn.cursor()

    # Enable Full-Text Search (FTS5) extension
    cursor.execute("PRAGMA foreign_keys = ON")

    # Create the products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')

    # Create the FTS virtual table for full-text search
    cursor.execute('''
    CREATE VIRTUAL TABLE IF NOT EXISTS products_fts
    USING fts5(name, description, content='products', content_rowid='id')
    ''')

    # Populate the tables with some sample data
    sample_data = [
        ('Laptop', 'A high-performance laptop with 16GB RAM and 512GB SSD.', 1200.00),
        ('Smartphone', 'Latest model smartphone with OLED display.', 800.00),
        ('Headphones', 'Noise-cancelling over-ear headphones.', 150.00),
        ('Keyboard', 'Mechanical keyboard with RGB backlighting.', 100.00),
        ('Monitor', '27-inch 4K UHD monitor.', 400.00)
    ]

    cursor.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', sample_data)

    # Populate the FTS table
    cursor.execute('''
    INSERT INTO products_fts(rowid, name, description)
    SELECT id, name, description FROM products
    ''')

    conn.commit()
    return conn

def search_products(conn, query, limit=10):
    cursor = conn.cursor()

    # Perform the search using FTS and rank the results based on relevance
    cursor.execute('''
    SELECT p.id, p.name, p.description, p.price
    FROM products_fts AS pf
    JOIN products AS p ON p.id = pf.rowid
    WHERE pf.name MATCH ? OR pf.description MATCH ?
    ORDER BY rank
    LIMIT ?
    ''', (query, query, limit))

    # Fetch results
    results = cursor.fetchall()
    return results

def test_search():
    # Initialize the database
    conn = initialize_database()

    # Test the search function
    queries = ['laptop', 'smartphone', 'display', 'keyboard']

    # Perform and print search results for each query
    for query in queries:
        print(f"Results for search '{query}':")
        results = search_products(query)

        for row in results:
            print(f"- {row[1]}: {row[2]} - ${row[0][4]}")
        
if __name__ == "__main__":
    
  test_search()   