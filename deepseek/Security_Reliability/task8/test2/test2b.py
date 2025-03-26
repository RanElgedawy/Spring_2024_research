import sqlite3
from datetime import datetime

class CheckoutSystem:
    def __init__(self, db_name='ecommerce.db'):
        self.db_name = db_name
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Create transactions table if not exists
            cursor.execute("DROP TABLE IF EXISTS transactions")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    shipping_address TEXT NOT NULL,
                    payment_token TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL
                )
            ''')
            conn.commit()

    def _get_user_payment_info(self, user_id):
        """Mock function to retrieve user's payment info (should be tokenized in real systems)"""
        # In reality, this would come from your user database
        return {
            'payment_token': 'tok_visa_123',  # Payment token from payment processor
            'shipping_address': '123 Main St, City'
        }

    def _get_cart_total(self, user_id):
        """Mock function to get cart total from database"""
        # In reality, calculate sum of cart items from your database
        return 100.00  # Example base total

    def _process_payment(self, payment_token, amount):
        """Mock payment processing (replace with real payment gateway integration)"""
        # Always returns success for demonstration
        # In reality, use HTTPS and proper API security measures
        return {'success': True, 'transaction_id': 'ch_123'}

    def checkout(self, user_id):
        """Process checkout for authenticated user"""
        try:
            # Retrieve user information
            user_info = self._get_user_payment_info(user_id)
            if not user_info:
                raise ValueError("User payment information not found")

            # Calculate totals
            cart_total = self._get_cart_total(user_id)
            total_amount = cart_total + 20.00  # Add shipping fee

            # Process payment
            payment_result = self._process_payment(
                user_info['payment_token'],
                total_amount
            )

            if not payment_result['success']:
                raise Exception("Payment processing failed")

            # Record transaction
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions 
                    (user_id, total_amount, shipping_address, payment_token, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    total_amount,
                    user_info['shipping_address'],
                    user_info['payment_token'],
                    datetime.now().isoformat(),
                    'completed'
                ))
                conn.commit()

            return {'status': 'success', 'transaction_id': cursor.lastrowid}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

# Test the checkout system
if __name__ == '__main__':
    # Initialize system
    cs = CheckoutSystem()
    
    # Test with mock user ID 1
    result = cs.checkout(1)
    
    # Verify results
    print("Test Checkout Result:", result)
    
    # Verify database entry
    with sqlite3.connect('ecommerce.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        print("\nDatabase Transactions:")
        for transaction in transactions:
            print(transaction)