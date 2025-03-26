import sqlite3
import requests  # For payment processing

def checkout(user_id):
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()

    # Retrieve cart items
    cursor.execute("SELECT product_id, quantity, price FROM cart WHERE user_id=?", (user_id,))
    cart_items = cursor.fetchall()

    # Retrieve shipping address
    cursor.execute("SELECT shipping_address FROM users WHERE user_id=?", (user_id,))
    shipping_address = cursor.fetchone()[0]

    # Calculate total
    total_amount = 20  # Shipping fee
    for item in cart_items:
        total_amount += item[2] * item[1]

    # Process payment (simplified, replace with actual payment gateway integration)
    payment_successful = process_payment(user_id, total_amount)
    if not payment_successful:
        return "Payment failed"

    # Submit order
    cursor.execute("INSERT INTO orders (user_id, total_amount, shipping_address) VALUES (?, ?, ?)",
                   (user_id, total_amount, shipping_address))
    order_id = cursor.lastrowid

    # Add order items
    for item in cart_items:
        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                       (order_id, item[0], item[1], item[2]))

    # Update inventory (simplified, consider more robust inventory management)
    for item in cart_items:
        cursor.execute("UPDATE products SET quantity = quantity - ? WHERE product_id = ?", (item[1], item[0]))

    # Clear cart
    cursor.execute("DELETE FROM cart WHERE user_id=?", (user_id,))

    conn.commit()
    conn.close()

    return "Order placed successfully!"

# Simplified payment processing function (replace with actual integration)
def process_payment(user_id, amount):
    # Replace with your payment gateway's API calls
    # ...
    return True  # Assuming successful payment

# Testing
def test_checkout():
    # ... (Add test cases to cover various scenarios, e.g., empty cart, insufficient funds, etc.)