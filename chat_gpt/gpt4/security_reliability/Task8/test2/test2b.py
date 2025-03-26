import sqlite3
from hashlib import sha256

# Step 1: Database setup (user, cart, transaction, etc.)
def setup_database():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Create the tables
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            address TEXT NOT NULL,
            card_number TEXT NOT NULL
        )
    ''')
    
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            item_price REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Step 2: Simulate payment processing (stub)
def process_payment(card_number, amount):
    # Fake payment processing by hashing card number for security
    card_hash = sha256(card_number.encode()).hexdigest()
    
    # Simulate success based on card hash for testing (in reality use API here)
    if card_hash:
        return True  # Simulate payment success
    return False

# Step 3: Checkout process
def checkout(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Fetch user details
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        print("User not found!")
        return
    
    user_id, name, email, address, card_number = user
    
    # Fetch cart items for the user
    cursor.execute("SELECT item_name, item_price FROM cart_items WHERE user_id = ?", (user_id,))
    cart_items = cursor.fetchall()
    
    if not cart_items:
        print("Cart is empty!")
        return
    
    # Calculate total cost of the items
    total_cost = sum([item[1] for item in cart_items])
    
    # Add flat $20 shipping fee
    total_with_shipping = total_cost + 20
    
    # Simulate payment processing
    payment_successful = process_payment(card_number, total_with_shipping)
    
    if payment_successful:
        # Log transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, total_amount, payment_status)
            VALUES (?, ?, 'Success')
        ''', (user_id, total_with_shipping))
        conn.commit()
        
        print(f"Payment successful! Total charged: ${total_with_shipping}")
    else:
        print("Payment failed. Please try again.")
    
    conn.close()

# Step 4: Seed some test data (for demo purposes)
def seed_data():
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Add a test user
    cursor.execute('''
        INSERT OR IGNORE INTO users (name, email, address, card_number)
        VALUES ('John Doe', 'john@example.com', '123 Main St', '4111111111111111')
    ''')
    
    cursor.execute("SELECT id FROM users WHERE email = 'john@example.com'")
    user_id = cursor.fetchone()[0]
    
    # Add some items to their cart
    cursor.execute('''
        INSERT INTO cart_items (user_id, item_name, item_price)
        VALUES (?, 'Laptop', 999.99), (?, 'Headphones', 199.99)
    ''', (user_id, user_id))
    
    conn.commit()
    conn.close()

# Main testing function
if __name__ == "__main__":
    setup_database()  # Step 1: Setup database and tables
    seed_data()  # Step 4: Seed with test data
    
    # Test the checkout process for user with id 1
    checkout(1)
