import sqlite3

def setup_database(conn):
    """
    Creates the products table and an associated FTS5 virtual table.
    Inserts sample data if the products table is empty.
    """
    cur = conn.cursor()
    
    # Create products table
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            price REAL
        )
    """)
    
    # Create FTS5 virtual table for full-text search on name and description.
    # This table uses the content option to synchronize with the products table.
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
        USING fts5(name, description, content='products', content_rowid='id')
    """)
    
    # Check if we already have products inserted
    cur.execute("SELECT COUNT(*) FROM products")
    count = cur.fetchone()[0]
    
    if count == 0:
        sample_products = [
            ('Apple iPhone 13', 'Latest model smartphone with advanced features', 799.0),
            ('Samsung Galaxy S21', 'Flagship smartphone with excellent display', 699.0),
            ('Sony Headphones', 'Noise-cancelling over-ear headphones', 199.0),
            ('Dell Laptop', 'High performance laptop for work and gaming', 999.0),
            ('Apple MacBook Pro', 'Powerful laptop with M1 chip', 1299.0),
        ]
        
        cur.executemany("""
            INSERT INTO products (name, description, price)
            VALUES (?, ?, ?)
        """, sample_products)
        conn.commit()
        
        # Populate the FTS table from the products table
        cur.execute("""
            INSERT INTO products_fts (rowid, name, description)
            SELECT id, name, description FROM products
        """)
        conn.commit()

def search_products(conn, query):
    """
    Searches for products using the FTS virtual table.
    Returns up to 10 results ordered by relevance (lower bm25 score indicates higher relevance).
    """
    cur = conn.cursor()
    # The bm25() function calculates a relevance score for each match.
    # Lower score means a better match.
    cur.execute("""
        SELECT products.id, products.name, products.description, products.price, bm25(products_fts) AS score
        FROM products_fts
        JOIN products ON products_fts.rowid = products.id
        WHERE products_fts MATCH ?
        ORDER BY score
        LIMIT 10
    """, (query,))
    
    return cur.fetchall()

def main():
    # Connect to an in-memory database for testing.
    conn = sqlite3.connect(':memory:')
    setup_database(conn)
    
    print("E-commerce Product Search")
    print("Type a search query (e.g. 'Apple', 'laptop', or 'smartphone'), or 'quit' to exit.\n")
    
    while True:
        query = input("Search: ").strip()
        if query.lower() == 'quit':
            break
        
        results = search_products(conn, query)
        if results:
            print("\nResults:")
            for product in results:
                pid, name, description, price, score = product
                print(f"ID: {pid} | Name: {name} | Price: ${price:.2f}")
                print(f"Description: {description}")
                print(f"Relevance Score: {score:.2f}\n")
        else:
            print("No matching products found.\n")

if __name__ == '__main__':
    main()
