from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_cart_items(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT products.name, cart.quantity, products.price FROM cart JOIN products ON cart.product_id = products.product_id WHERE cart.user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def get_shipping_address(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT shipping_address FROM users WHERE user_id = ?', (user_id,))
    address = cursor.fetchone()['shipping_address']
    conn.close()
    return address

def calculate_total(items):
    total = sum(item['quantity'] * item['price'] for item in items)
    total += 20  # Shipping fee
    return total

# ... (Payment processing integration)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        user_id = 1  # Replace with actual user ID
        items = get_cart_items(user_id)
        shipping_address = get_shipping_address(user_id)
        total = calculate_total(items)

        # Process payment
        if process_payment(total):
            # Submit order
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO orders (user_id, total_price, shipping_address, order_date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)', (user_id, total, shipping_address))
            order_id = cursor.lastrowid
            for item in items:
                cursor.execute('INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)', (order_id, item['product_id'], item['quantity'], item['price']))
            conn.commit()
            conn.close()

            # Update inventory (if necessary)
            # Send order confirmation

            return redirect(url_for('order_confirmation'))
        else:
            return render_template('checkout.html', items=items, shipping_address=shipping_address, total=total, error='Payment failed')
    else:
        items = get_cart_items(user_id)
        shipping_address = get_shipping_address(user_id)
        total = calculate_total(items)
        return render_template('checkout.html', items=items, shipping_address=shipping_address, total=total)