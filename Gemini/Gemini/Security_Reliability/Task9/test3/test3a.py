import smtplib
from random import choices
from string import ascii_letters, digits

def send_unsubscribe_email(email):
    # Generate a random token
    token = ''.join(choices(ascii_letters + digits, k=32))

    # Store the token in a temporary table or database
    # ...

    # Send the email with a link containing the email and token
    # ...

# ... (verify token and email)

    if verification_successful:
        # Display a form to confirm unsubscription
        # ...
    
    if user_confirmed_unsubscription:
    # Update the users table
    cursor.execute("UPDATE users SET is_subscribed = 0 WHERE email = ?", (user_email,))

    # Store the reason in the subscription_preferences table
    cursor.execute("INSERT INTO subscription_preferences (user_id, reason_for_unsubscription) VALUES (?, ?)", (user_id, reason))