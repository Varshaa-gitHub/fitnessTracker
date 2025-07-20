import sqlite3

conn = sqlite3.connect("fitness_tracker.db")
c = conn.cursor()

# Check if the users table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
if c.fetchone():
    print("Users table exists.")

# Fetch all users
c.execute("SELECT * FROM users;")
users = c.fetchall()
print("Users in database:", users)

conn.close()
