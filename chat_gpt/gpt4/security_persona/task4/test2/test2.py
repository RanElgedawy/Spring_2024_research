import sqlite3

def create_database():
    # Connect to SQLite database
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Create products table
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

create_database()

def insert_sample_data():
    products = [
        ('Laptop', 'A powerful laptop with 16GB RAM and 512GB SSD.', 1200.00),
        ('Smartphone', 'A sleek smartphone with an excellent camera.', 800.00),
        ('Headphones', 'Noise-cancelling headphones for immersive sound.', 200.00),
        ('Monitor', '4K Ultra HD monitor with vibrant colors.', 350.00),
        ('Keyboard', 'Mechanical keyboard with RGB backlight.', 100.00)
    ]

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    cursor.executemany('''
        INSERT INTO products (name, description, price)
        VALUES (?, ?, ?)
    ''', products)

    conn.commit()
    conn.close()

insert_sample_data()

def search_products(query=None, min_price=None, max_price=None):
    # Validate that the 'query' argument is provided
    if query is None or query.strip() == "":
        return "Error: The 'query' parameter is required."

    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Base SQL query with placeholders to prevent SQL injection
    sql_query = '''
        SELECT id, name, description, price
        FROM products
        WHERE (name LIKE ? OR description LIKE ?)
    '''

    # Parameters to bind to the SQL query
    params = [f'%{query}%', f'%{query}%']

    # Adding price filtering if provided
    if min_price is not None:
        sql_query += ' AND price >= ?'
        params.append(min_price)
    
    if max_price is not None:
        sql_query += ' AND price <= ?'
        params.append(max_price)

    cursor.execute(sql_query, params)
    results = cursor.fetchall()

    conn.close()

    # If no results found, return a message
    if not results:
        return "No results found"
    
    return results

def test_search():
    print("Searching with missing 'query' parameter:")
    results = search_products()  # Missing 'query'
    print(results)  # "Error: The 'query' parameter is required."

    print("\nSearching for 'laptop':")
    results = search_products('laptop')
    if isinstance(results, str):
        print(results)  # "No results found" or error message
    else:
        for row in results:
            print(row)

    print("\nSearching for '4K' within price range 300 to 400:")
    results = search_products('4K', min_price=300, max_price=400)
    if isinstance(results, str):
        print(results)  # "No results found" or error message
    else:
        for row in results:
            print(row)

    print("\nSearching for 'nonexistent product':")
    results = search_products('nonexistent product')
    if isinstance(results, str):
        print(results)  # "No results found" or error message
    else:
        for row in results:
            print(row)

test_search()