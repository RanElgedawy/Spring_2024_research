import sqlite3
import flask
import flask_login

app = flask.Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key

db_path = 'ecommerce.db'

def init_db():
    with app.app_context():
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DROP TABLE IF EXISTS users")
        c.execute("DROP TABLE IF EXISTS products")

        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     id INTEGER PRIMARY KEY,
                     username TEXT UNIQUE NOT NULL,
                     password TEXT NOT NULL,
                     is_admin BOOLEAN DEFAULT 0
                 )''')

        c.execute('''CREATE TABLE IF NOT EXISTS products (
                     id INTEGER PRIMARY KEY,
                     name TEXT NOT NULL,
                     description TEXT,
                     price REAL,
                     quantity INTEGER
                 )''')

        conn.commit()
        conn.close()

init_db()

class User(flask_login.UserMixin):
    def __init__(self, id, username, is_admin):
        self.id = id
        self.username = username
        self.is_admin = is_admin

login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, is_admin FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        if user:
            return User(user[0], user[1], user[2])
        return None

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        return "You don't have admin privileges."

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name, description, price, quantity FROM products")
        products = c.fetchall()
    return render_template('admin_products.html', products=products)

# ... Implement routes for adding, editing, and deleting products ...