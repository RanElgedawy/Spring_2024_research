import sqlite3

def initialize_database():
    """Creates an in-memory SQLite database and sets up the tables."""
    conn = sqlite3.connect(':memory:')  # Use ':memory:' for a temporary database; replace with a filename for persistence.
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create a users table. 'is_admin' is 1 for admin users, 0 otherwise.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    ''')

    # Create a products table.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')
    conn.commit()
    return conn

def seed_database(conn):
    """Populates the database with sample users and products."""
    cursor = conn.cursor()

    # Insert sample users: one admin and one regular user.
    users = [
        (1, 'admin_user', 1),      # Admin user
        (2, 'regular_user', 0)     # Regular user
    ]
    cursor.executemany('INSERT INTO users (id, username, is_admin) VALUES (?, ?, ?)', users)

    # Insert sample products.
    products = [
        (1, 'Product A', 'Description A', 10.0),
        (2, 'Product B', 'Description B', 20.0)
    ]
    cursor.executemany('INSERT INTO products (id, name, description, price) VALUES (?, ?, ?, ?)', products)
    conn.commit()

def is_admin(user_id, conn):
    """Verifies if a given user_id belongs to an admin."""
    cursor = conn.cursor()
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    if result is not None:
        return result[0] == 1
    return False

def add_product(user_id, name, description, price, conn):
    """Allows an admin to add a new product."""
    if not is_admin(user_id, conn):
        raise Exception("User does not have admin privileges.")
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (name, description, price) VALUES (?, ?, ?)', (name, description, price))
    conn.commit()
    return cursor.lastrowid

def modify_product(user_id, product_id, name=None, description=None, price=None, conn=None):
    """Allows an admin to update an existing product. Only provided fields are updated."""
    if not is_admin(user_id, conn):
        raise Exception("User does not have admin privileges.")
    cursor = conn.cursor()

    # Retrieve current product details
    cursor.execute('SELECT name, description, price FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if product is None:
        raise Exception("Product not found.")

    # Use new values if provided; otherwise, keep the existing values.
    updated_name = name if name is not None else product[0]
    updated_description = description if description is not None else product[1]
    updated_price = price if price is not None else product[2]

    cursor.execute('''
        UPDATE products
        SET name = ?, description = ?, price = ?
        WHERE id = ?
    ''', (updated_name, updated_description, updated_price, product_id))
    conn.commit()

def remove_product(user_id, product_id, conn):
    """Allows an admin to remove a product after verifying its existence."""
    if not is_admin(user_id, conn):
        raise Exception("User does not have admin privileges.")
    cursor = conn.cursor()

    # Verify that the product exists before attempting to remove it.
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    if product is None:
        raise Exception("Product not found.")

    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()

def list_products(conn):
    """Returns a list of all products in the database."""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    return cursor.fetchall()

def main():
    # Initialize and seed the database.
    conn = initialize_database()
    seed_database(conn)
    
    print("Initial products:")
    for product in list_products(conn):
        print(product)

    admin_id = 1
    regular_id = 2

    # Test: Admin adds a new product.
    print("\nAdmin adding a product...")
    new_product_id = add_product(admin_id, 'Product C', 'Description C', 30.0, conn)
    for product in list_products(conn):
        print(product)

    # Test: Admin modifies the newly added product.
    print("\nAdmin modifying Product C...")
    modify_product(admin_id, new_product_id, name='Updated Product C', price=35.0, conn=conn)
    for product in list_products(conn):
        print(product)

    # Test: Admin removes Product B.
    print("\nAdmin removing Product B...")
    remove_product(admin_id, 2, conn)
    for product in list_products(conn):
        print(product)

    # Test: Attempting to remove a non-existent product.
    print("\nAdmin attempting to remove a non-existent product...")
    try:
        remove_product(admin_id, 999, conn)  # Assuming 999 is an invalid product id.
    except Exception as e:
        print("Expected error:", e)

    # Test: Non-admin user attempting to add a product should raise an error.
    print("\nRegular user trying to add a product...")
    try:
        add_product(regular_id, 'Product D', 'Description D', 40.0, conn)
    except Exception as e:
        print("Expected error for regular user:", e)

if __name__ == "__main__":
    main()
