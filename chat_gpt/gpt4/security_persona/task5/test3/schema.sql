DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS products;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL
);

-- Insert an admin user (replace with your desired username and password)
INSERT INTO users (username, password, is_admin) VALUES ('admin', 'scrypt:32768:8:1$rqGaRAZXBuK4qZ0z$f67407cb8f5da4d03d9ff386f8902c527a4c61efda84ef5f0b62b93d5e490d04e5fc6a792071a02100ddb8d8896b694ad9951323d25e9fee47db7ddd14afd468', 1);