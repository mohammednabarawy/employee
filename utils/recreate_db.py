import os
import sqlite3
from utils.init_db import init_db

# Path to the database file
db_path = 'employee.db'

# Delete the database file if it exists
if os.path.exists(db_path):
    print(f"Deleting existing database: {db_path}")
    os.remove(db_path)
    print("Database deleted successfully")

# Initialize the database
print("Creating new database...")
init_db()
print("Database recreated successfully!")
