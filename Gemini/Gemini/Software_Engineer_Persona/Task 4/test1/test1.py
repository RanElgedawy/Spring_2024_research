from flask import Flask, request
import sqlite3
import re

app = Flask(__name__)

db_file = 'products.db'

def create_search_index(db_file):
  """Creates a database with a search index table."""
  conn = sqlite3.connect(db_file)
  c = conn.cursor()

  c.execute("DROP TABLE IF EXISTS products")
  c.execute("DROP TABLE IF EXISTS search_index")

  c.execute('''CREATE TABLE IF NOT EXISTS products (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 description TEXT
              )''')

  c.execute('''CREATE TABLE IF NOT EXISTS search_index (
                 product_id INTEGER,
                 word TEXT,
                 position INTEGER
              )''')

  conn.commit()
  conn.close()

create_search_index(db_file)

def index_product(db_file, product_id, name, description):
  """Indexes a product in the search index."""
  conn = sqlite3.connect(db_file)
  c = conn.cursor()

  # Insert the product into the products table
  c.execute("INSERT INTO products (id, name, description) VALUES (?, ?, ?)", (product_id, name, description))

  # Create search index entries for each word in the name and description
  words = re.findall(r'\w+', name.lower() + ' ' + description.lower())
  for i, word in enumerate(words):
    c.execute("INSERT INTO search_index (product_id, word, position) VALUES (?, ?, ?)", (product_id, word, i + 1))
  conn.commit()
  conn.close()

def search_products(db_file, query):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()

    # Split the query into words
    words = re.findall(r'\w+', query.lower())

    c.execute('''CREATE TEMPORARY TABLE matching_products AS
                 SELECT products.id, products.name, products.description
                 FROM products JOIN search_index ON products.id = search_index.product_id
                 WHERE search_index.word = ?''', (words[0],))  # Use first word for table creation

    final_results = []
    # Add matching products for each word
    for word in words[1:]:
        c.execute('''INSERT INTO matching_products
                 SELECT products.id, products.name, products.description
                 FROM products JOIN search_index ON products.id = search_index.product_id
                 WHERE search_index.word = ?''', (word,))
        final_results.extend(set([row[0] for row in c.fetchall()]))

    if not final_results:
        return "No results found"

    # Fetch product details based on final_results
    c.execute("SELECT id, name, description FROM products WHERE id IN (?)", (tuple(final_results),))
    results = c.fetchall()

    conn.close()
    return results

@app.route('/search')
def search():
  query = request.args.get('query')

  if not query:
    return "Please provide a query parameter."

  results = search_products(db_file, query)
  return results

if __name__ == '__main__':
  # Insert test data
  index_product(db_file, 1, "Laptop", "A powerful laptop with a 15-inch screen.")
  index_product(db_file, 2, "Smartphone", "A high-end smartphone with a great camera.")
  index_product(db_file, 3, "Headphones", "Wireless headphones with excellent sound quality.")
  index_product(db_file, 4, "Gaming Mouse", "A high-precision gaming mouse with RGB lighting.")
  index_product(db_file, 5, "Wireless Keyboard", "A comfortable wireless keyboard with backlit keys.")

  app.run(debug=True)