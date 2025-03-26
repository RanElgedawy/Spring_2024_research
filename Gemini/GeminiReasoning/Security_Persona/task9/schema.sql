CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL -- In a real app, use proper hashing
);

CREATE TABLE IF NOT EXISTS newsletter_subscriptions (
    user_id INTEGER PRIMARY KEY,
    is_subscribed INTEGER NOT NULL DEFAULT 1, -- 1 for subscribed, 0 for unsubscribed
    unsubscribe_reason TEXT,
    unsubscribe_timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS unsubscribe_tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expiry_timestamp DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);