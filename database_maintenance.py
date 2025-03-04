#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Maintenance Utility

This script provides utilities to check and fix database schemas for both the main
employee database and the stress test database. It ensures all required tables and
columns exist with the proper structure.
"""

import os
import sqlite3
from database.database import Database
from database.schema import SCHEMA
from database.payroll_schema import PAYROLL_TABLES_SQL

def check_database_schema(db_file):
    """Check if the database has all required tables and columns"""
    if not os.path.exists(db_file):
        print(f"Database file {db_file} does not exist.")
        return False
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Get all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    # Check if all required tables exist
    required_tables = list(SCHEMA.keys())
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        print(f"Missing tables in {db_file}: {', '.join(missing_tables)}")
        return False
    
    # Check if payroll_entries has required columns
    if 'payroll_entries' in tables:
        cursor.execute("PRAGMA table_info(payroll_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'gross_salary' not in columns:
            print(f"Missing column 'gross_salary' in payroll_entries table")
            return False
        
        if 'payment_date' not in columns:
            print(f"Missing column 'payment_date' in payroll_entries table")
            return False
    
    # Check if salaries table exists
    if 'salaries' not in tables:
        print(f"Missing 'salaries' table in {db_file}")
        return False
    
    # Check if salary_payments table exists
    if 'salary_payments' not in tables:
        print(f"Missing 'salary_payments' table in {db_file}")
        return False
    
    conn.close()
    return True

def fix_database_schema(db_file):
    """Fix the database schema by creating missing tables and columns"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Get all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    
    # Create missing tables
    for table_name, create_sql in SCHEMA.items():
        if table_name not in tables:
            print(f"Creating missing table: {table_name}")
            cursor.execute(create_sql)
    
    # Check and fix payroll_entries table
    if 'payroll_entries' in tables:
        cursor.execute("PRAGMA table_info(payroll_entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'gross_salary' not in columns:
            print("Adding missing column 'gross_salary' to payroll_entries table")
            cursor.execute("ALTER TABLE payroll_entries ADD COLUMN gross_salary REAL DEFAULT 0")
            cursor.execute("UPDATE payroll_entries SET gross_salary = basic_salary + total_allowances")
        
        if 'payment_date' not in columns:
            print("Adding missing column 'payment_date' to payroll_entries table")
            cursor.execute("ALTER TABLE payroll_entries ADD COLUMN payment_date DATE")
            cursor.execute("UPDATE payroll_entries SET payment_date = date('now')")
    
    # Create salaries table if it doesn't exist
    if 'salaries' not in tables and 'salaries' in PAYROLL_TABLES_SQL:
        print("Creating missing 'salaries' table")
        cursor.execute(PAYROLL_TABLES_SQL['salaries'])
    
    # Create salary_payments table if it doesn't exist
    if 'salary_payments' not in tables and 'salary_payments' in PAYROLL_TABLES_SQL:
        print("Creating missing 'salary_payments' table")
        cursor.execute(PAYROLL_TABLES_SQL['salary_payments'])
    
    conn.commit()
    conn.close()
    print(f"Database {db_file} schema has been fixed.")
    return True

def main():
    """Main function to check and fix both databases"""
    main_db = "employee.db"
    stress_test_db = "stress_test.db"
    
    # Check and fix main database
    print(f"Checking main database: {main_db}")
    if not check_database_schema(main_db):
        print(f"Fixing main database schema...")
        fix_database_schema(main_db)
    else:
        print(f"Main database schema is valid.")
    
    # Check and fix stress test database
    if os.path.exists(stress_test_db):
        print(f"\nChecking stress test database: {stress_test_db}")
        if not check_database_schema(stress_test_db):
            print(f"Fixing stress test database schema...")
            fix_database_schema(stress_test_db)
        else:
            print(f"Stress test database schema is valid.")
    else:
        print(f"\nStress test database {stress_test_db} does not exist. It will be created when running stress tests.")
    
    print("\nDatabase maintenance completed.")

if __name__ == "__main__":
    main()
