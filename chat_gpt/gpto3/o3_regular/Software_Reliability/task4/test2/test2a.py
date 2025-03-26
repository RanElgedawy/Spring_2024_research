import sqlite3

def create_tables(conn):
    """
    Creates the products table and the corresponding FTS5 virtual table.
    """
    cur = conn.cursor()
    # Regular table for products
    cur.execute("DROP TABLE IF EXISTS products")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        );
    """)
    # FTS5 virtual table that indexes name and description.
    # 'content' and 'content_rowid' link the virtual table to the products table.
    cur.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts
        USING fts5(name, description, content='products', content_rowid='id');
    """)
    conn.commit()

def insert_product(conn, name, description):
    """
    Inserts a product into the products table and then into the FTS5 index.
    """
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, description) VALUES (?, ?);", (name, description))
    product_id = cur.lastrowid
    # Update the FTS table for the newly inserted row.
    cur.execute("INSERT INTO products_fts(rowid, name, description) VALUES (?, ?, ?);",
                (product_id, name, description))
    conn.commit()

def search_products(conn, query, limit=10):
    """
    Searches the products using the FTS5 table.
    Uses the built-in BM25 ranking function to order results.
    Lower BM25 scores indicate more relevant matches.
    """
    cur = conn.cursor()
    # Execute the FTS5 query joining the main table to retrieve full product info.
    cur.execute(f"""
        SELECT p.id, p.name, p.description, bm25(products_fts) AS rank
        FROM products_fts 
        JOIN products p ON p.id = products_fts.rowid
        WHERE products_fts MATCH ?
        ORDER BY rank
        LIMIT ?;
    """, (query, limit))
    return cur.fetchall()

def test_search():
    # Create an in-memory SQLite database (for persistent storage, supply a filename).
    conn = sqlite3.connect(':memory:')
    create_tables(conn)

    # Insert some sample products.
    products = [
        ("Apple iPhone 13", "Latest Apple smartphone with advanced camera and performance."),
        ("Samsung Galaxy S21", "High-end Android smartphone with great display and camera."),
        ("Google Pixel 6", "Newest Google phone featuring a clean Android experience and excellent camera."),
        ("Apple MacBook Air", "Lightweight laptop with M1 chip and impressive battery life."),
        ("Dell XPS 13", "Compact and powerful laptop with a stunning display.")
    ]
    for name, description in products:
        insert_product(conn, name, description)

    # Prompt user for a search query.
    query = input("Enter your search query: ")
    results = search_products(conn, query)
    
    # Print out the results.
    if results:
        print("\nSearch results:")
        for pid, name, description, rank in results:
            print(f"ID: {pid}\nName: {name}\nDescription: {description}\nRelevance Score (BM25): {rank:.2f}\n")
    else:
        print("No matching products found.")

if __name__ == '__main__':
    test_search()
