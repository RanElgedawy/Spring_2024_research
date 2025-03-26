import sqlite3

def create_connection(db_file):
    """Create a database connection."""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
    except Error as e:
        print(e)
    return conn

def create_table(conn, sql):
    """Create a table from the create_table_sql statement."""
    try:
        c = conn.cursor()
        c.execute(sql)
    except Error as e:
        print(e)

def insert_product(conn, product):
    """Insert a product into the products table."""
    sql = '''
        INSERT INTO products(name, description, price)
        VALUES (?,?,?)
        '''
    cur = conn.cursor()
    cur.execute(sql, product)
    return cur.lastrowid

def search_products(conn, query):
    """Search products based on the query."""
    sql = f'''
        SELECT * FROM products WHERE name MATCH ? OR description MATCH ?
    '''
    cur = conn.cursor()
    cur.execute(sql, (query, query))
    rows = cur.fetchall()
    return rows

# Example usage
db_file = "products.db"
conn = create_connection(db_file)

if conn is not None:
    create_table(conn, "DROP TABLE IF EXISTS products")
    create_table(conn, """CREATE TABLE products (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        name TEXT NOT NULL,
                                        description TEXT,
                                        price REAL
                                    );""")
    create_table(conn, """CREATE INDEX products_fts_index ON products (name, description);""")

    # Insert some sample products
    insert_product(conn, ("Laptop", "Powerful laptop with 16GB RAM", 1299.99))
    insert_product(conn, ("Phone", "High-resolution camera phone", 999.99))

    # Search for products
    results = search_products(conn, "laptop")
    for result in results:
        print(f"ID: {result['id']}, Name: {result['name']}, Price: {result['price']}")

    conn.close()
else:
    print("Error! Cannot create the database connection.")