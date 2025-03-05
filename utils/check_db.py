#!/usr/bin/env python
"""
Script to check the database structure
"""

import sqlite3
import os

def check_database():
    """Check the database structure"""
    print("Checking database structure...")
    
    # Find the database file
    db_path = 'employee.db'
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Check if salaries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='salaries'")
        if cursor.fetchone():
            print("salaries table exists")
            
            # Get columns in salaries table
            cursor.execute("PRAGMA table_info(salaries)")
            columns = cursor.fetchall()
            print(f"Columns in salaries table: {[col[1] for col in columns]}")
        else:
            print("salaries table does not exist")
        
        # Check if salary_payments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='salary_payments'")
        if cursor.fetchone():
            print("salary_payments table exists")
            
            # Get columns in salary_payments table
            cursor.execute("PRAGMA table_info(salary_payments)")
            columns = cursor.fetchall()
            print(f"Columns in salary_payments table: {[col[1] for col in columns]}")
        else:
            print("salary_payments table does not exist")
        
        # Check if payroll_entries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payroll_entries'")
        if cursor.fetchone():
            print("payroll_entries table exists")
            
            # Get columns in payroll_entries table
            cursor.execute("PRAGMA table_info(payroll_entries)")
            columns = cursor.fetchall()
            print(f"Columns in payroll_entries table: {[col[1] for col in columns]}")
        else:
            print("payroll_entries table does not exist")
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database()
