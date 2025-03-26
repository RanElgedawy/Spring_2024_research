import sqlite3

# Connect to the database
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Retrieve all users from the database
c.execute('SELECT * FROM users')
users = c.fetchall()

# Print every user
for user in users:
    print(user)

# Close the database connection
conn.close()