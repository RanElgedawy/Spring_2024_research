import sqlite3

def setup_database():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  description TEXT,
                  price REAL)''')
    
    # Insert some test data
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
              ('Product 1', 'Description of product 1', 19.99))
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
              ('Product 2', 'Description of product 2', 29.99))
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
              ('Product 3', 'Description of product 3', 39.99))
    
    conn.commit()
    conn.close()

setup_database()

def search_products(search_term=None, search_by=None):
    # Validate presence of required arguments
    if not search_term:
        return "Error: Missing 'search_term' argument"
    if not search_by:
        return "Error: Missing 'search_by' argument"
    
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()
    
    # Ensure that the search_by value is safe and valid
    if search_by not in ['name', 'description', 'price']:
        conn.close()
        return "Error: Invalid search criterion"
    
    # Use parameterized query to avoid SQL injection
    query = f"SELECT id, name, description, price FROM products WHERE {search_by} LIKE ?"
    c.execute(query, (f'%{search_term}%',))
    
    results = c.fetchall()
    conn.close()
    
    # Check if no results were found
    if not results:
        return "No results found"
    
    return results

def test_search():
    print("Test missing search_term:")
    result = search_products(search_by='name')
    print(result)

    print("\nTest missing search_by:")
    result = search_products(search_term='Product 1')
    print(result)

    print("\nSearch by name 'Product 1':")
    results = search_products('Product 1', search_by='name')
    if results == "No results found":
        print(results)
    else:
        for result in results:
            print(result)
    
    print("\nSearch by description 'Nonexistent Description':")
    results = search_products('Nonexistent Description', search_by='description')
    if results == "No results found":
        print(results)
    else:
        for result in results:
            print(result)
    
    print("\nSearch by price '100.00':")
    results = search_products('100.00', search_by='price')
    if results == "No results found":
        print(results)
    else:
        for result in results:
            print(result)

test_search()