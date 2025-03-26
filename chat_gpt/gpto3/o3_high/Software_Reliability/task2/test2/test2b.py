from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Use SQLite; the DB file (ecommerce.db) will be created in the same directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ----------------------
# Database Models
# ----------------------

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

# ----------------------
# API Endpoints
# ----------------------

@app.route('/product/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Retrieve product information by product ID.
    """
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock
        })
    else:
        return jsonify({"error": "Product not found"}), 404

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    """
    Add a product to a user's cart if the product has stock.
    User identification is handled via the 'X-User-ID' header.
    The request JSON must include a 'product_id' and can optionally include 'quantity' (default 1).
    """
    data = request.get_json()
    if not data or 'product_id' not in data:
        return jsonify({"error": "Missing product_id in request body"}), 400

    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    
    # Get user identification from header (assumes authenticated users)
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        return jsonify({"error": "Missing X-User-ID header"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"error": "Invalid X-User-ID header"}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    # Ensure the product has sufficient stock available.
    if product.stock < quantity:
        return jsonify({"error": "Not enough stock available"}), 400

    # Check if the product is already in the user's cart
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)

    # (Optional) If you wish to reduce stock when a product is added to the cart,
    # uncomment the following line. Otherwise, leave the product stock unchanged until checkout.
    # product.stock -= quantity

    db.session.commit()
    return jsonify({
        "message": "Product added to cart",
        "cart_item": {"user_id": user_id, "product_id": product_id, "quantity": cart_item.quantity}
    })

# ----------------------
# Initialize DB and Sample Data
# ----------------------

if __name__ == "__main__":
    db.drop_all()
    db.create_all()
    # Add sample products if none exist
    if Product.query.count() == 0:
        sample_products = [
            Product(name="Product A", description="Description of product A", price=9.99, stock=10),
            Product(name="Product B", description="Description of product B", price=19.99, stock=5),
        ]
        db.session.bulk_save_objects(sample_products)
        db.session.commit()
        print("Sample products added to the database.")
    
    # Run the Flask development server
    app.run(debug=True)
