import sqlite3

def initialize_database():
    conn = sqlite3.connect(':memory:')  # Use an in-memory database for testing
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS products;")
    # Create a virtual table for full-text search using the porter tokenizer
    cursor.execute('''
    CREATE VIRTUAL TABLE products USING fts5(name, description, tokenize="porter");
    ''')

    # Insert sample data into the products table
    products = [
        ('Laptop', 'A high performance laptop with 16GB RAM and 512GB SSD.'),
        ('Smartphone', 'A smartphone with excellent camera and battery life.'),
        ('Headphones', 'Noise-cancelling over-ear headphones.'),
        ('Smartwatch', 'A smartwatch with fitness tracking and heart rate monitoring.'),
        ('Tablet', 'A lightweight tablet with a 10-inch display and 64GB storage.')
    ]

    cursor.executemany('INSERT INTO products (name, description) VALUES (?, ?)', products)
    conn.commit()

    return conn

def api_search(conn, search_term=None):
    # Check if the search_term is provided
    if not search_term:
        return {"status": "error", "message": "Search term is required."}

    # Perform the search
    results = search_products(conn, search_term)
    
    # Check if results are found
    if results:
        return {"status": "success", "data": results}
    else:
        return {"status": "success", "message": "No results found."}

def search_products(conn, search_term):
    cursor = conn.cursor()
    
    # Perform a partial search on the products table using the LIKE clause
    search_pattern = f'%{search_term}%'
    cursor.execute('''
    SELECT name, description FROM products
    WHERE name LIKE ? OR description LIKE ?
    ''', (search_pattern, search_pattern))
    
    results = cursor.fetchall()
    return results

def test_api_search_functionality():
    print("Testing API search functionality...\n")

    # Initialize the database
    conn = initialize_database()

    # Test case 1: Valid search term "laptop"
    response = api_search(conn, 'laptop')
    print("API response for 'laptop':")
    print(response)
    print("\n" + "="*50 + "\n")

    # Test case 2: Valid search term "smart"
    response = api_search(conn, 'smart')
    print("API response for 'smart':")
    print(response)
    print("\n" + "="*50 + "\n")

    # Test case 3: Valid search term "battery"
    response = api_search(conn, 'battery')
    print("API response for 'battery':")
    print(response)
    print("\n" + "="*50 + "\n")

    # Test case 4: Non-existent search term
    response = api_search(conn, 'nonexistent')
    print("API response for 'nonexistent':")
    print(response)
    print("\n" + "="*50 + "\n")

    # Test case 5: Missing search term (simulates missing argument)
    response = api_search(conn)
    print("API response for missing search term:")
    print(response)
    
    conn.close()

# Run the test
test_api_search_functionality()