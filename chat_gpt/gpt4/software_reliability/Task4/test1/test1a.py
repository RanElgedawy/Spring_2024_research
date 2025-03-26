import sqlite3

def setup_database():
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Create a table for products
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    
    # Insert sample product data
    sample_products = [
        ('Laptop', 'A high-performance laptop suitable for gaming and work'),
        ('Headphones', 'Noise-cancelling over-ear headphones with rich bass'),
        ('Keyboard', 'Mechanical keyboard with RGB lighting'),
        ('Smartphone', 'Latest smartphone with cutting-edge camera features'),
        ('Gaming Chair', 'Ergonomic gaming chair with adjustable armrests'),
        ('Monitor', '4K Ultra HD monitor with wide viewing angles'),
        ('Mouse', 'Wireless mouse with ergonomic design and high DPI settings'),
        ('Tablet', '10-inch tablet with a high-resolution display and stylus support'),
        ('Printer', 'Wireless printer with fast printing speed and duplex printing'),
        ('Webcam', 'HD webcam with a built-in microphone for video calls')
    ]
    
    cursor.executemany('INSERT INTO products (name, description) VALUES (?, ?)', sample_products)
    conn.commit()
    print("Database setup complete with sample data.")
    conn.close()

def search_products(query, limit=5):
    # Connect to the database
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Perform a full-text search on the name and description fields
    cursor.execute('''
        SELECT id, name, description 
        FROM products 
        WHERE name LIKE ? OR description LIKE ? 
        ORDER BY 
            CASE 
                WHEN name LIKE ? THEN 1 
                WHEN description LIKE ? THEN 2 
                ELSE 3 
            END, 
            name
        LIMIT ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%', limit))
    
    # Fetch the results
    results = cursor.fetchall()
    conn.close()
    return results

def test_search():
    # Set up the database and insert sample data
    setup_database()

    # Test search queries
    test_queries = ['laptop', 'gaming', 'wireless', 'RGB']
    for query in test_queries:
        print(f"Search results for '{query}':")
        results = search_products(query)
        if results:
            for row in results:
                print(f"- {row[1]}: {row[2]}")
        else:
            print("No results found.")
        print('-' * 40)

if __name__ == '__main__':
    # Run the test function
    test_search()