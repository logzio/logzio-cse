-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS dbproblems;
USE dbproblems;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    inventory INT NOT NULL DEFAULT 0
);

-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create order_items table
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Insert some sample data
INSERT INTO users (username, email) VALUES
    ('user1', 'user1@example.com'),
    ('user2', 'user2@example.com'),
    ('user3', 'user3@example.com'),
    ('user4', 'user4@example.com'),
    ('user5', 'user5@example.com');

INSERT INTO products (name, price, inventory) VALUES
    ('Product A', 19.99, 100),
    ('Product B', 29.99, 50),
    ('Product C', 9.99, 200),
    ('Product D', 49.99, 30),
    ('Product E', 99.99, 10);

-- Insert some sample orders and order items
INSERT INTO orders (user_id, total_amount) VALUES
    (1, 59.97),
    (2, 149.97),
    (3, 29.98),
    (4, 199.98),
    (5, 89.95);

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 1, 3, 19.99),
    (2, 4, 3, 49.99),
    (3, 3, 3, 9.99),
    (4, 5, 2, 99.99),
    (5, 2, 3, 29.99);