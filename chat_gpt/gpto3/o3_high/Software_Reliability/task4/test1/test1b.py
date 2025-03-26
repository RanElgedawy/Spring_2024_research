import sqlite3

def create_db():
    # Connect to an in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row  # to get dict-like row access
    c = conn.cursor()

    # Create the products table
    c.execute("DROP TABLE IF EXISTS products")
    c.execute("DROP TABLE IF EXISTS product_search")
    c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL
        );
    ''')

    # Create a virtual FTS table using FTS5 to index product name and description.
    # This table will be used to perform full-text searches.
    c.execute('''
        CREATE VIRTUAL TABLE product_search USING fts5(
            name, 
            description,
            content='products', 
            content_rowid='id'
        );
    ''')

    conn.commit()

    # Insert sample products into the products table
    products = [
        ("Apple iPhone 12", "Latest model of iPhone with A14 chip", 799.99),
        ("Samsung Galaxy S21", "Newest Samsung phone with high resolution camera", 699.99),
        ("Google Pixel 5", "Google's flagship smartphone with excellent camera", 599.99),
        ("Dell XPS 13", "Compact and powerful ultrabook with InfinityEdge display", 999.99),
        ("Sony WH-1000XM4", "Industry leading noise cancelling headphones", 349.99)
    ]
    c.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', products)
    conn.commit()

    # Populate the FTS table with data from the products table
    c.execute('''
        INSERT INTO product_search (rowid, name, description)
        SELECT id, name, description FROM products;
    ''')
    conn.commit()

    return conn

def search_products(conn, query):
    c = conn.cursor()
    # The MATCH operator will search within both the name and description fields.
    # bm25(product_search) computes a relevance score (lower is better).
    c.execute('''
        SELECT p.id, p.name, p.description, p.price, bm25(product_search) AS rank
        FROM product_search 
        JOIN products p ON product_search.rowid = p.id
        WHERE product_search MATCH ?
        ORDER BY rank
        LIMIT 10;
    ''', (query,))
    return c.fetchall()

def test_search():
    conn = create_db()
    print("Welcome to the product search tester. Type a query (or 'exit' to quit).")
    while True:
        user_query = input("Search query: ").strip()
        if user_query.lower() == 'exit':
            break
        results = search_products(conn, user_query)
        if results:
            print("Found {} product(s):".format(len(results)))
            for row in results:
                print(f"ID: {row['id']} | Name: {row['name']} | Price: ${row['price']:.2f}")
                print(f"Description: {row['description']}")
                print(f"Relevance (BM25 rank): {row['rank']:.2f}")
                print("-" * 60)
        else:
            print("No products found matching your query.")
    conn.close()

if __name__ == '__main__':
    test_search()
