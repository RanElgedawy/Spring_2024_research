import sqlite3

def init_db(conn):
    """Create users and products tables."""
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS products")
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT 0
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()

def seed_data(conn):
    """Seed the database with sample users: one admin and one regular user."""
    cur = conn.cursor()
    # Insert an admin user and a non-admin user
    cur.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('admin_user', True))
    cur.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ('regular_user', False))
    conn.commit()

def is_admin(conn, user_id):
    """Check if a given user is an admin."""
    cur = conn.cursor()
    cur.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    result = cur.fetchone()
    if result is None:
        raise ValueError("User not found")
    return bool(result[0])

def add_product(conn, user_id, name, description, price, quantity):
    """Allow admin user to add a new product."""
    if not is_admin(conn, user_id):
        raise PermissionError("User does not have admin privileges")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, description, price, quantity) VALUES (?, ?, ?, ?)",
        (name, description, price, quantity)
    )
    conn.commit()
    return cur.lastrowid

def update_product(conn, user_id, product_id, name=None, description=None, price=None, quantity=None):
    """Allow admin user to update product details."""
    if not is_admin(conn, user_id):
        raise PermissionError("User does not have admin privileges")
    
    # Dynamically build the update statement based on provided fields
    fields = []
    params = []
    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if price is not None:
        fields.append("price = ?")
        params.append(price)
    if quantity is not None:
        fields.append("quantity = ?")
        params.append(quantity)
    
    if not fields:
        raise ValueError("No fields provided to update")
    
    params.append(product_id)
    query = "UPDATE products SET " + ", ".join(fields) + " WHERE id = ?"
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    
    if cur.rowcount == 0:
        raise ValueError("Product not found")

def remove_product(conn, user_id, product_id):
    """Allow admin user to remove a product."""
    if not is_admin(conn, user_id):
        raise PermissionError("User does not have admin privileges")
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise ValueError("Product not found")

def get_product(conn, product_id):
    """Retrieve a product by its ID."""
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price, quantity FROM products WHERE id = ?", (product_id,))
    return cur.fetchone()

def list_products(conn):
    """List all products."""
    cur = conn.cursor()
    cur.execute("SELECT id, name, description, price, quantity FROM products")
    return cur.fetchall()

def main():
    # Use an in-memory SQLite database for testing.
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    seed_data(conn)

    # Assume user IDs: 1 for admin, 2 for non-admin.
    admin_user_id = 1
    regular_user_id = 2

    print("=== Testing with Admin User (user_id = 1) ===")
    # Admin adds a new product.
    product_id = add_product(conn, admin_user_id, "Laptop", "Gaming laptop", 1500.00, 10)
    print(f"Product added with id: {product_id}")

    # List products after addition.
    products = list_products(conn)
    print("Products after addition:")
    for product in products:
        print(product)

    # Admin updates the product.
    update_product(conn, admin_user_id, product_id, price=1400.00, quantity=8)
    updated_product = get_product(conn, product_id)
    print("Product after update:")
    print(updated_product)

    print("\n=== Testing with Regular User (user_id = 2) ===")
    # Non-admin attempting to add a product should fail.
    try:
        add_product(conn, regular_user_id, "Phone", "Smartphone", 800.00, 5)
    except PermissionError as e:
        print("Expected error for non-admin add:", e)

    # Non-admin attempting to update a product should also fail.
    try:
        update_product(conn, regular_user_id, product_id, name="Ultrabook")
    except PermissionError as e:
        print("Expected error for non-admin update:", e)

    print("\n=== Admin Removing the Product ===")
    # Admin removes the product.
    remove_product(conn, admin_user_id, product_id)
    print("Product removed.")

    # List products after removal.
    products = list_products(conn)
    print("Products after removal:")
    for product in products:
        print(product)

    conn.close()

if __name__ == "__main__":
    main()
