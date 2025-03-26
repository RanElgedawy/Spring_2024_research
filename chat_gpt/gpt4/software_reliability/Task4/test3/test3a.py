import sqlite3

def initialize_database(db_name="ecommerce.db"):
    """Initialize the database and create the products table with some sample data."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Enable Full-Text Search in SQLite (using FTS5)
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("CREATE VIRTUAL TABLE products USING fts5(id, name, description)")

    # Sample data for products
    sample_data = [
        (1, "Laptop", "A high-performance laptop for gaming and work."),
        (2, "Smartphone", "A smartphone with a great camera and long battery life."),
        (3, "Headphones", "Noise-cancelling headphones for immersive sound."),
        (4, "Keyboard", "Mechanical keyboard with RGB lighting."),
        (5, "Monitor", "4K monitor for sharp visuals and vibrant colors."),
        (6, "Mouse", "Ergonomic mouse with customizable buttons."),
        (7, "Webcam", "HD webcam for video conferencing and streaming."),
        (8, "Speaker", "Portable Bluetooth speaker with powerful sound."),
        (9, "Tablet", "A tablet for reading, browsing, and light gaming."),
        (10, "Charger", "Fast-charging USB-C charger for phones and laptops.")
    ]

    # Insert sample data into the products table
    cursor.executemany("INSERT INTO products (id, name, description) VALUES (?, ?, ?)", sample_data)
    conn.commit()
    conn.close()

def search_products(query, db_name="ecommerce.db", limit=5):
    """Search for products in the database by name or description."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Perform Full-Text Search
    cursor.execute("SELECT id, name, description FROM products WHERE products MATCH ? ORDER BY rank LIMIT ?", (query, limit))
    results = cursor.fetchall()

    conn.close()
    return results

def test_search():
    """Test the search functionality with sample queries."""
    initialize_database()  # Initialize the database with sample data
    
    # Example search queries
    queries = ["laptop", "gaming", "RGB", "sound", "charger", "phone", "camera"]
    
    for query in queries:
        print(f"Search results for '{query}':")
        results = search_products(query)
        if results:
            for product in results:
                print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}")
        else:
            print("No results found.")
        print("-" * 40)

if __name__ == "__main__":
    test_search()