import time
import random
import logging
import threading
from mysql.connector import Error
from database import get_db_connection, DB_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary of database problems to simulate
DB_PROBLEMS = {
    "connection_timeout": {
        "name": "Connection Timeout",
        "description": "Simulates a database connection timeout",
        "category": "connectivity"
    },
    "slow_query": {
        "name": "Slow Query",
        "description": "Executes a very inefficient query that takes a long time to complete",
        "category": "performance"
    },
    "connection_pool_exhaustion": {
        "name": "Connection Pool Exhaustion",
        "description": "Opens many connections without closing them, exhausting the connection pool",
        "category": "resources"
    },
    "deadlock": {
        "name": "Deadlock",
        "description": "Creates two transactions that deadlock with each other",
        "category": "concurrency"
    },
    "table_lock": {
        "name": "Table Lock",
        "description": "Locks a table for a long time, blocking other operations",
        "category": "concurrency"
    },
    "memory_leak": {
        "name": "Memory Leak",
        "description": "Simulates a memory leak by fetching large result sets",
        "category": "resources"
    },
    "connection_drop": {
        "name": "Connection Drop",
        "description": "Abruptly closes a connection during a transaction",
        "category": "connectivity"
    },
    "query_error": {
        "name": "Query Error",
        "description": "Executes a query with syntax or semantic errors",
        "category": "errors"
    }
}

def simulate_db_problem(problem_id):
    """Simulate a specific database problem"""
    logger.info(f"Simulating database problem: {problem_id}")
    
    if problem_id == "connection_timeout":
        return simulate_connection_timeout()
    
    elif problem_id == "slow_query":
        return simulate_slow_query()
    
    elif problem_id == "connection_pool_exhaustion":
        return simulate_connection_pool_exhaustion()
    
    elif problem_id == "deadlock":
        return simulate_deadlock()
    
    elif problem_id == "table_lock":
        return simulate_table_lock()
    
    elif problem_id == "memory_leak":
        return simulate_memory_leak()
    
    elif problem_id == "connection_drop":
        return simulate_connection_drop()
    
    elif problem_id == "query_error":
        return simulate_query_error()
    
    else:
        raise ValueError(f"Unknown problem ID: {problem_id}")


def simulate_connection_timeout():
    """Simulate a database connection timeout by trying to connect to a non-responsive DB"""
    try:
        bad_config = DB_CONFIG.copy()
        bad_config['host'] = 'non-existent-host'
        bad_config['connect_timeout'] = 5
        
        logger.info("Attempting connection to non-existent host...")
        conn = get_db_connection(bad_config)
        conn.close()
    except Error as e:
        logger.error(f"Connection timeout error: {e}")
        return {
            "problem": "connection_timeout",
            "status": "simulated",
            "error": str(e)
        }

