import sqlite3

def create_connection(db_file=":memory:"):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_file)
    return conn

def create_tables(conn):
    """Create the products table and the FTS virtual table for searching."""
    cur = conn.cursor()
    # Create a standard products table
    cur.execute("DROP TABLE IF EXISTS products")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        )
    """)
    # Create an FTS5 virtual table for full-text search
    cur.execute("CREATE VIRTUAL TABLE IF NOT EXISTS product_index USING fts5(name, description, content='products', content_rowid='id')")
    
    # Create triggers to keep the FTS index up-to-date with the products table
    cur.executescript("""
        CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
            INSERT INTO product_index(rowid, name, description)
            VALUES (new.id, new.name, new.description);
        END;
        CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
            INSERT INTO product_index(product_index, rowid, name, description)
            VALUES('delete', old.id, old.name, old.description);
        END;
        CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
            INSERT INTO product_index(product_index, rowid, name, description)
            VALUES('delete', old.id, old.name, old.description);
            INSERT INTO product_index(rowid, name, description)
            VALUES (new.id, new.name, new.description);
        END;
    """)
    conn.commit()

def insert_sample_data(conn):
    """Insert some sample products into the products table."""
    sample_products = [
        ("Apple iPhone 13", "The latest iPhone with advanced features and great performance."),
        ("Samsung Galaxy S21", "A high-end smartphone with excellent camera and display."),
        ("Dell XPS 13 Laptop", "A powerful and portable laptop perfect for work and entertainment."),
        ("Sony WH-1000XM4", "Industry-leading noise canceling over-ear headphones."),
        ("Apple MacBook Pro", "High performance laptop with an outstanding display and battery life."),
        ("Amazon Echo Dot", "Compact smart speaker with Alexa voice assistant.")
    ]
    cur = conn.cursor()
    cur.executemany("INSERT INTO products (name, description) VALUES (?, ?)", sample_products)
    conn.commit()

def search_products(conn, query, limit=5):
    """
    Search products by matching the query against the product name and description.
    Uses the FTS5 virtual table for relevance ranking.
    """
    cur = conn.cursor()
    # Use the MATCH operator on the FTS virtual table. 
    # FTS5 returns results ordered by relevance (best matches first).
    cur.execute("SELECT p.id, p.name, p.description FROM product_index pi JOIN products p ON p.id = pi.rowid WHERE product_index MATCH ? LIMIT ?", (query, limit))
    results = cur.fetchall()
    return results

def test_search():
    conn = create_connection()
    create_tables(conn)
    insert_sample_data(conn)
    
    # Test the search functionality
    queries = [
        "iPhone",
        "laptop",
        "smart speaker",
        "noise canceling headphones",
        "Galaxy"
    ]
    
    for q in queries:
        print(f"Search results for '{q}':")
        results = search_products(conn, q)
        if results:
            for row in results:
                print(f"  ID: {row[0]} | Name: {row[1]} | Description: {row[2]}")
        else:
            print("  No results found.")
        print("-" * 60)
    
    conn.close()

if __name__ == "__main__":
    test_search()
