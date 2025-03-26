import sqlite3

def setup_db(conn):
    """
    Creates the products table and inserts sample products.
    """
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS products")
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    # Sample data
    products = [
        ('Apple iPhone 14', 'Latest model smartphone from Apple', 999.99),
        ('Samsung Galaxy S22', 'High-end Android smartphone', 899.99),
        ('Sony WH-1000XM4', 'Noise cancelling headphones', 349.99),
        ('Dell XPS 13', 'Powerful and portable laptop', 1199.99),
        ('Apple MacBook Pro', 'Professional laptop with M1 chip', 1999.99),
    ]
    c.executemany('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', products)
    conn.commit()

def search_products(conn, query):
    """
    Searches the products table for entries that match the query.
    
    The search checks:
    - Name: if it contains the query (case-insensitive)
    - Description: if it contains the query (case-insensitive)
    - Price: if the query is a number and exactly matches the price
     
    A simple score is computed:
    - +1 if the name matches
    - +1 if the description matches
    - +1 if the price matches (only if the query is a valid number)
    
    Results are returned ordered by score (highest first).
    """
    c = conn.cursor()
    # Build a LIKE pattern for string matching.
    query_like = f'%{query}%'
    # Try to convert the query to a float (for price matching)
    try:
        price_value = float(query)
    except ValueError:
        price_value = None

    # SQL using parameterized queries to avoid SQL injection.
    sql = '''
    SELECT id, name, description, price,
        ((CASE WHEN lower(name) LIKE lower(?) THEN 1 ELSE 0 END) +
         (CASE WHEN lower(description) LIKE lower(?) THEN 1 ELSE 0 END) +
         (CASE WHEN ? IS NOT NULL AND price = ? THEN 1 ELSE 0 END)
        ) as score
    FROM products
    WHERE lower(name) LIKE lower(?) OR lower(description) LIKE lower(?) OR ( ? IS NOT NULL AND price = ?)
    ORDER BY score DESC
    '''
    # Parameters for the query.
    params = (query_like, query_like,
              price_value, price_value,
              query_like, query_like,
              price_value, price_value)
    c.execute(sql, params)
    results = c.fetchall()
    return results

def main():
    # Create an in-memory SQLite database.
    conn = sqlite3.connect(':memory:')
    setup_db(conn)
    
    print("Product search (type 'exit' to quit)")
    while True:
        user_input = input("Enter search query: ").strip()
        if user_input.lower() == 'exit':
            break
        results = search_products(conn, user_input)
        if results:
            print("Search results:")
            for row in results:
                print(f"ID: {row[0]}, Name: {row[1]}, Description: {row[2]}, Price: {row[3]}, Score: {row[4]}")
        else:
            print("No results found.")
    
    conn.close()

if __name__ == '__main__':
    main()