def simulate_slow_query():
    """Simulate a slow query by executing an inefficient query"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logger.info("Executing slow query...")
        
        # Create a more simple slow query instead of using temporary tables
        # Use a cross join between users and products to generate a large result set
        start_time = time.time()
        
        # Generate Cartesian product between users and products (inefficient)
        cursor.execute("""
        SELECT 
            u.id as user_id,
            u.username,
            p.id as product_id,
            p.name as product_name,
            CONCAT(u.username, ' - ', p.name) as combined_name,
            LENGTH(u.username) + LENGTH(p.name) as name_length
        FROM 
            users u
        CROSS JOIN 
            products p
        ORDER BY 
            name_length DESC
        """)
        
        # Fetch the results
        results = cursor.fetchall()
        end_time = time.time()
        
        # Artificial delay to make it even slower
        time.sleep(2)
        
        duration = (end_time - start_time) + 2  # Add the sleep time
        logger.info(f"Slow query completed in {duration:.2f} seconds")
        
        return {
            "problem": "slow_query",
            "status": "simulated",
            "duration": duration,
            "results_count": len(results),
            "query_type": "CROSS JOIN between users and products"
        }
    except Error as e:
        logger.error(f"Error in slow query: {e}")
        return {
            "problem": "slow_query",
            "status": "error",
            "error": str(e)
        }
    finally:
        cursor.close()
        conn.close()

def simulate_connection_pool_exhaustion():
    """Simulate connection pool exhaustion by opening many connections without closing them"""
    connections = []
    max_connections = 10
    
    try:
        logger.info(f"Opening {max_connections} connections without closing them...")
        
        for i in range(max_connections):
            conn = get_db_connection()
            connections.append(conn)
            logger.info(f"Opened connection {i+1}/{max_connections}")
            time.sleep(0.5)  # Small delay to make it visible in monitoring
        
        # Wait a bit to simulate the connections being held open
        time.sleep(5)
        
        return {
            "problem": "connection_pool_exhaustion",
            "status": "simulated",
            "connections_opened": len(connections)
        }
    except Error as e:
        logger.error(f"Connection pool error: {e}")
        return {
            "problem": "connection_pool_exhaustion",
            "status": "error",
            "error": str(e)
        }
    finally:
        # Close all connections
        for i, conn in enumerate(connections):
            try:
                conn.close()
                logger.info(f"Closed connection {i+1}/{len(connections)}")
            except Exception as e:
                logger.error(f"Error closing connection {i+1}: {e}")

def deadlock_transaction_1(signal_ready, wait_for_other):
    """First transaction for deadlock simulation"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.start_transaction()
        
        # Update first table
        cursor.execute("UPDATE users SET email = CONCAT(email, '_updated1') WHERE id = 1")
        logger.info("Transaction 1: Updated users table")
        
        # Signal that we're ready for the deadlock
        signal_ready.set()
        
        # Wait for the other transaction to update its first table
        wait_for_other.wait()
        
        time.sleep(1)  # Give it time to set up the deadlock condition
        
        # Try to update the second table - this should deadlock
        logger.info("Transaction 1: Attempting to update products table (should deadlock)")
        cursor.execute("UPDATE products SET name = CONCAT(name, '_updated1') WHERE id = 1")
        
        # If we get here, no deadlock occurred
        conn.commit()
        logger.info("Transaction 1: Committed (no deadlock detected)")
        return False
    except Error as e:
        logger.error(f"Transaction 1 error: {e}")
        return True
    finally:
        try:
            conn.rollback()
        except:
            pass
        cursor.close()
        conn.close()

def deadlock_transaction_2(signal_ready, wait_for_other):
    """Second transaction for deadlock simulation"""
    # Wait for transaction 1 to start
    wait_for_other.wait()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.start_transaction()
        
        # Update second table first (opposite order from transaction 1)
        cursor.execute("UPDATE products SET name = CONCAT(name, '_updated2') WHERE id = 1")
        logger.info("Transaction 2: Updated products table")
        
        # Signal that we've done our first update
        signal_ready.set()
        
        time.sleep(1)  # Give it time to set up the deadlock condition
        
        # Try to update the first table - this should cause a deadlock with transaction 1
        logger.info("Transaction 2: Attempting to update users table (should deadlock)")
        cursor.execute("UPDATE users SET email = CONCAT(email, '_updated2') WHERE id = 1")
        
        # If we get here, no deadlock occurred
        conn.commit()
        logger.info("Transaction 2: Committed (no deadlock detected)")
        return False
    except Error as e:
        logger.error(f"Transaction 2 error: {e}")
        return True
    finally:
        try:
            conn.rollback()
        except:
            pass
        cursor.close()
        conn.close()

def simulate_deadlock():
    """Simulate a deadlock between two transactions"""
    logger.info("Setting up deadlock simulation...")
    
    # Signals for coordinating the two transactions
    t1_ready = threading.Event()
    t2_ready = threading.Event()
    
    # Start the two transactions in separate threads
    t1 = threading.Thread(target=deadlock_transaction_1, args=(t1_ready, t2_ready))
    t2 = threading.Thread(target=deadlock_transaction_2, args=(t2_ready, t1_ready))
    
    t1.start()
    t2.start()
    
    # Wait for both threads to complete
    t1.join(timeout=10)
    t2.join(timeout=10)
    
    return {
        "problem": "deadlock",
        "status": "simulated",
        "message": "Deadlock simulation completed. Check the logs for details."
    }

