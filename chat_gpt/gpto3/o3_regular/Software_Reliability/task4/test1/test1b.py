import sqlite3

def create_connection(db_file=":memory:"):
    """Create a database connection to the SQLite database."""
    return sqlite3.connect(db_file)

def create_tables(conn):
    """Create the products table and an FTS virtual table for full-text search."""
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create the main products table.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    );
    """)
    
    # Create a virtual table using FTS5 for full-text search.
    # Note: 'content' and 'content_rowid' link this FTS table to the products table.
    cursor.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS products_fts 
    USING fts5(name, description, content='products', content_rowid='id');
    """)
    
    # Create triggers to keep the FTS table in sync with the products table.
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
        INSERT INTO products_fts(rowid, name, description) VALUES (new.id, new.name, new.description);
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
        INSERT INTO products_fts(products_fts, rowid, name, description) VALUES('delete', old.id, old.name, old.description);
    END;
    """)
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
        INSERT INTO products_fts(products_fts, rowid, name, description) VALUES('delete', old.id, old.name, old.description);
        INSERT INTO products_fts(rowid, name, description) VALUES (new.id, new.name, new.description);
    END;
    """)
    
    conn.commit()

def add_sample_products(conn):
    """Insert some sample products into the database."""
    products = [
        ("Apple iPhone 12", "Latest model with A14 Bionic chip and dual-camera system."),
        ("Samsung Galaxy S21", "High performance smartphone with excellent display."),
        ("Google Pixel 6", "Featuring a custom Tensor chip and great camera quality."),
        ("Dell XPS 13", "Compact and powerful ultrabook for everyday use."),
        ("Sony WH-1000XM4", "Industry leading noise cancellation headphones."),
    ]
    
    cursor = conn.cursor()
    cursor.executemany("INSERT INTO products (name, description) VALUES (?, ?);", products)
    conn.commit()

def search_products(conn, query):
    """
    Search for products by querying the FTS virtual table.
    
    The query uses BM25 ranking (a built-in ranking function for FTS5) to order the results 
    by relevance. It returns up to 10 of the best matching products.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT products.id, products.name, products.description, bm25(products_fts) as score
        FROM products_fts 
        JOIN products ON products_fts.rowid = products.id
        WHERE products_fts MATCH ?
        ORDER BY score LIMIT 10;
    """, (query,))
    return cursor.fetchall()

def test_search_function(conn):
    """Test the search functionality with several queries."""
    test_queries = ["iPhone", "smartphone", "noise cancellation", "ultrabook"]
    for q in test_queries:
        print(f"Search results for query: '{q}'")
        results = search_products(conn, q)
        if results:
            for row in results:
                # Lower BM25 score indicates a better match.
                print(f"ID: {row[0]}, Name: {row[1]}, Score: {row[3]:.2f}")
        else:
            print("No results found.")
        print("-" * 40)

def main():
    conn = create_connection()  # Using in-memory database for self-containment.
    create_tables(conn)
    add_sample_products(conn)
    test_search_function(conn)
    conn.close()

if __name__ == "__main__":
    main()
