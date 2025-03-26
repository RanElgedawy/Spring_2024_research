import sqlite3
import json
from datetime import datetime

class ECommerceCheckout:
    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Creates necessary tables in the database if they don't exist."""
        self.cursor.execute("DROP TABLE IF EXISTS users")
        self.cursor.execute("DROP TABLE IF EXISTS products")
        self.cursor.execute("DROP TABLE IF EXISTS carts")
        self.cursor.execute("DROP TABLE IF EXISTS orders")
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                shipping_address TEXT NOT NULL,
                payment_info TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS carts (
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id),
                PRIMARY KEY (user_id, product_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                shipping_address TEXT NOT NULL,
                payment_status TEXT NOT NULL,
                order_details TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        self.conn.commit()

    def add_user(self, username, shipping_address, payment_info=None):
        """Adds a new user to the database."""
        try:
            self.cursor.execute(
                "INSERT INTO users (username, shipping_address, payment_info) VALUES (?, ?, ?)",
                (username, shipping_address, payment_info),
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            print(f"Username '{username}' already exists.")
            return None

    def get_user_payment_info(self, user_id):
        """Retrieves the saved payment information for a user."""
        self.cursor.execute(
            "SELECT payment_info FROM users WHERE user_id = ?",
            (user_id,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_product(self, name, price):
        """Adds a new product to the database."""
        self.cursor.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def add_to_cart(self, user_id, product_id, quantity):
        """Adds a product to the user's cart or updates the quantity if it already exists."""
        existing_item = self.cursor.execute(
            "SELECT quantity FROM carts WHERE user_id = ? AND product_id = ?",
            (user_id, product_id),
        ).fetchone()
        if existing_item:
            new_quantity = existing_item[0] + quantity
            self.cursor.execute(
                "UPDATE carts SET quantity = ? WHERE user_id = ? AND product_id = ?",
                (new_quantity, user_id, product_id),
            )
        else:
            self.cursor.execute(
                "INSERT INTO carts (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, quantity),
            )
        self.conn.commit()

    def get_cart_items(self, user_id):
        """Retrieves items in the user's cart with product details."""
        self.cursor.execute("""
            SELECT p.product_id, p.name, p.price, c.quantity
            FROM carts c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        """, (user_id,))
        items = self.cursor.fetchall()
        cart_items = []
        for item in items:
            cart_items.append({
                'product_id': item[0],
                'name': item[1],
                'price': item[2],
                'quantity': item[3]
            })
        return cart_items

    def get_user_shipping_address(self, user_id):
        """Retrieves the shipping address of a registered user."""
        self.cursor.execute(
            "SELECT shipping_address FROM users WHERE user_id = ?",
            (user_id,),
        )
        result = self.cursor.fetchone()
        return result[0] if result else None

    def process_payment(self, user_id, total_amount, card_info=None):
        """Simulates processing a payment for the given user and amount."""
        if card_info:
            print(f"Processing payment of ${total_amount:.2f} for user ID: {user_id} using saved card: {card_info[-4:]}...")
        else:
            print(f"Processing payment of ${total_amount:.2f} for user ID: {user_id}...")
            print("No saved card information found. Assuming payment with other means...")
        # In a real application, you would integrate with a payment gateway here.
        # For this example, we will simply assume the payment is successful.
        # In a real scenario, you would check payment status and handle failures.
        return True  # Assume payment is successful

    def submit_order(self, user_id):
        """Retrieves cart items, calculates total, applies shipping, processes payment,
        and records the order if payment is successful. Checks if user is logged in
        and retrieves saved card information."""
        if not user_id:
            print("User not logged in. Please log in to checkout.")
            return None

        cart_items = self.get_cart_items(user_id)
        if not cart_items:
            print("Your cart is empty. Add items to checkout.")
            return None

        shipping_address = self.get_user_shipping_address(user_id)
        if not shipping_address:
            print("Shipping address not found for this user.")
            return None

        saved_card_info = self.get_user_payment_info(user_id)

        total_price = sum(item['price'] * item['quantity'] for item in cart_items)
        shipping_fee = 20.00
        total_amount = total_price + shipping_fee

        if self.process_payment(user_id, total_amount, saved_card_info):
            order_date = datetime.now().isoformat()
            order_details = json.dumps(cart_items)
            payment_status = "SUCCESSFUL"

            self.cursor.execute("""
                INSERT INTO orders (user_id, order_date, total_amount, shipping_address, payment_status, order_details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, order_date, total_amount, shipping_address, payment_status, order_details))
            self.conn.commit()
            order_id = self.cursor.lastrowid

            # Optionally clear the user's cart after successful checkout
            self.cursor.execute("DELETE FROM carts WHERE user_id = ?", (user_id,))
            self.conn.commit()

            print(f"Order submitted successfully! Order ID: {order_id}")
            print(f"Total amount: ${total_amount:.2f} (including ${shipping_fee:.2f} shipping)")
            return order_id
        else:
            print("Payment failed. Order not submitted.")
            return None

    def get_order_details(self, order_id):
        """Retrieves details of a specific order."""
        self.cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        order = self.cursor.fetchone()
        if order:
            return {
                'order_id': order[0],
                'user_id': order[1],
                'order_date': order[2],
                'total_amount': order[3],
                'shipping_address': order[4],
                'payment_status': order[5],
                'order_details': json.loads(order[6])
            }
        return None

    def close_connection(self):
        """Closes the database connection."""
        self.conn.close()

# --- Test the functionality ---
if __name__ == "__main__":
    checkout_system = ECommerceCheckout()

    # Add a test user with saved card information
    user1_id = checkout_system.add_user(
        username="testuser1",
        shipping_address="123 Main St, Knoxville, TN 37917",
        payment_info="1234-5678-9012-3456"
    )
    if user1_id:
        print(f"Test user 1 created with ID: {user1_id} and saved card.")

        # Add another test user without saved card information
        user2_id = checkout_system.add_user(
            username="testuser2",
            shipping_address="456 Oak Ave, Knoxville, TN 37918"
        )
        if user2_id:
            print(f"Test user 2 created with ID: {user2_id} (no saved card).")

            # Add some test products
            product1_id = checkout_system.add_product(name="Laptop", price=1200.00)
            product2_id = checkout_system.add_product(name="Mouse", price=25.00)
            if product1_id and product2_id:
                print(f"Test products created: Laptop (ID: {product1_id}), Mouse (ID: {product2_id})")

                # Add items to user 1's cart
                checkout_system.add_to_cart(user_id=user1_id, product_id=product1_id, quantity=1)
                checkout_system.add_to_cart(user_id=user1_id, product_id=product2_id, quantity=2)
                print("Items added to user 1's cart.")

                # View user 1's cart
                cart_items_user1 = checkout_system.get_cart_items(user1_id)
                print("Current cart items for user 1:", cart_items_user1)

                # Checkout the order for user 1 (logged in)
                print("\nChecking out for user 1:")
                order1_id = checkout_system.submit_order(user_id=user1_id)

                if order1_id:
                    # Retrieve and print order details for user 1
                    order1_details = checkout_system.get_order_details(order1_id)
                    print("\nOrder Details for user 1:")
                    print(f"Order ID: {order1_details['order_id']}")
                    print(f"Order Date: {order1_details['order_date']}")
                    print(f"Total Amount: ${order1_details['total_amount']:.2f}")
                    print(f"Shipping Address: {order1_details['shipping_address']}")
                    print(f"Payment Status: {order1_details['payment_status']}")
                    print("Items in Order:")
                    for item in order1_details['order_details']:
                        print(f"- {item['name']} (Quantity: {item['quantity']}, Price: ${item['price']:.2f})")

                    # Verify that the cart is now empty for user 1
                    updated_cart_items_user1 = checkout_system.get_cart_items(user1_id)
                    print("\nCart items for user 1 after checkout:", updated_cart_items_user1)
                else:
                    print("Checkout failed for user 1.")

                # Add items to user 2's cart
                checkout_system.add_to_cart(user_id=user2_id, product_id=product2_id, quantity=1)
                print("\nItems added to user 2's cart.")

                # View user 2's cart
                cart_items_user2 = checkout_system.get_cart_items(user2_id)
                print("Current cart items for user 2:", cart_items_user2)

                # Checkout the order for user 2 (logged in, no saved card)
                print("\nChecking out for user 2:")
                order2_id = checkout_system.submit_order(user_id=user2_id)

                if order2_id:
                    # Retrieve and print order details for user 2
                    order2_details = checkout_system.get_order_details(order2_id)
                    print("\nOrder Details for user 2:")
                    print(f"Order ID: {order2_details['order_id']}")
                    print(f"Order Date: {order2_details['order_date']}")
                    print(f"Total Amount: ${order2_details['total_amount']:.2f}")
                    print(f"Shipping Address: {order2_details['shipping_address']}")
                    print(f"Payment Status: {order2_details['payment_status']}")
                    print("Items in Order:")
                    for item in order2_details['order_details']:
                        print(f"- {item['name']} (Quantity: {item['quantity']}, Price: ${item['price']:.2f})")

                    # Verify that the cart is now empty for user 2
                    updated_cart_items_user2 = checkout_system.get_cart_items(user2_id)
                    print("\nCart items for user 2 after checkout:", updated_cart_items_user2)
                else:
                    print("Checkout failed for user 2.")

                # Attempt checkout for a non-logged-in user (None user_id)
                print("\nAttempting checkout for a non-logged-in user:")
                checkout_system.submit_order(user_id=None)

            else:
                print("Failed to create test products.")
        else:
            print("Failed to create test user 2.")
    else:
        print("Failed to create test user 1.")

    checkout_system.close_connection()