import sqlite3

# Initialize the database and create tables if they don't exist.
def init_db():
    conn = sqlite3.connect('ecommerce.db')
    c = conn.cursor()

    # Create a users table with an admin flag.
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("DROP TABLE IF EXISTS products")
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
    ''')

    # Create a products table to store product details.
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL
    )
    ''')
    conn.commit()
    return conn

# Verify whether a user has admin privileges.
def verify_admin(user_id, conn):
    c = conn.cursor()
    c.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    return row is not None and row[0] == 1

# Function to add a new product (admin-only).
def add_product(user_id, conn, name, description, price):
    if not verify_admin(user_id, conn):
        raise PermissionError("User does not have admin privileges.")
    c = conn.cursor()
    c.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", 
              (name, description, price))
    conn.commit()
    print("Product added successfully!")

# Function to modify an existing product (admin-only).
def modify_product(user_id, conn, product_id, name=None, description=None, price=None):
    if not verify_admin(user_id, conn):
        raise PermissionError("User does not have admin privileges.")
    c = conn.cursor()
    # Only update fields if new values are provided.
    if name:
        c.execute("UPDATE products SET name = ? WHERE id = ?", (name, product_id))
    if description:
        c.execute("UPDATE products SET description = ? WHERE id = ?", (description, product_id))
    if price is not None:
        c.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
    conn.commit()
    print("Product updated successfully!")

# Function to remove a product (admin-only).
def remove_product(user_id, conn, product_id):
    if not verify_admin(user_id, conn):
        raise PermissionError("User does not have admin privileges.")
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    print("Product removed successfully!")

# Helper function to list all products.
def list_products(conn):
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    print("\nCurrent Products:")
    for product in products:
        print(product)

# Populate the users table with sample data if empty.
def populate_sample_data(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        # Create one admin user (id will be 1) and one regular user (id will be 2).
        c.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("admin_user", 1))
        c.execute("INSERT INTO users (username, is_admin) VALUES (?, ?)", ("regular_user", 0))
        conn.commit()

# Testing the admin management functionality.
def main():
    conn = init_db()
    populate_sample_data(conn)

    # Assume for testing that admin_user has id 1 and regular_user has id 2.
    admin_user_id = 1
    regular_user_id = 2

    print("Testing with admin user:")
    add_product(admin_user_id, conn, "Product 1", "A great product", 19.99)
    add_product(admin_user_id, conn, "Product 2", "Another great product", 29.99)
    list_products(conn)
    
    modify_product(admin_user_id, conn, 1, name="Updated Product 1", price=24.99)
    list_products(conn)
    
    remove_product(admin_user_id, conn, 2)
    list_products(conn)

    print("\nTesting with regular user (should raise error):")
    try:
        add_product(regular_user_id, conn, "Product 3", "Should fail", 9.99)
    except PermissionError as e:
        print(e)

    conn.close()

if __name__ == '__main__':
    main()
