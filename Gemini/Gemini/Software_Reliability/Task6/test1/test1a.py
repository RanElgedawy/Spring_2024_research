from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from flask import Flask, request, render_template
from sqlalchemy import create_engine, sessionmaker

Base = declarative_base()

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    text_review = Column(String(500))
    review_score = Column(Float, nullable=False)

app = Flask(__name__)

engine = create_engine('sqlite:///reviews.db')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@app.route('/add_review', methods=['POST'])
def add_review():
    session = Session()
    user_id = 1  # Replace with actual logged-in user ID
    product_id = 2  # Replace with actual product ID
    text_review = request.form['text_review']
    review_score = float(request.form['review_score'])

    review = Review(user_id=user_id, product_id=product_id,
                    text_review=text_review, review_score=review_score)
    session.add(review)
    session.commit()
    return 'Review added successfully'

if __name__ == '__main__':
    app.run(debug=True)