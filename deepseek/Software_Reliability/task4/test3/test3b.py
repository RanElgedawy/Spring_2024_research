import sqlite3
from sqlite3 import Error
import argparse

def create_connection():
    """Create a database connection and return the connection object"""
    conn = None
    try:
        conn = sqlite3.connect(':memory:')  # Using in-memory database for testing
        print("Connected to SQLite in-memory database")
        return conn
    except Error as e:
        print(e)
    return conn

def setup_database(conn):
    """Create database tables and triggers"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("DROP TABLE IF EXISTS products")
        # Create products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create FTS5 virtual table for searching
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS product_search 
            USING fts5(name, description, content='products', content_rowid='id')
        ''')
        
        # Create triggers to maintain FTS index
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products
            BEGIN
                INSERT INTO product_search(rowid, name, description) 
                VALUES (new.id, new.name, new.description);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products
            BEGIN
                UPDATE product_search 
                SET name = new.name, description = new.description 
                WHERE rowid = old.id;
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products
            BEGIN
                DELETE FROM product_search WHERE rowid = old.id;
            END
        ''')
        
        print("Database tables and triggers created successfully")
    except Error as e:
        print(f"Error setting up database: {e}")

def insert_sample_data(conn):
    """Insert sample product data for testing"""
    products = [
        ('Premium Laptop', 'High-performance laptop with 16GB RAM and 1TB SSD', 1299.99, 50),
        ('Wireless Mouse', 'Ergonomic wireless mouse with RGB lighting', 29.99, 100),
        ('Mechanical Keyboard', 'RGB mechanical keyboard with cherry MX switches', 149.99, 75),
        ('4K Monitor', '27-inch 4K UHD monitor with HDR support', 399.99, 30),
        ('Coffee Mug', 'Insulated stainless steel coffee mug - 16oz', 19.99, 200),
        ('Office Chair', 'Ergonomic office chair with lumbar support', 299.99, 25),
        ('USB-C Hub', '7-in-1 USB-C hub with 4K HDMI output', 49.99, 150),
        ('Noise-Canceling Headphones', 'Wireless headphones with ANC technology', 199.99, 40),
        ('Desk Lamp', 'Smart LED desk lamp with adjustable color temperature', 59.99, 80),
        ('External SSD', '1TB Portable SSD with USB 3.2 Gen 2', 159.99, 60),
    ]
    
    try:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO products (name, description, price, stock_quantity)
            VALUES (?, ?, ?, ?)
        ''', products)
        conn.commit()
        print(f"Inserted {len(products)} sample products")
    except Error as e:
        print(f"Error inserting sample data: {e}")

def search_products(conn, search_term):
    """
    Search products using FTS5 with BM25 ranking
    Weights: name (10.0), description (5.0)
    """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.id,
                p.name,
                p.description,
                p.price,
                p.stock_quantity,
                s.rank
            FROM products p
            JOIN (
                SELECT 
                    rowid, 
                    bm25(product_search, 10.0, 5.0) AS rank
                FROM product_search
                WHERE product_search MATCH ?
                ORDER BY rank
            ) AS s ON p.id = s.rowid
            ORDER BY s.rank
        ''', (search_term,))
        
        results = cursor.fetchall()
        return results
    except Error as e:
        print(f"Search error: {e}")
        return []

def print_results(results):
    """Print search results in a readable format"""
    if not results:
        print("No results found")
        return
    
    print("\nSearch Results:")
    print("{:<5} {:<25} {:<60} {:<10} {:<8}".format(
        "ID", "Name", "Description", "Price", "Stock"
    ))
    for row in results:
        product_id, name, description, price, stock, rank = row
        print("{:<5} {:<25} {:<60} ${:<9.2f} {:<8}".format(
            product_id,
            name[:20] + '...' if len(name) > 20 else name,
            description[:55] + '...' if len(description) > 55 else description,
            price,
            stock
        ))

def test_search(conn):
    """Interactive test interface"""
    print("\nTest Search Interface (type 'exit' to quit)")
    while True:
        search_term = input("\nEnter search terms: ").strip()
        if search_term.lower() == 'exit':
            break
            
        if not search_term:
            print("Please enter a search term")
            continue
            
        results = search_products(conn, search_term)
        print_results(results)

if __name__ == '__main__':
    # Set up database and sample data
    conn = create_connection()
    if conn:
        setup_database(conn)
        insert_sample_data(conn)
        
        # Run test interface
        test_search(conn)
        conn.close()