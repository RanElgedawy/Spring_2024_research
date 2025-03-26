import pytest
from test2 import app, db
from test2 import User, Cart, CartItem

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    client = app.test_client()
    with app.app_context():
        db.create_all() 
    return client

def test_checkout(client):
    print("Running test_checkout")
    # Create a test user and cart
    user = User(id=1)
    db.session.add(user)
    db.session.commit()

    cart = Cart(user_id=1)
    cart_item = CartItem(cart_id=1, product_id=1, quantity=2)
    db.session.add(cart)
    db.session.add(cart_item)
    db.session.commit()

    # Simulate a checkout request
    response = client.post('/checkout', json={'user_id': 1})
    assert response.status_code == 200

if __name__ == "__main__":
  pytest.main()