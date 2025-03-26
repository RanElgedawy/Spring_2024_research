from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db.init_app(app)

class SearchForm(FlaskForm):
    query = StringField('Search')
    submit = SubmitField('Search')

@app.route('/', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        query = form.query.data
        results = Product.query.filter(
            Product.name.ilike(f'%{query}%') |
            Product.description.ilike(f'%{query}%')
        ).all()
        return render_template('search_results.html', results=results)
    return render_template('search.html', form=form)