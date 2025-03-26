import sqlite3

DATABASE_NAME = 'ecommerce.db'

def create_tables():
    """Creates the users and products tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS products")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    """)

    # Add a default admin user for testing
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('admin', 'password123', 1))

    # Add a default non-admin user for testing
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'user'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ('user', 'password', 0))

    # Add some sample products
    cursor.execute("SELECT COUNT(*) FROM products WHERE name = 'Test Product 1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", ('Test Product 1', 'This is a test product.', 19.99))
    cursor.execute("SELECT COUNT(*) FROM products WHERE name = 'Test Product 2'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", ('Test Product 2', 'Another test product with a different price.', 29.99))

    conn.commit()
    conn.close()
    print("Tables 'users' and 'products' created (if they didn't exist) and default users/products added.")

def get_user_by_id(user_id):
    """Retrieves user information by user ID."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def is_admin(user_id):
    """Checks if a user has admin privileges."""
    user = get_user_by_id(user_id)
    return user is not None and user[3] == 1

def add_product(user_id, name, description, price):
    """Adds a new product to the database if the user is an admin."""
    if not is_admin(user_id):
        print("Error: Insufficient privileges. Only admin users can add products.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        print(f"Product '{name}' added successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error adding product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def modify_product(user_id, product_id, name=None, description=None, price=None):
    """Modifies an existing product in the database if the user is an admin and the product exists."""
    if not is_admin(user_id):
        print("Error: Insufficient privileges. Only admin users can modify products.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the product exists
    cursor.execute("SELECT product_id FROM products WHERE product_id = ?", (product_id,))
    if cursor.fetchone() is None:
        print(f"Error: Product with ID {product_id} not found.")
        conn.close()
        return False

    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if price is not None:
        updates.append("price = ?")
        params.append(price)

    if not updates:
        print("No updates provided for the product.")
        conn.close()
        return False

    sql = f"UPDATE products SET {', '.join(updates)} WHERE product_id = ?"
    params.append(product_id)

    try:
        cursor.execute(sql, params)
        conn.commit()
        print(f"Product with ID {product_id} modified successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error modifying product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def remove_product(user_id, product_id):
    """Removes a product from the database if the user is an admin and the product exists."""
    if not is_admin(user_id):
        print("Error: Insufficient privileges. Only admin users can remove products.")
        return False

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Check if the product exists
    cursor.execute("SELECT product_id FROM products WHERE product_id = ?", (product_id,))
    if cursor.fetchone() is None:
        print(f"Error: Product with ID {product_id} not found.")
        conn.close()
        return False

    try:
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        print(f"Product with ID {product_id} removed successfully.")
        return True
    except sqlite3.Error as e:
        print(f"Error removing product: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_product_details(product_id):
    """Retrieves details of a specific product."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return {"product_id": product[0], "name": product[1], "description": product[2], "price": product[3]}
    else:
        return None

def list_all_products():
    """Lists all products in the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, price FROM products")
    products = cursor.fetchall()
    conn.close()
    if products:
        print("\n--- All Products ---")
        for product in products:
            print(f"ID: {product[0]}, Name: {product[1]}, Price: ${product[2]:.2f}")
    else:
        print("No products found in the database.")

# --- Functionality to simulate user login (for testing) ---
def login(username, password):
    """Simulates user login and returns the user ID if successful, None otherwise."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ? AND password = ?", (username, password))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return None

# --- Test the functionality ---
def test_admin_operations():
    print("\n--- Testing Admin Operations ---")

    # Simulate admin login
    admin_user_id = login('admin', 'password123')
    if not admin_user_id:
        print("Admin login failed. Please check the default admin user in the create_tables function.")
        return

    print(f"Logged in as admin with ID: {admin_user_id}")

    # Add a new product
    add_product(admin_user_id, 'New Admin Product', 'This product was added by an admin.', 49.99)

    # List all products to see the new one
    list_all_products()

    # Modify an existing product
    modify_product(admin_user_id, 1, name='Updated Test Product 1', price=24.99)
    product1_details = get_product_details(1)
    if product1_details:
        print(f"\nDetails of product 1 after modification: {product1_details}")

    # Remove a product
    remove_product(admin_user_id, 2)
    list_all_products()

def test_non_admin_operations():
    print("\n--- Testing Non-Admin Operations ---")

    # Simulate non-admin login
    non_admin_user_id = login('user', 'password')
    if not non_admin_user_id:
        print("Non-admin login failed. Please check the default non-admin user in the create_tables function.")
        return

    print(f"Logged in as non-admin with ID: {non_admin_user_id}")

    # Try to add a product (should fail)
    add_product(non_admin_user_id, 'New User Product', 'This should not be added by a regular user.', 39.99)

    # Try to modify a product (should fail)
    modify_product(non_admin_user_id, 1, description='Attempted modification by a regular user.')

    # Try to remove a product (should fail)
    remove_product(non_admin_user_id, 3) # Assuming product ID 3 might exist after admin added

    list_all_products()

if __name__ == "__main__":
    # This block will run when the script is executed directly
    create_tables()
    test_admin_operations()
    test_non_admin_operations()