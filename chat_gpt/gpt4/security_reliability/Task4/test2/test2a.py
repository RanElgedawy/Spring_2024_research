import sqlite3

# Database connection
def create_connection():
    conn = sqlite3.connect(":memory:")  # Using an in-memory database for testing purposes
    return conn

# Create a table for products and populate with sample data
def create_table_and_insert_data(conn):
    cursor = conn.cursor()

    # Create products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')

    # Sample data
    sample_data = [
        ('Laptop', 'A high-performance laptop', 1000.99),
        ('Smartphone', 'A feature-packed smartphone', 499.99),
        ('Headphones', 'Noise-cancelling headphones', 199.99),
        ('Monitor', 'A 27-inch 4K monitor', 349.99),
        ('Mouse', 'A wireless mouse', 29.99),
    ]

    # Insert sample data
    cursor.executemany('''
        INSERT INTO products (name, description, price) 
        VALUES (?, ?, ?)
    ''', sample_data)

    conn.commit()

# Function to search products securely
def search_products(conn, name=None, description=None, min_price=None, max_price=None):
    cursor = conn.cursor()

    # Start the query
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    # Add conditions based on parameters passed
    if name:
        query += " AND name LIKE ?"
        params.append(f'%{name}%')
    
    if description:
        query += " AND description LIKE ?"
        params.append(f'%{description}%')

    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)

    # Execute the query with the parameters
    cursor.execute(query, params)
    results = cursor.fetchall()

    # Return the search results
    return results

# Test the implementation
def test_search_functionality():
    # Create a connection and setup the table with data
    conn = create_connection()
    create_table_and_insert_data(conn)

    # Example test cases
    print("Search for 'Laptop':")
    results = search_products(conn, name="Laptop")
    print(results)

    print("\nSearch for products with price between 100 and 500:")
    results = search_products(conn, min_price=100, max_price=500)
    print(results)

    print("\nSearch for products with 'wireless' in description:")
    results = search_products(conn, description="wireless")
    print(results)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    test_search_functionality()