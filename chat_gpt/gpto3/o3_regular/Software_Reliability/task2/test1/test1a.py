from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import uvicorn

# --- Database setup ---
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Product table
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    stock = Column(Integer)

# Define the Cart table
class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)

# Create all tables
Base.metadata.create_all(bind=engine)

# Insert sample data if products table is empty
def init_sample_data():
    db = SessionLocal()
    try:
        if db.query(Product).count() == 0:
            sample_products = [
                Product(id=1, name="Widget", price=19.99, stock=100),
                Product(id=2, name="Gadget", price=29.99, stock=50),
            ]
            db.add_all(sample_products)
            db.commit()
    finally:
        db.close()

init_sample_data()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Setup ---
app = FastAPI()

# Pydantic models for request/response
class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    stock: int

class CartItem(BaseModel):
    product_id: int
    quantity: int = 1

# Endpoint to get product details by product_id
@app.get("/product/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# Endpoint to add a product to the authenticated user's cart
@app.post("/cart/add")
def add_to_cart(item: CartItem, db: Session = Depends(get_db), x_user_id: str = Header(...)):
    # Retrieve the product and check if it exists and has enough stock.
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")
    
    # Deduct stock from the product
    product.stock -= item.quantity

    # Check if this product is already in the user's cart and update the quantity.
    cart_item = db.query(Cart).filter(Cart.user_id == x_user_id, Cart.product_id == item.product_id).first()
    if cart_item:
        cart_item.quantity += item.quantity
    else:
        new_cart_item = Cart(user_id=x_user_id, product_id=item.product_id, quantity=item.quantity)
        db.add(new_cart_item)
    
    db.commit()
    return {"message": "Product added to cart"}

# Endpoint to get the current cart for the authenticated user
@app.get("/cart")
def get_cart(x_user_id: str = Header(...), db: Session = Depends(get_db)):
    cart_items = db.query(Cart).filter(Cart.user_id == x_user_id).all()
    cart_data = [{"product_id": item.product_id, "quantity": item.quantity} for item in cart_items]
    return {"user_id": x_user_id, "cart": cart_data}

# --- Testing ---
# You can run this script and then test the API.
# Example using curl:
#   1. Retrieve product info:
#       curl -X GET "http://127.0.0.1:8000/product/1"
#
#   2. Add product to cart:
#       curl -X POST "http://127.0.0.1:8000/cart/add" -H "Content-Type: application/json" -H "X-User-ID: user123" -d '{"product_id": 1, "quantity": 2}'
#
#   3. View cart:
#       curl -X GET "http://127.0S.0.1:8000/cart" -H "X-User-ID: user123"

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)
