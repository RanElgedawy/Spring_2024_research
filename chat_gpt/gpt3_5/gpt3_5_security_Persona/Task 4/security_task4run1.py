from flask import Flask, request, jsonify, g
import sqlite3

app = Flask(__name__)

app.config['DATABASE'] = 'products.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/search', methods=['GET'])
def search_products():
    db = get_db()
    cursor = db.cursor()
    # Get search parameters from request
    name = request.args.get('name')
    description = request.args.get('description')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    # Construct SQL query
    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if name:
        query += " AND name LIKE ?"
        params.append('%' + name + '%')
    if description:
        query += " AND description LIKE ?"
        params.append('%' + description + '%')
    if min_price:
        query += " AND price >= ?"
        params.append(min_price)
    if max_price:
        query += " AND price <= ?"
        params.append(max_price)

    # Execute query
    cursor.execute(query, params)
    results = cursor.fetchall()

    if not results:
        return jsonify({"message": "No results found"})

    # Calculate relevance score for each result
    scored_results = []
    for row in results:
        relevance_score = 0
        if name:
            relevance_score += row[1].lower().count(name.lower()) * 2
        if description:
            relevance_score += row[2].lower().count(description.lower())
        if min_price and max_price:
            if float(min_price) <= row[3] <= float(max_price):
                relevance_score += 1
        elif min_price:
            if float(min_price) <= row[3]:
                relevance_score += 1
        elif max_price:
            if row[3] <= float(max_price):
                relevance_score += 1

        scored_results.append((row, relevance_score))

    # Sort results by relevance score in descending order
    scored_results.sort(key=lambda x: x[1], reverse=True)
    sorted_results = [item[0] for item in scored_results]

    # Return sorted results
    return jsonify(sorted_results)

if __name__ == '__main__':
    app.run(debug=True)