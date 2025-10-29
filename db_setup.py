
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

def create_sample_database(db_path='data/sample_db.sqlite'):
    """Create and populate a sample database with customers, orders, and products tables."""
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS order_items")
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS products")
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            phone TEXT,
            created_date DATE NOT NULL
        )
    """)
    
    # Create products table
    cursor.execute("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INTEGER NOT NULL,
            description TEXT
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_date DATE NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            status TEXT NOT NULL,
            shipping_city TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    # Create order_items table
    cursor.execute("""
        CREATE TABLE order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)
    
    # Sample data
    cities = ['Bangalore', 'Mumbai', 'Delhi', 'Chennai', 'Hyderabad', 'Pune', 'Kolkata', 'Ahmedabad']
    states = ['Karnataka', 'Maharashtra', 'Delhi', 'Tamil Nadu', 'Telangana', 'Maharashtra', 'West Bengal', 'Gujarat']
    
    # Insert sample customers
    customers_data = []
    for i in range(1, 101):
        city_idx = random.randint(0, len(cities)-1)
        customers_data.append((
            f"Customer {i}",
            f"customer{i}@email.com",
            cities[city_idx],
            states[city_idx],
            f"+91-9{random.randint(100000000, 999999999)}",
            (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
        ))
    
    cursor.executemany("""
        INSERT INTO customers (name, email, city, state, phone, created_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, customers_data)
    
    # Insert sample products
    products_data = [
        ("iPhone 15", "Electronics", 79999.00, 50, "Latest iPhone model"),
        ("Samsung Galaxy S24", "Electronics", 69999.00, 45, "Android flagship phone"),
        ("MacBook Air M3", "Electronics", 114900.00, 30, "Apple laptop with M3 chip"),
        ("Dell XPS 13", "Electronics", 89999.00, 25, "Premium Windows laptop"),
        ("Sony WH-1000XM5", "Electronics", 29990.00, 80, "Noise cancelling headphones"),
        ("Nike Air Max", "Footwear", 8999.00, 100, "Comfortable running shoes"),
        ("Adidas Ultraboost", "Footwear", 12999.00, 75, "Performance running shoes"),
        ("Levi's 501 Jeans", "Clothing", 3999.00, 120, "Classic denim jeans"),
        ("Zara Cotton Shirt", "Clothing", 1999.00, 90, "Casual cotton shirt"),
        ("Books Set", "Books", 1299.00, 200, "Popular fiction book collection"),
        ("Gaming Chair", "Furniture", 15999.00, 40, "Ergonomic gaming chair"),
        ("Study Desk", "Furniture", 8999.00, 35, "Wooden study desk"),
        ("Coffee Maker", "Appliances", 4999.00, 60, "Automatic drip coffee maker"),
        ("Blender", "Appliances", 2999.00, 70, "High-speed blender"),
        ("Yoga Mat", "Sports", 1499.00, 150, "Non-slip yoga mat")
    ]
    
    cursor.executemany("""
        INSERT INTO products (name, category, price, stock_quantity, description)
        VALUES (?, ?, ?, ?, ?)
    """, products_data)
    
    # Insert sample orders
    order_statuses = ['Completed', 'Processing', 'Shipped', 'Cancelled', 'Delivered']
    
    orders_data = []
    for i in range(1, 201):
        customer_id = random.randint(1, 100)
        order_date = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d')
        status = random.choice(order_statuses)
        shipping_city = random.choice(cities)
        # We'll calculate total_amount after inserting order_items
        orders_data.append((customer_id, order_date, 0.0, status, shipping_city))
    
    cursor.executemany("""
        INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_city)
        VALUES (?, ?, ?, ?, ?)
    """, orders_data)
    
    # Insert sample order_items and update order totals
    for order_id in range(1, 201):
        num_items = random.randint(1, 5)
        total_amount = 0.0
        
        for _ in range(num_items):
            product_id = random.randint(1, 15)
            quantity = random.randint(1, 3)
            
            # Get product price
            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            unit_price = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, product_id, quantity, unit_price))
            
            total_amount += quantity * unit_price
        
        # Update order total
        cursor.execute("""
            UPDATE orders SET total_amount = ? WHERE order_id = ?
        """, (total_amount, order_id))
    
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at {db_path}")
    print("Tables created: customers, products, orders, order_items")

def get_database_schema(db_path='data/sample_db.sqlite'):
    """Return database schema information for reference."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    schema_info = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        schema_info[table_name] = columns
    
    conn.close()
    return schema_info

if __name__ == "__main__":
    import os
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Create the database
    create_sample_database()
    
    # Print schema info
    schema = get_database_schema()
    print("\nDatabase Schema:")
    for table, columns in schema.items():
        print(f"\n{table}:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
