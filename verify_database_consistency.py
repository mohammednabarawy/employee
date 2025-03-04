#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Consistency Verification Utility

This script checks and verifies that all databases used by the application
have consistent schemas and can be used interchangeably.
"""

import os
import sqlite3
import argparse
from database.database import Database
from database.schema import SCHEMA
from database.payroll_schema import PAYROLL_TABLES_SQL

def list_all_databases(directory='.'):
    """Find all SQLite database files in the given directory"""
    db_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    return db_files

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

def fix_database(db_file):
    """Fix a database by using the Database class's validate_schema method"""
    print(f"Fixing database: {db_file}")
    db = Database(db_file)
    db.validate_schema()
    print(f"Database {db_file} has been fixed.")
    return True

def main():
    parser = argparse.ArgumentParser(description='Verify database consistency across all databases')
    parser.add_argument('--fix', action='store_true', help='Fix inconsistent databases')
    parser.add_argument('--directory', '-d', default='.', help='Directory to search for database files')
    args = parser.parse_args()
    
    # Find all database files
    db_files = list_all_databases(args.directory)
    
    if not db_files:
        print(f"No database files found in {args.directory}")
        return
    
    print(f"Found {len(db_files)} database files:")
    for db_file in db_files:
        print(f"  - {db_file}")
    
    print("\nChecking database schemas...")
    inconsistent_dbs = []
    
    for db_file in db_files:
        print(f"\nVerifying {db_file}...")
        if check_database_schema(db_file):
            print(f"✓ {db_file} has a consistent schema")
        else:
            print(f"✗ {db_file} has an inconsistent schema")
            inconsistent_dbs.append(db_file)
    
    if inconsistent_dbs:
        print(f"\nFound {len(inconsistent_dbs)} databases with inconsistent schemas:")
        for db_file in inconsistent_dbs:
            print(f"  - {db_file}")
        
        if args.fix:
            print("\nFixing inconsistent databases...")
            for db_file in inconsistent_dbs:
                fix_database(db_file)
            
            # Verify again after fixing
            print("\nVerifying databases after fixing...")
            still_inconsistent = []
            for db_file in inconsistent_dbs:
                if check_database_schema(db_file):
                    print(f"✓ {db_file} now has a consistent schema")
                else:
                    print(f"✗ {db_file} still has an inconsistent schema")
                    still_inconsistent.append(db_file)
            
            if still_inconsistent:
                print(f"\nWarning: {len(still_inconsistent)} databases still have inconsistent schemas")
            else:
                print("\nAll databases now have consistent schemas")
        else:
            print("\nUse --fix option to fix inconsistent databases")
    else:
        print("\nAll databases have consistent schemas")

if __name__ == "__main__":
    main()
