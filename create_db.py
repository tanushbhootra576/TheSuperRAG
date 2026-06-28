import sqlite3
import random
import datetime

def create_db():
    conn = sqlite3.connect("sales.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        region TEXT,
        created_at DATE
    )''')

    c.execute('''CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        price REAL NOT NULL
    )''')

    c.execute('''CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER NOT NULL,
        status TEXT,
        order_date DATE
    )''')

    # Insert dummy data
    regions = ['North', 'South', 'East', 'West']
    categories = ['Electronics', 'Clothing', 'Food']
    statuses = ['pending', 'shipped', 'delivered', 'cancelled']

    for i in range(1, 11):
        c.execute("INSERT INTO users (name, email, region, created_at) VALUES (?, ?, ?, ?)",
                  (f"User {i}", f"user{i}@example.com", random.choice(regions), datetime.date(2026, 1, random.randint(1, 28))))

    for i in range(1, 6):
        c.execute("INSERT INTO products (name, category, price) VALUES (?, ?, ?)",
                  (f"Product {i}", random.choice(categories), round(random.uniform(10.0, 500.0), 2)))

    for i in range(1, 51):
        c.execute("INSERT INTO orders (user_id, product_id, quantity, status, order_date) VALUES (?, ?, ?, ?, ?)",
                  (random.randint(1, 10), random.randint(1, 5), random.randint(1, 5), random.choice(statuses), datetime.date(2026, random.randint(1, 6), random.randint(1, 28))))

    conn.commit()
    conn.close()
    print("sales.db created and seeded.")

if __name__ == "__main__":
    create_db()
