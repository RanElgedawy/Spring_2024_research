from flask import Flask, request, jsonify, g
import sqlite3
from contextlib import closing
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__)

# Create a database connection and set up the table
def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("Connected to SQLite database")
    except sqlite3.Error as e:
        print(f"Error connecting to db: {e}")
    return conn

def create_table(conn, sql):
    try:
        with closing(conn.cursor()) as c:
            c.execute(sql)
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

# Define the SQL statements
create_reviews_table_sql = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    review TEXT,
    score INTEGER
);
"""

# Create users and products tables
create_users_table_sql = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);
"""

create_products_table_sql = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL
);
"""

create_purchases_table_sql = """
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES 
 products(id)
);
"""

# Create the database and table
conn = create_connection("reviews.db")

create_table(conn, create_reviews_table_sql)
create_table(conn, create_users_table_sql)
create_table(conn, create_products_table_sql)
create_table(conn, create_purchases_table_sql)

# Initialize SQLAlchemy
engine = create_engine('sqlite:///reviews.db', connect_args={'check_same_thread': False})  # Disable same-thread check
Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)

class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))


    user = relationship(User)
    product = relationship(Product)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    review = Column(String)
    score = Column(Integer)

    user = relationship(User)
    product = relationship(Product)

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    yield db

def close_db(db):
    db.close()


app = Flask(__name__)
@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_db', None)
    if db is not None:
        close_db(db)

# Make db session available globally
app.app_context().push()

# API endpoint to submit reviews
@app.route('/submit_review', methods=['POST'])
def submit_review():
    user_id = request.json['user_id']
    product_id = request.json['product_id']
    review_text = request.json['review']
    review_score = request.json['score']

    # Validate review text and score
    if not review_text:
        return jsonify({'message': 'Review text is required'}), 400
    try:
        review_score = int(review_score)
        if review_score < 1 or review_score > 5:
            return jsonify({'message': 'Review score must be between 1 and 5'}), 400
    except ValueError:
        return jsonify({'message': 'Review score must be an integer'}), 400

    with app.app_context():  # Get session from context
        db = get_db()

        # Validate user existence
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'message': 'User does not exist'}), 400

        # Validate product purchase
        product = db.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({'message': 'Product does not exist'}), 400

        # Check if user has purchased the product (assuming you have a 'purchases' table)
        purchase = db.query(Purchase).filter_by(user_id=user_id, product_id=product_id).first()
        if not purchase:
            return jsonify({'message': 'User has not purchased this product'}), 400

        # Insert review into the database
        review = Review(user=user, product=product, review=review_text, score=review_score)
        db.add(review)
        db.commit()

    return jsonify({'message': 'Review submitted successfully'})

def insert_test_data(conn):
    with closing(conn.cursor()) as cursor:
        cursor.execute("INSERT INTO users (name, email) VALUES ('Test User', 'testuser@example.com')")
        cursor.execute("INSERT INTO products (name, price) VALUES ('Test Product', 19.99)")
        cursor.execute("INSERT INTO purchases (user_id, product_id) VALUES (1, 1)")  # Assuming user_id 1 and product_id 1 exist

        conn.commit()

# Call this function to drop all tables
if __name__ == '__main__':
    # insert_test_data(conn)
    app.run(debug=True)