import sqlite3

# Function to connect to the database
def connect_to_database():
    conn = sqlite3.connect('ecommerce.db')
    return conn

# Function to create necessary tables if they don't exist
def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS carts")
    cursor.execute("DROP TABLE IF EXISTS addresses")
    cursor.execute("DROP TABLE IF EXISTS cards")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            total_amount REAL,
            successful INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            item_id INTEGER,
            quantity INTEGER,
            price REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS addresses (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            address TEXT,
            city TEXT,
            zipcode TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            card_number TEXT,
            expiry_date TEXT,
            cvv TEXT
        )
    ''')
    conn.commit()

# Function to simulate payment (in real-world, integrate with payment gateway)
def process_payment(user_id, total_amount, card_info):
    # Simulate payment success for now
    return True

# Function to retrieve cart information from the database
def get_cart(user_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT item_id, quantity, price FROM carts WHERE user_id = ?', (user_id,))
    cart = [{'item_id': row[0], 'quantity': row[1], 'price': row[2]} for row in cursor.fetchall()]
    conn.close()
    return cart

# Function to retrieve user address information from the database
def get_user_address(user_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT address, city, zipcode FROM addresses WHERE user_id = ?', (user_id,))
    address_info = cursor.fetchone()
    conn.close()
    return address_info

# Function to retrieve user card information from the database if logged in
def get_user_card(user_id):
    conn = connect_to_database()
    cursor = conn.cursor()
    cursor.execute('SELECT card_number, expiry_date, cvv FROM cards WHERE user_id = ?', (user_id,))
    card_info = cursor.fetchone()
    conn.close()
    return card_info

# Function to handle checkout process
def checkout(user_id):
    # Check if the user is logged in
    # In a real-world scenario, you would use user authentication mechanism
    if user_id is None:
        return False, "User is not logged in."

    # Fetch user's payment and shipping info from the database
    # For simplicity, assuming payment and shipping info is stored in the database
    # In a real-world scenario, you'd fetch this data based on the user_id
    payment_info = {'card_number': '1234 5678 9012 3456', 'expiry_date': '12/25', 'cvv': '123'}

    # Retrieve user's address information from the database
    address_info = get_user_address(user_id)
    if not address_info:
        return False, "Address information not found."

    # Retrieve user's card information from the database if logged in
    card_info = get_user_card(user_id)
    if not card_info:
        return False, "Card information not found."

    # Retrieve cart information from the database
    cart = get_cart(user_id)
    if not cart:
        return False, "Cart is empty."

    # Calculate total amount including shipping fee
    total_amount = sum(item['price'] * item.get('quantity', 1) for item in cart) + 20

    # Process payment
    if process_payment(user_id, total_amount, card_info):
        # Record successful transaction in the database
        conn = connect_to_database()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO transactions (user_id, total_amount, successful) VALUES (?, ?, ?)', (user_id, total_amount, 1))
        conn.commit()
        conn.close()

        return True, "Transaction successful."
    else:
        return False, "Payment failed."

# Function to insert test data for testing
def insert_test_data():
    conn = connect_to_database()
    create_tables(conn)
    
    # Insert test data into addresses table
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO addresses (user_id, address, city, zipcode)
        VALUES (1, '123 Test St', 'Test City', '12345')
    ''')
    
    # Insert test data into cards table
    cursor.execute('''
        INSERT INTO cards (user_id, card_number, expiry_date, cvv)
        VALUES (1, '1234567812345678', '12/25', '123')
    ''')
    
    # Insert test data into carts table
    cursor.execute('''
        INSERT INTO carts (user_id, item_id, quantity, price)
        VALUES (1, 1, 2, 10.0), (1, 2, 1, 20.0)
    ''')
    
    conn.commit()
    conn.close()

# Test functionality
if __name__ == "__main__":
    insert_test_data()
    
    # Simulate a logged in user with ID 1
    user_id = 1
    
    success, message = checkout(user_id)
    print(message)