from flask import Flask, request, render_template_string, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///newsletter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    is_subscribed = db.Column(db.Boolean, default=True)
    reason = db.Column(db.String(255), nullable=True)

# Create database and tables
with app.app_context():
    db.drop_all()
    db.create_all()

# HTML form for unsubscribing
unsubscribe_form = """
<!DOCTYPE html>
<html>
<head>
    <title>Unsubscribe</title>
</head>
<body>
    <h1>Unsubscribe from Newsletter</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul>
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    
    <form method="POST">
        <label for="email">Enter your email to confirm unsubscription:</label><br>
        <input type="email" id="email" name="email" required><br><br>
        <label for="reason">Optional: Reason for unsubscription:</label><br>
        <textarea id="reason" name="reason" rows="4" cols="50"></textarea><br><br>
        <input type="submit" value="Unsubscribe">
    </form>
</body>
</html>
"""

# Route for unsubscribing
@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'POST':
        email = request.form['email']
        reason = request.form['reason']

        # Verify user identity and update the database
        user = User.query.filter_by(email=email).first()

        if user:
            if user.is_subscribed:
                user.is_subscribed = False
                if reason:
                    user.reason = reason
                db.session.commit()
                flash('You have successfully unsubscribed from the newsletter.', 'success')
            else:
                flash('You are already unsubscribed from the newsletter.', 'warning')
        else:
            flash('No user found with that email address.', 'danger')

        return redirect(url_for('unsubscribe'))

    return render_template_string(unsubscribe_form)

# Test route to add dummy users (for testing purposes)
@app.route('/add_dummy_users')
def add_dummy_users():
    dummy_users = [
        User(email='user1@example.com'),
        User(email='user2@example.com'),
        User(email='user3@example.com')
    ]
    db.session.add_all(dummy_users)
    db.session.commit()
    return "Dummy users added!"

# Route to view all users (for testing purposes)
@app.route('/users')
def view_users():
    users = User.query.all()
    user_list = "<ul>"
    for user in users:
        user_list += f"<li>{user.email} - Subscribed: {user.is_subscribed} - Reason: {user.reason}</li>"
    user_list += "</ul>"
    return user_list

if __name__ == '__main__':
    app.run(debug=True)
