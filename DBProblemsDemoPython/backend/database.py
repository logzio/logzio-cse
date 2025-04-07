import os
import time
import mysql.connector
import logging
from mysql.connector import Error
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters from environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'mysql'),
    'user': os.environ.get('DB_USER', 'dbuser'),
    'password': os.environ.get('DB_PASSWORD', 'dbpassword'),
    'database': os.environ.get('DB_NAME', 'dbproblems')
}

def get_db_connection(config=None):
    """
    Create a database connection with optional custom config
    This allows simulation of connection issues with alternative configs
    """
    if config is None:
        config = DB_CONFIG
    
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise

def wait_for_db():
    """Wait for database to be available"""
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            conn = get_db_connection()
            if conn.is_connected():
                conn.close()
                logger.info("Database is ready")
                return True
        except Error as e:
            logger.warning(f"Database not ready (attempt {i+1}/{max_retries}): {e}")
            time.sleep(retry_interval)
    
    logger.error("Failed to connect to database after maximum retries")
    return False
def efficient_bulk_query(table_name, filter_dict=None, limit=None, batch_size=1000):
    """
    Perform an efficient bulk query with batching and connection reuse.
    
    Args:
        table_name: Name of the table to query
        filter_dict: Dictionary of column:value pairs for WHERE clause
        limit: Maximum number of records to return
        batch_size: Number of records to fetch in each batch
    
    Returns:
        List of records as dictionaries
    """
    results = []
    processed = 0
    
    # Build the query
    query = f"SELECT * FROM {table_name}"
    params = []
    
    if filter_dict:
        conditions = []
        for column, value in filter_dict.items():
            conditions.append(f"{column} = %s")
            params.append(value)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    
    query += f" LIMIT {batch_size}"
    if limit:
        query += f" OFFSET %s"
    
    # Get a connection from the pool
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Fetch data in batches to avoid memory issues
        offset = 0
        while True:
            if limit and offset >= limit:
                break
                
            # Adjust batch size for the last batch if limit is set
            if limit and offset + batch_size > limit:
                current_batch_size = limit - offset
                current_query = query.replace(f"LIMIT {batch_size}", f"LIMIT {current_batch_size}")
            else:
                current_query = query
                
            # Set the offset parameter if needed
            current_params = params.copy()
            if limit:
                current_params.append(offset)
                
            # Execute the query
            cursor.execute(current_query, current_params)
            batch = cursor.fetchall()
            
            # Break if no more results
            if not batch:
                break
                
            # Add results and update counters
            results.extend(batch)
            processed += len(batch)
            offset += batch_size
            
            # Break if we've reached the limit
            if limit and processed >= limit:
                break
                
        return results
        
    finally:
        # Clean up resources
        cursor.close()
        conn.close()
def initialize_db():
    """Initialize database with test tables and data"""
    logger.info("Initializing database...")
    
    if not wait_for_db():
        raise Exception("Database initialization failed: could not connect to database")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            inventory INT NOT NULL DEFAULT 0
        )
        """)
        
        # Create orders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create order_items table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        """)
        
        # Insert test users if they don't exist
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            test_users = [
                ('user1', 'user1@example.com'),
                ('user2', 'user2@example.com'),
                ('user3', 'user3@example.com'),
                ('user4', 'user4@example.com'),
                ('user5', 'user5@example.com')
            ]
            cursor.executemany("INSERT INTO users (username, email) VALUES (%s, %s)", test_users)
            
            # Insert test products
            test_products = [
                ('Product A', 19.99, 100),
                ('Product B', 29.99, 50),
                ('Product C', 9.99, 200),
                ('Product D', 49.99, 30),
                ('Product E', 99.99, 10)
            ]
            cursor.executemany("INSERT INTO products (name, price, inventory) VALUES (%s, %s, %s)", test_products)
            
            # Insert test orders
            for i in range(1, 6):
                cursor.execute(
                    "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)",
                    (random.randint(1, 5), random.uniform(20, 500))
                )
                order_id = cursor.lastrowid
                
                # Insert order items
                for j in range(1, random.randint(1, 4)):
                    product_id = random.randint(1, 5)
                    quantity = random.randint(1, 5)
                    
                    cursor.execute("SELECT price FROM products WHERE id = %s", (product_id,))
                    price = cursor.fetchone()[0]
                    
                    cursor.execute(
                        "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                        (order_id, product_id, quantity, price)
                    )
        
        conn.commit()
        logger.info("Database initialized successfully")
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()