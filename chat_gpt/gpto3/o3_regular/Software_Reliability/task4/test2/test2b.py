import sqlite3

def create_tables(conn):
    cursor = conn.cursor()
    # Create the regular products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_description TEXT NOT NULL
        )
    ''')
    # Create an FTS5 virtual table linked to the products table
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
            product_name, 
            product_description, 
            content='products', 
            content_rowid='id'
        );
    ''')
    conn.commit()

def insert_sample_data(conn):
    cursor = conn.cursor()
    # Sample product data
    sample_data = [
        ("Apple iPhone 13", "Latest model with improved battery life and camera features"),
        ("Samsung Galaxy S21", "High-end smartphone with sleek design and powerful performance"),
        ("Google Pixel 6", "New Google phone with excellent camera and stock Android experience"),
        ("Dell XPS 15", "Powerful laptop for professionals with high-resolution display"),
        ("Sony WH-1000XM4", "Noise cancelling over-ear headphones with excellent sound quality")
    ]
    cursor.executemany('''
        INSERT INTO products (product_name, product_description) 
        VALUES (?, ?)
    ''', sample_data)
    conn.commit()

def update_fts(conn):
    cursor = conn.cursor()
    # Rebuild the FTS index from the products table
    cursor.execute("INSERT INTO products_fts(products_fts) VALUES('rebuild')")
    conn.commit()

def search_products(conn, query):
    cursor = conn.cursor()
    # Use the FTS5 MATCH operator and BM25 ranking to sort results by relevance.
    # Note: BM25 returns a lower score for better matches.
    cursor.execute('''
        SELECT p.id, p.product_name, p.product_description,
               bm25(products_fts) AS score
        FROM products_fts 
        JOIN products p ON products_fts.rowid = p.id
        WHERE products_fts MATCH ?
        ORDER BY score
        LIMIT 10;
    ''', (query,))
    return cursor.fetchall()

def main():
    # Use an in-memory SQLite database for this self-contained example.
    conn = sqlite3.connect(':memory:')
    
    # Enable extension loading if needed (FTS5 is usually built-in with Python's sqlite3)
    create_tables(conn)
    insert_sample_data(conn)
    update_fts(conn)
    
    print("E-commerce Product Search Test")
    print("Type a search query (e.g. 'iPhone', 'camera', 'laptop') or 'exit' to quit.")
    
    while True:
        user_query = input("Search query: ")
        if user_query.lower() == 'exit':
            break
        results = search_products(conn, user_query)
        if results:
            print("\nSearch Results:")
            for row in results:
                # The lower the BM25 score, the better the match.
                print(f"ID: {row[0]}, Name: {row[1]}, Description: {row[2]}, Relevance Score: {row[3]:.2f}")
        else:
            print("No matching products found.")
        print()

if __name__ == '__main__':
    main()
