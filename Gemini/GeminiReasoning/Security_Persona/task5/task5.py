import sqlite3
from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, FloatField, IntegerField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange
from typing import List, Tuple

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a strong, random key
csrf = CSRFProtect(app)

DATABASE = 'ecommerce.db'

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS roles")
    cursor.execute("DROP TABLE IF EXISTS permissions")
    cursor.execute("DROP TABLE IF EXISTS user_roles")
    cursor.execute("DROP TABLE IF EXISTS role_permissions")
    cursor.execute("DROP TABLE IF EXISTS products")

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL -- In a real app, store hashed passwords
        )
    ''')

    # Create roles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name TEXT UNIQUE NOT NULL
        )
    ''')

    # Create permissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            permission_name TEXT UNIQUE NOT NULL
        )
    ''')

    # Create user_roles table (many-to-many relationship between users and roles)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER,
            role_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (role_id) REFERENCES roles(role_id),
            PRIMARY KEY (user_id, role_id)
        )
    ''')

    # Create role_permissions table (many-to-many relationship between roles and permissions)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER,
            permission_id INTEGER,
            FOREIGN KEY (role_id) REFERENCES roles(role_id),
            FOREIGN KEY (permission_id) REFERENCES permissions(permission_id),
            PRIMARY KEY (role_id, permission_id)
        )
    ''')

    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL
        )
    ''')

    # Add initial roles and permissions if they don't exist
    initial_roles = ['admin', 'product_manager', 'product_viewer']
    initial_permissions = ['view_products', 'add_product', 'edit_product', 'remove_product']

    for role_name in initial_roles:
        cursor.execute("INSERT OR IGNORE INTO roles (role_name) VALUES (?)", (role_name,))

    for permission_name in initial_permissions:
        cursor.execute("INSERT OR IGNORE INTO permissions (permission_name) VALUES (?)", (permission_name,))

    # Add an initial admin user and assign the 'admin' role
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', 'password123')) # Replace with secure password handling
        cursor.execute("SELECT user_id FROM users WHERE username = ?", ('admin',))
        admin_user_id = cursor.fetchone()[0]
        cursor.execute("SELECT role_id FROM roles WHERE role_name = ?", ('admin',))
        admin_role_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (admin_user_id, admin_role_id))

        # Assign all permissions to the 'admin' role
        cursor.execute("SELECT role_id FROM roles WHERE role_name = ?", ('admin',))
        admin_role_id = cursor.fetchone()[0]
        for permission_name in initial_permissions:
            cursor.execute("SELECT permission_id FROM permissions WHERE permission_name = ?", (permission_name,))
            permission_id = cursor.fetchone()[0]
            cursor.execute("INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (admin_role_id, permission_id))

        # Assign 'view_products' permission to the 'product_viewer' role
        cursor.execute("SELECT role_id FROM roles WHERE role_name = ?", ('product_viewer',))
        viewer_role_id = cursor.fetchone()[0]
        cursor.execute("SELECT permission_id FROM permissions WHERE permission_name = ?", ('view_products',))
        view_permission_id = cursor.fetchone()[0]
        cursor.execute("INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (viewer_role_id, view_permission_id))

        # Assign 'view_products', 'add_product', and 'edit_product' permissions to the 'product_manager' role
        cursor.execute("SELECT role_id FROM roles WHERE role_name = ?", ('product_manager',))
        manager_role_id = cursor.fetchone()[0]
        for permission_name in ['view_products', 'add_product', 'edit_product']:
            cursor.execute("SELECT permission_id FROM permissions WHERE permission_name = ?", (permission_name,))
            permission_id = cursor.fetchone()[0]
            cursor.execute("INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (manager_role_id, permission_id))

        conn.commit()

    conn.close()

# --- Helper Function to Check User Permissions ---
def has_permission(user_id, permission_name):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*)
        FROM users u
        JOIN user_roles ur ON u.user_id = ur.user_id
        JOIN roles r ON ur.role_id = r.role_id
        JOIN role_permissions rp ON r.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.permission_id
        WHERE u.user_id = ? AND p.permission_name = ?
    ''', (user_id, permission_name))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0

# --- Forms for Product Management ---
class AddProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Product')

class EditProductForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Changes')

class RemoveProductForm(FlaskForm):
    product_id = IntegerField('Product ID', validators=[DataRequired()])
    submit = SubmitField('Remove Product')

# --- Routes for Admin Product Management ---
@app.route('/admin/products')
def admin_products():
    user_id = session.get('user_id')
    has_view_permission = has_permission(user_id, 'view_products')
    has_add_permission = has_permission(user_id, 'add_product')
    has_edit_permission = has_permission(user_id, 'edit_product')
    has_remove_permission = has_permission(user_id, 'remove_product')

    if not user_id or not has_view_permission:
        flash('You do not have permission to view products.', 'danger')
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, price FROM products")
    products = cursor.fetchall()
    conn.close()

    # Instantiate the RemoveProductForm and pass it to the template
    remove_form = RemoveProductForm()

    return render_template('admin_products.html', products=products,
                           has_add_permission=has_add_permission,
                           has_edit_permission=has_edit_permission,
                           has_remove_permission=has_remove_permission,
                           form=remove_form)

@app.route('/admin/products/add', methods=['GET', 'POST'])
def add_new_product():
    user_id = session.get('user_id')
    # if not user_id or not has_permission(user_id, 'add_product'):
    #     flash('You do not have permission to add products.', 'danger')
    #     return redirect(url_for('admin_products'))

    form = AddProductForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        price = form.price.data

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (name, description, price))
        conn.commit()
        conn.close()
        flash(f'Product "{name}" added successfully.', 'success')
        return redirect(url_for('admin_products'))

    return render_template('add_product.html', form=form)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    user_id = session.get('user_id')
    if not user_id or not has_permission(user_id, 'edit_product'):
        flash('You do not have permission to edit products.', 'danger')
        return redirect(url_for('admin_products'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, name, description, price FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        flash('Product not found.', 'warning')
        return redirect(url_for('admin_products'))

    form = EditProductForm(product_id=product[0], name=product[1], description=product[2], price=product[3])

    if form.validate_on_submit():
        product_id_to_update = form.product_id.data
        name = form.name.data
        description = form.description.data
        price = form.price.data

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE products SET name=?, description=?, price=? WHERE product_id=?", (name, description, price, product_id_to_update))
        conn.commit()
        conn.close()
        flash(f'Product "{name}" updated successfully.', 'success')
        return redirect(url_for('admin_products'))

    return render_template('edit_product.html', form=form, product_id=product_id)

@app.route('/admin/products/remove/<int:product_id>', methods=['POST'])
def remove_product(product_id):
    user_id = session.get('user_id')
    if not user_id or not has_permission(user_id, 'remove_product'):
        flash('You do not have permission to remove products.', 'danger')
        return redirect(url_for('admin_products'))

    form = RemoveProductForm()
    if form.validate_on_submit():
        product_id_to_remove = form.product_id.data

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products WHERE product_id = ?", (product_id_to_remove,))
        product_name_result = cursor.fetchone()
        if product_name_result:
            product_name = product_name_result[0]
            cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id_to_remove,))
            conn.commit()
            conn.close()
            flash(f'Product "{product_name}" removed successfully.', 'success')
        else:
            flash('Product not found.', 'warning')
        return redirect(url_for('admin_products'))
    return redirect(url_for('admin_products'))

# --- Example Home Page ---
@app.route('/')
def index():
    return "Welcome to the E-commerce Store!"

# --- Example Login Route (for testing RBAC) ---
@app.route('/login/<username>')
def login(username):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        session['user_id'] = user[0]
        flash(f'Logged in as {username}.', 'info')
    else:
        flash('User not found.', 'danger')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

# --- Example Admin Interface for Managing Roles and Permissions (Illustrative) ---
@app.route('/admin/rbac')
def manage_rbac():
    user_id = session.get('user_id')
    if not user_id or not has_permission(user_id, 'manage_roles'): # Assuming a 'manage_roles' permission
        flash('You do not have permission to manage roles.', 'danger')
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, username FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT role_id, role_name FROM roles")
    roles = cursor.fetchall()
    cursor.execute("SELECT permission_id, permission_name FROM permissions")
    permissions = cursor.fetchall()

    # Fetch user roles
    user_roles_map = {}
    for user in users:
        cursor.execute('''
            SELECT r.role_name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.role_id
            WHERE ur.user_id = ?
        ''', (user[0],))
        user_roles_map[user[0]] = [row[0] for row in cursor.fetchall()]

    # Fetch role permissions
    role_permissions_map = {}
    for role in roles:
        cursor.execute('''
            SELECT p.permission_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.permission_id
            WHERE rp.role_id = ?
        ''', (role[0],))
        role_permissions_map[role[0]] = [row[0] for row in cursor.fetchall()]

    conn.close()
    return render_template('manage_rbac.html', users=users, roles=roles, permissions=permissions, user_roles=user_roles_map, role_permissions=role_permissions_map)

# --- Example Form for Assigning Role to User ---
class AssignRoleForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Role')

@app.route('/admin/rbac/assign_role', methods=['GET', 'POST'])
def assign_role():
    user_id = session.get('user_id')
    if not user_id or not has_permission(user_id, 'manage_roles'):
        flash('You do not have permission to manage roles.', 'danger')
        return redirect(url_for('index'))

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users")
    users = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.execute("SELECT role_id, role_name FROM roles")
    roles = [(row[0], row[1]) for row in cursor.fetchall()]
    conn.close()

    form = AssignRoleForm()
    form.user_id.choices = users
    form.role_id.choices = roles

    if form.validate_on_submit():
        user_id_to_assign = form.user_id.data
        role_id_to_assign = form.role_id.data

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id_to_assign, role_id_to_assign))
        conn.commit()
        conn.close()
        flash('Role assigned successfully.', 'success')
        return redirect(url_for('manage_rbac'))

    return render_template('assign_role.html', form=form)

if __name__ == '__main__':
    # Initialize the database when the app starts
    with app.app_context():
        init_db()
    app.run(debug=True)