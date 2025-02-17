import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_file="employee.db"):
        self.db_file = db_file
        self.create_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_file)
    
    def create_tables(self):
        tables = [
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob DATE,
                gender TEXT,
                phone TEXT,
                email TEXT,
                position TEXT,
                department TEXT,
                hire_date DATE,
                salary_type TEXT,
                basic_salary REAL,
                bank_account TEXT,
                photo_path TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS salaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                base_salary REAL,
                bonuses REAL,
                deductions REAL,
                overtime_pay REAL,
                total_salary REAL,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS salary_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                amount_paid REAL,
                payment_date DATE,
                payment_mode TEXT,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for table in tables:
            cursor.execute(table)
        
        conn.commit()
        conn.close()
    
    def execute_query(self, query, parameters=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        return cursor
    
    def fetch_query(self, query, parameters=()):
        cursor = self.execute_query(query, parameters)
        results = cursor.fetchall()
        cursor.connection.close()
        return results
