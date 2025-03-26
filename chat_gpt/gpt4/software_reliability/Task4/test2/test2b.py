import sqlite3

# Set up the database connection
def setup_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create the products table
    cursor.execute("DROP TABLE IF EXISTS products")
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')
    conn.commit()
    return conn, cursor

# Insert sample data into the products table
def insert_sample_data(cursor):
    sample_products = [
        ('Laptop', 'A high-performance laptop with 16GB RAM and 512GB SSD.', 999.99),
        ('Smartphone', 'A smartphone with an amazing camera and long battery life.', 699.99),
        ('Headphones', 'Noise-cancelling over-ear headphones with Bluetooth connectivity.', 199.99),
        ('Camera', 'A DSLR camera with 24MP resolution and multiple lenses.', 499.99),
        ('Coffee Maker', 'An automatic coffee maker with a built-in grinder.', 129.99),
        ('Monitor', 'A 27-inch 4K monitor with HDR support.', 299.99),
        ('Mouse', 'A wireless mouse with ergonomic design and long battery life.', 49.99),
        ('Keyboard', 'Mechanical keyboard with RGB lighting and programmable keys.', 89.99)
    ]

    cursor.executemany('''
    INSERT INTO products (name, description, price)
    VALUES (?, ?, ?)
    ''', sample_products)

    cursor.connection.commit()

# Search function
def search_products(cursor, query):
    # Simple search using SQL LIKE operator for product name and description
    cursor.execute('''
    SELECT id, name, description, price
    FROM products
    WHERE name LIKE ? OR description LIKE ?
    ORDER BY CASE 
        WHEN name LIKE ? THEN 1
        WHEN description LIKE ? THEN 2
        ELSE 3
    END
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

    # Fetch and return the results
    results = cursor.fetchall()
    return results

# Function to test the search functionality
def test_search():
    # Set up database and cursor
    conn, cursor = setup_database()

    # Insert sample data (if table is empty)
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        insert_sample_data(cursor)

    # Get the search query from the user
    query = input("Enter your search query: ")

    # Perform the search
    results = search_products(cursor, query)

    # Display the results
    if results:
        print(f"Search results for '{query}':")
        for result in results:
            print(f"ID: {result[0]}, Name: {result[1]}, Description: {result[2]}, Price: ${result[3]:.2f}")
    else:
        print(f"No results found for '{query}'.")

    # Close the connection
    conn.close()

if __name__ == '__main__':
    test_search()