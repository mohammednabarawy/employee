#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Consistency Verification Tool

This script checks all database files in the project for schema consistency
and can optionally fix any issues found.
"""

import os
import sys
import argparse
import glob
import sqlite3

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import Database
from database.schema import SCHEMA
from database.payroll_schema import PAYROLL_TABLES_SQL

def find_database_files(directory='.'):
    """Find all .db files in the given directory and subdirectories"""
    return glob.glob(os.path.join(directory, '**', '*.db'), recursive=True)

def verify_database(db_file, fix=False):
    """Verify a database file for schema consistency"""
    print(f"\nVerifying database: {db_file}")
    
    if not os.path.exists(db_file):
        print(f"  Error: File does not exist")
        return False
    
    try:
        # Create a temporary database instance
        db = Database(db_file)
        
        # Check if all tables exist
        missing_tables = db.get_missing_tables()
        
        if missing_tables:
            print(f"  Missing tables: {', '.join(missing_tables)}")
            
            if fix:
                print("  Fixing missing tables...")
                db.create_tables()
                
                # Verify fix
                remaining_missing = db.get_missing_tables()
                if remaining_missing:
                    print(f"  Error: Could not create all tables. Still missing: {', '.join(remaining_missing)}")
                    return False
                else:
                    print("  All tables created successfully")
        else:
            print("  All required tables exist")
        
        # Check for missing columns in key tables
        key_tables = ['employees', 'salaries', 'attendance_records', 'payroll_entries']
        issues_found = False
        
        for table in key_tables:
            if table not in missing_tables:
                columns = db.get_table_columns(table)
                
                # Check specific columns for each table
                if table == 'employees' and 'shift_id' not in columns:
                    print(f"  Table {table} is missing column: shift_id")
                    issues_found = True
                    
                    if fix:
                        db.execute_query(f"ALTER TABLE {table} ADD COLUMN shift_id INTEGER REFERENCES shifts(id)")
                        print(f"  Added shift_id column to {table}")
                
                elif table == 'attendance_records' and 'shift_id' not in columns:
                    print(f"  Table {table} is missing column: shift_id")
                    issues_found = True
                    
                    if fix:
                        db.execute_query(f"ALTER TABLE {table} ADD COLUMN shift_id INTEGER REFERENCES shifts(id)")
                        print(f"  Added shift_id column to {table}")
                
                elif table == 'salaries' and 'effective_date' not in columns:
                    print(f"  Table {table} is missing column: effective_date")
                    issues_found = True
                    
                    if fix:
                        db.execute_query(f"ALTER TABLE {table} ADD COLUMN effective_date DATE")
                        print(f"  Added effective_date column to {table}")
                
                elif table == 'payroll_entries' and 'gross_salary' not in columns:
                    print(f"  Table {table} is missing column: gross_salary")
                    issues_found = True
                    
                    if fix:
                        db.execute_query(f"ALTER TABLE {table} ADD COLUMN gross_salary DECIMAL(10,2)")
                        print(f"  Added gross_salary column to {table}")
        
        if not issues_found and not missing_tables:
            print("  Database schema is consistent")
            return True
        elif fix:
            print("  Database schema has been fixed")
            return True
        else:
            print("  Database schema has issues that need to be fixed")
            return False
            
    except Exception as e:
        print(f"  Error verifying database: {str(e)}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Verify database consistency')
    parser.add_argument('--dir', default='.', help='Directory to search for database files')
    parser.add_argument('--fix', action='store_true', help='Fix issues found')
    parser.add_argument('--file', help='Specific database file to check')
    
    args = parser.parse_args()
    
    if args.file:
        # Check a specific file
        db_files = [args.file]
    else:
        # Find all database files
        db_files = find_database_files(args.dir)
    
    if not db_files:
        print("No database files found")
        return
    
    print(f"Found {len(db_files)} database files:")
    for db_file in db_files:
        print(f"  {db_file}")
    
    # Verify each database
    results = []
    for db_file in db_files:
        result = verify_database(db_file, args.fix)
        results.append((db_file, result))
    
    # Print summary
    print("\nVerification Summary:")
    print("=" * 50)
    
    consistent_count = sum(1 for _, result in results if result)
    inconsistent_count = len(results) - consistent_count
    
    print(f"Total databases checked: {len(results)}")
    print(f"Consistent databases: {consistent_count}")
    print(f"Inconsistent databases: {inconsistent_count}")
    
    if inconsistent_count > 0 and not args.fix:
        print("\nRun with --fix option to automatically fix inconsistent databases")

if __name__ == "__main__":
    main()
