import os
import sqlite3
import sys
import json
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_database_schema(db_path="employee.db"):
    """Check the database schema and report any issues"""
    print(f"Checking database schema for: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} does not exist")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nFound {len(tables)} tables in the database:")
    for table in tables:
        print(f"  - {table}")
    
    # Check each table's schema
    print("\nTable schemas:")
    table_schemas = {}
    foreign_keys = {}
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [dict(row) for row in cursor.fetchall()]
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = [dict(row) for row in cursor.fetchall()]
        
        if fks:
            foreign_keys[table] = fks
        
        table_schemas[table] = columns
        
        print(f"\nTable: {table}")
        print("Columns:")
        for col in columns:
            nullable = "NOT NULL" if col["notnull"] else "NULL"
            pk = "PRIMARY KEY" if col["pk"] else ""
            print(f"  - {col['name']} ({col['type']}) {nullable} {pk}")
    
    # Print foreign key relationships
    print("\nForeign Key Relationships:")
    for table, fks in foreign_keys.items():
        print(f"\nTable: {table}")
        for fk in fks:
            print(f"  - {fk['from']} -> {fk['table']}.{fk['to']}")
    
    # Check for common issues
    print("\nChecking for potential issues...")
    
    # Check for tables with foreign keys to non-existent tables
    fk_issues = []
    for table, fks in foreign_keys.items():
        for fk in fks:
            if fk['table'] not in tables:
                fk_issues.append(f"Table '{table}' has foreign key to non-existent table '{fk['table']}'")
    
    if fk_issues:
        print("\nForeign Key Issues:")
        for issue in fk_issues:
            print(f"  - {issue}")
    else:
        print("✓ No foreign key issues found")
    
    # Check for required tables
    required_tables = [
        'users', 'employees', 'departments', 'positions', 'shifts',
        'attendance_records', 'salaries', 'payroll_periods', 'payroll_entries'
    ]
    
    missing_tables = [table for table in required_tables if table not in tables]
    if missing_tables:
        print("\nMissing Required Tables:")
        for table in missing_tables:
            print(f"  - {table}")
    else:
        print("✓ All required tables exist")
    
    # Check for required columns in key tables
    required_columns = {
        'employees': ['id', 'name', 'code', 'department_id', 'position_id', 'shift_id', 'hire_date'],
        'attendance_records': ['employee_id', 'check_in', 'check_out', 'status', 'shift_id'],
        'salaries': ['employee_id', 'base_salary', 'total_salary', 'effective_date'],
        'payroll_entries': ['employee_id', 'payroll_period_id', 'basic_salary', 'net_salary', 'gross_salary']
    }
    
    column_issues = []
    for table, columns in required_columns.items():
        if table in tables:
            table_columns = [col['name'] for col in table_schemas[table]]
            missing_columns = [col for col in columns if col not in table_columns]
            if missing_columns:
                column_issues.append(f"Table '{table}' is missing columns: {', '.join(missing_columns)}")
    
    if column_issues:
        print("\nColumn Issues:")
        for issue in column_issues:
            print(f"  - {issue}")
    else:
        print("✓ All required columns exist in key tables")
    
    # Close connection
    conn.close()
    
    # Return success if no issues found
    return not (fk_issues or missing_tables or column_issues)

if __name__ == "__main__":
    success = check_database_schema()
    print("\nSchema check " + ("passed" if success else "failed"))
    exit(0 if success else 1)
