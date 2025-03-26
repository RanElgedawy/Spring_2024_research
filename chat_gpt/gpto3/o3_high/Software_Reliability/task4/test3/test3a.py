import sqlite3

def create_tables(conn):
    cursor = conn.cursor()
    # Create a regular products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS product_search")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL
        )
    ''')
    conn.commit()
    
    # Create an FTS5 virtual table for full-text search, using products as its content table.
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS product_search USING fts5(
            name, 
            description, 
            content='products', 
            content_rowid='id'
        )
    ''')
    conn.commit()

def populate_sample_data(conn):
    cursor = conn.cursor()
    # Sample product data
    products = [
        ("Apple iPhone 13", "Latest model with advanced features", 999.99),
        ("Samsung Galaxy S21", "High-performance smartphone with excellent camera", 899.99),
        ("Dell XPS 13 Laptop", "Ultra-thin laptop with powerful performance", 1199.99),
        ("Sony WH-1000XM4", "Industry-leading noise cancellation headphones", 349.99),
        ("Apple MacBook Pro", "Powerful laptop for professionals", 1999.99)
    ]
    cursor.executemany('''
        INSERT INTO products (name, description, price) VALUES (?, ?, ?)
    ''', products)
    conn.commit()
    
    # Populate the FTS table with data from the products table
    cursor.execute('''
        INSERT INTO product_search (rowid, name, description)
        SELECT id, name, description FROM products
    ''')
    conn.commit()

def search_products(conn, query):
    cursor = conn.cursor()
    # The MATCH operator performs the FTS search; bm25() provides a relevance score
    # Lower scores indicate a more relevant match.
    cursor.execute('''
        SELECT p.id, p.name, p.description, p.price,
               bm25(product_search) as score
        FROM product_search
        JOIN products p ON p.id = product_search.rowid
        WHERE product_search MATCH ?
        ORDER BY score ASC
        LIMIT 10
    ''', (query,))
    return cursor.fetchall()

def main():
    # Create an in-memory SQLite database
    conn = sqlite3.connect(":memory:")
    create_tables(conn)
    populate_sample_data(conn)
    
    # Allow user to test the search functionality
    query = input("Enter search query: ")
    results = search_products(conn, query)
    
    print("\nSearch results:")
    if results:
        for row in results:
            print(f"ID: {row[0]}")
            print(f"Name: {row[1]}")
            print(f"Description: {row[2]}")
            print(f"Price: ${row[3]:.2f}")
            print(f"Relevance Score: {row[4]:.2f}\n")
    else:
        print("No matching products found.")

if __name__ == "__main__":
    main()
