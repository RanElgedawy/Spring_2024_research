import sqlite3

# Initialize the database connection and create tables if they don't exist
def initialize_db():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create table for products
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )
    ''')

    # Insert some test data
    cursor.executemany('''
    INSERT INTO products (name, description, price)
    VALUES (?, ?, ?)
    ''', [
        ('Laptop', 'A high performance laptop', 999.99),
        ('Phone', 'Smartphone with 4GB RAM', 299.99),
        ('Headphones', 'Noise cancelling headphones', 199.99),
        ('Keyboard', 'Mechanical keyboard', 89.99),
        ('Monitor', '24-inch Full HD monitor', 149.99)
    ])

    conn.commit()
    conn.close()

# Secure search function using parameterized queries
def search_products(name=None, min_price=None, max_price=None, description=None):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Build the query dynamically but securely using placeholders
    query = "SELECT id, name, description, price FROM products WHERE 1=1"
    params = []

    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    
    if min_price:
        query += " AND price >= ?"
        params.append(min_price)
    
    if max_price:
        query += " AND price <= ?"
        params.append(max_price)
    
    if description:
        query += " AND description LIKE ?"
        params.append(f"%{description}%")

    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    # Format results for testing output
    return results

# Function to test the search
def test_search():
    print("Test 1: Search by name 'Phone'")
    print(search_products(name='Phone'))

    print("\nTest 2: Search by price range 100 to 300")
    print(search_products(min_price=100, max_price=300))

    print("\nTest 3: Search by description containing 'laptop'")
    print(search_products(description='laptop'))

# Main execution flow
if __name__ == "__main__":
    initialize_db()
    test_search()