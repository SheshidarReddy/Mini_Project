import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Drop tables if they exist (optional, for resetting)
c.execute('DROP TABLE IF EXISTS student')
c.execute('DROP TABLE IF EXISTS admin')

# Create tables
c.execute('''
    CREATE TABLE student (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        batch TEXT
    )
''')

c.execute('''
    CREATE TABLE admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# Insert demo data
c.execute("INSERT INTO student (name, email, password, batch) VALUES (?, ?, ?, ?)",
          ("John Doe", "john@example.com", "password123", "Batch A"))

c.execute("INSERT INTO admin (username, password) VALUES (?, ?)",
          ("admin", "admin123"))

conn.commit()
conn.close()

print("Database initialized.")
