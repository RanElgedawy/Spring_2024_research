import sqlite3

def create_tables(conn):
    """Create users and products tables if they do not exist."""
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            is_admin INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    """)
    conn.commit()

def seed_users(conn):
    """Insert sample users into the users table."""
    cur = conn.cursor()
    # Insert an admin and a non-admin user
    users = [
        ('admin', 1),  # is_admin = 1 (true)
        ('user', 0)    # is_admin = 0 (false)
    ]
    for username, is_admin in users:
        try:
            cur.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", (username, is_admin))
        except sqlite3.IntegrityError:
            # User already exists; skip
            pass
    conn.commit()

def is_admin(conn, username):
    """Check if the given username has admin privileges."""
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    return row is not None and row[0] == 1

def add_product(conn, username, name, price, description):
    """Add a product if the user is admin."""
    if not is_admin(conn, username):
        raise PermissionError(f"User '{username}' does not have admin privileges.")
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, description) VALUES (?, ?, ?)", 
                (name, price, description))
    conn.commit()
    print(f"Product '{name}' added.")

def update_product(conn, username, product_id, name=None, price=None, description=None):
    """Update product details if the user is admin."""
    if not is_admin(conn, username):
        raise PermissionError(f"User '{username}' does not have admin privileges.")
    cur = conn.cursor()
    
    # Build update query dynamically based on provided parameters
    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if price is not None:
        fields.append("price = ?")
        values.append(price)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    
    if not fields:
        print("No updates provided.")
        return
    
    values.append(product_id)
    query = f"UPDATE products SET {', '.join(fields)} WHERE id = ?"
    cur.execute(query, tuple(values))
    conn.commit()
    print(f"Product id {product_id} updated.")

def remove_product(conn, username, product_id):
    """Remove a product if the user is admin."""
    if not is_admin(conn, username):
        raise PermissionError(f"User '{username}' does not have admin privileges.")
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    print(f"Product id {product_id} removed.")

def list_products(conn):
    """Retrieve and print all products."""
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, description FROM products")
    products = cur.fetchall()
    if not products:
        print("No products available.")
    else:
        for prod in products:
            print(f"ID: {prod[0]}, Name: {prod[1]}, Price: {prod[2]}, Description: {prod[3]}")

if __name__ == '__main__':
    # For demonstration, we use an in-memory SQLite DB.
    # To persist data, change ':memory:' to a file name like 'ecommerce.db'
    conn = sqlite3.connect(':memory:')
    
    # Create tables and seed sample users.
    create_tables(conn)
    seed_users(conn)
    
    print("Initial product list:")
    list_products(conn)
    
    # Testing as admin
    print("\n--- Admin Operations ---")
    admin_user = 'admin'
    try:
        add_product(conn, admin_user, "Widget", 19.99, "A useful widget.")
        add_product(conn, admin_user, "Gadget", 29.99, "A fancy gadget.")
    except PermissionError as e:
        print(e)
    
    print("\nProduct list after adding products (admin):")
    list_products(conn)
    
    # Update a product
    try:
        update_product(conn, admin_user, product_id=1, price=17.99)
    except PermissionError as e:
        print(e)
    
    print("\nProduct list after updating product id 1 (admin):")
    list_products(conn)
    
    # Remove a product
    try:
        remove_product(conn, admin_user, product_id=2)
    except PermissionError as e:
        print(e)
    
    print("\nProduct list after removing product id 2 (admin):")
    list_products(conn)
    
    # Testing as a non-admin user
    print("\n--- Non-Admin Operations ---")
    non_admin_user = 'user'
    try:
        add_product(conn, non_admin_user, "New Product", 9.99, "Should not be allowed.")
    except PermissionError as e:
        print(e)
    
    # Final product list
    print("\nFinal product list:")
    list_products(conn)
    
    conn.close()
