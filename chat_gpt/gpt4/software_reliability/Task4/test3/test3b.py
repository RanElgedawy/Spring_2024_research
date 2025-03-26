import sqlite3

# Function to set up the database and create the products table
def setup_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create a products table with sample data
    cursor.execute("DROP TABLE IF EXISTS products")
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL
    )
    ''')

    # Sample products
    products = [
        ('Laptop', 'A high-performance laptop with 16GB RAM and 512GB SSD.'),
        ('Headphones', 'Wireless noise-canceling headphones with long battery life.'),
        ('Smartphone', 'Latest model smartphone with an amazing camera and fast processor.'),
        ('Tablet', 'Lightweight tablet with a sharp display and long-lasting battery.'),
        ('Monitor', '24-inch monitor with Full HD resolution and thin bezels.'),
        ('Keyboard', 'Mechanical keyboard with RGB lighting and comfortable keys.'),
        ('Mouse', 'Ergonomic wireless mouse with adjustable DPI settings.'),
        ('Speaker', 'Portable Bluetooth speaker with deep bass and clear sound.'),
        ('Camera', 'Digital camera with 20MP sensor and optical zoom lens.'),
        ('Charger', 'Fast charging USB-C charger compatible with various devices.')
    ]

    # Insert sample data into the products table
    cursor.executemany('INSERT INTO products (name, description) VALUES (?, ?)', products)
    conn.commit()
    conn.close()

# Function to search for products by name or description
def search_products(query):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Use full-text search with the LIKE operator to find matching products
    cursor.execute('''
    SELECT id, name, description
    FROM products
    WHERE name LIKE ? OR description LIKE ?
    ''', (f'%{query}%', f'%{query}%'))

    # Fetch all matching results
    results = cursor.fetchall()
    conn.close()
    return results

# Function to test the search functionality
def test_search():
    setup_database()
    while True:
        query = input("Enter a search term (or 'exit' to quit): ")
        if query.lower() == 'exit':
            break
        results = search_products(query)
        if results:
            print("Search Results:")
            for product in results:
                print(f"ID: {product[0]}, Name: {product[1]}, Description: {product[2]}")
        else:
            print("No products found matching your search.")

# Run the test
if __name__ == '__main__':
    test_search()