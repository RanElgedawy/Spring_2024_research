import sqlite3

def create_connection():
    # Create an in-memory SQLite database. For production, you could use a file-based DB.
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn

def create_tables(conn):
    # Create a virtual table using FTS5 for full-text search on product name and description.
    conn.execute("DROP TABLE IF EXISTS products")
    conn.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS products USING fts5(
            name, 
            description,
            content=''
        );
    ''')
    conn.commit()

def insert_product(conn, name, description):
    # Insert a product into the FTS table.
    conn.execute('INSERT INTO products (name, description) VALUES (?, ?)', (name, description))
    conn.commit()

def search_products(conn, query):
    # Search the products table using the MATCH operator.
    # The bm25() function returns a ranking score (lower is better).
    cursor = conn.execute('''
        SELECT rowid, name, description, bm25(products) AS rank
        FROM products
        WHERE products MATCH ?
        ORDER BY rank
    ''', (query,))
    return cursor.fetchall()

def main():
    conn = create_connection()
    create_tables(conn)
    
    # Insert some sample products
    insert_product(conn, 'Red Shirt', 'A bright red shirt made of cotton.')
    insert_product(conn, 'Blue Jeans', 'Comfortable blue jeans with a modern fit.')
    insert_product(conn, 'Green Hat', 'A stylish green hat perfect for summer.')
    insert_product(conn, 'Red Dress', 'Elegant red dress for special occasions.')
    
    # Test the search functionality
    query = input("Enter search query (e.g., 'red', 'cotton', 'dress'): ")
    results = search_products(conn, query)
    
    print(f"\nSearch results for '{query}':")
    if results:
        for row in results:
            print(f"ID: {row['rowid']}, Name: {row['name']}")
            print(f"Description: {row['description']}")
            print(f"Relevance Score (BM25): {row['rank']:.2f}\n")
    else:
        print("No products found.")

if __name__ == '__main__':
    main()
