from flask import Flask, request, jsonify
import bcrypt

app = Flask(__name__)

# ... (database connection and table creation)

@app.route('/register', methods=['POST'])
def register():
    # ... (validate data, hash password, store in database)

@app.route('/login', methods=['POST'])
def login():
    # ... (validate data, retrieve user, compare passwords, generate token)

if __name__ == '__main__':
    app.run()