def simulate_table_lock():
    """Simulate a table lock that blocks other operations"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.start_transaction()
        
        # Lock the table with a write lock
        logger.info("Acquiring table lock on products...")
        cursor.execute("LOCK TABLES products WRITE")
        
        # Hold the lock for a while
        logger.info("Holding table lock for 10 seconds...")
        time.sleep(10)
        
        # Release the lock
        cursor.execute("UNLOCK TABLES")
        conn.commit()
        
        return {
            "problem": "table_lock",
            "status": "simulated",
            "message": "Table was locked for 10 seconds"
        }
    except Error as e:
        logger.error(f"Table lock error: {e}")
        return {
            "problem": "table_lock",
            "status": "error",
            "error": str(e)
        }
    finally:
        try:
            cursor.execute("UNLOCK TABLES")
            conn.rollback()
        except:
            pass
        cursor.close()
        conn.close()

def simulate_memory_leak():
    """Simulate a memory leak by fetching large result sets repeatedly"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create a temporary table with lots of data
        cursor.execute("CREATE TEMPORARY TABLE memory_leak_test (id INT, data TEXT)")
        
        # Generate a large amount of data
        large_data = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=1000))
        
        # Insert multiple rows
        for i in range(1000):
            cursor.execute(
                "INSERT INTO memory_leak_test VALUES (%s, %s)", 
                (i, large_data * 10)  # 10KB of data per row
            )
        
        conn.commit()
        
        # Fetch the data multiple times without proper cleanup
        for i in range(5):
            logger.info(f"Memory leak simulation: fetching large dataset (iteration {i+1}/5)")
            cursor.execute("SELECT * FROM memory_leak_test")
            
            # This is intentionally inefficient - fetching all at once
            results = cursor.fetchall()
            
            # Simulate processing the data
            total_size = sum(len(str(row)) for row in results)
            logger.info(f"Fetched approximately {total_size/1024/1024:.2f} MB of data")
            
            # In a real memory leak, we might store this data somewhere without releasing it
            # For simulation, we'll just wait a bit to make it visible in monitoring
            time.sleep(2)
        
        # Clean up
        cursor.execute("DROP TEMPORARY TABLE memory_leak_test")
        
        return {
            "problem": "memory_leak",
            "status": "simulated",
            "iterations": 5,
            "approximate_size_mb": total_size/1024/1024
        }
    except Error as e:
        logger.error(f"Memory leak simulation error: {e}")
        return {
            "problem": "memory_leak",
            "status": "error",
            "error": str(e)
        }
    finally:
        cursor.close()
        conn.close()

def simulate_connection_drop():
    """Simulate a connection drop during a transaction"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start a transaction
        conn.start_transaction()
        
        # Make some changes
        cursor.execute("UPDATE users SET email = CONCAT(email, '_temp') WHERE id = 1")
        
        # Simulate some processing time
        logger.info("Transaction in progress, about to drop connection...")
        time.sleep(2)
        
        # Abruptly close the connection without committing or rolling back
        conn._socket.close()
        
        return {
            "problem": "connection_drop",
            "status": "simulated",
            "message": "Connection was abruptly closed during transaction"
        }
    except Error as e:
        logger.error(f"Connection drop simulation error: {e}")
        return {
            "problem": "connection_drop",
            "status": "error",
            "error": str(e)
        }

def simulate_query_error():
    """Simulate query errors like syntax errors or invalid references"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Execute a query with a syntax error
        logger.info("Executing query with syntax error...")
        cursor.execute("SELECT * FROMM users WHERE id = 1")  # Intentional typo in FROM
        
        # We shouldn't reach this point
        return {
            "problem": "query_error",
            "status": "unexpected_success",
            "message": "The query with syntax error unexpectedly succeeded"
        }
    except Error as e:
        logger.info(f"Expected query error: {e}")
        return {
            "problem": "query_error",
            "status": "simulated",
            "error": str(e)
        }
    finally:
        cursor.close()
        conn.close()