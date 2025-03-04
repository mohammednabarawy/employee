#!/usr/bin/env python
"""
Script to fix the stress test database by creating required tables
"""

import sqlite3
import os
from datetime import datetime
import sys

def fix_stress_test_db():
    """Fix the stress test database by creating required tables"""
    print("Fixing stress test database...")
    
    # Use the stress test database file
    db_file = "stress_test.db"
    
    if not os.path.exists(db_file):
        print(f"Stress test database file not found at {db_file}")
        print("Run the stress test first to create the initial database")
        return
    
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"Existing tables: {existing_tables}")
        
        # Create salaries table if it doesn't exist
        if 'salaries' not in existing_tables:
            print("Creating salaries table...")
            cursor.execute("""
                CREATE TABLE salaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    base_salary REAL NOT NULL,
                    bonuses REAL DEFAULT 0,
                    deductions REAL DEFAULT 0,
                    overtime_pay REAL DEFAULT 0,
                    total_salary REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)
            
            # Initialize salaries for existing employees
            cursor.execute("SELECT id, basic_salary FROM employees WHERE is_active = 1")
            employees = cursor.fetchall()
            
            for employee_id, basic_salary in employees:
                cursor.execute("""
                    INSERT INTO salaries (
                        employee_id, base_salary, bonuses, deductions, overtime_pay, total_salary
                    ) VALUES (?, ?, 0, 0, 0, ?)
                """, (employee_id, basic_salary, basic_salary))
        
        # Create salary_payments table if it doesn't exist
        if 'salary_payments' not in existing_tables:
            print("Creating salary_payments table...")
            cursor.execute("""
                CREATE TABLE salary_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    amount_paid REAL NOT NULL,
                    payment_date DATE NOT NULL,
                    payment_mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)
            
            # Add sample payment data for testing
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT id, basic_salary FROM employees WHERE is_active = 1 LIMIT 5")
            employees = cursor.fetchall()
            
            for employee_id, basic_salary in employees:
                cursor.execute("""
                    INSERT INTO salary_payments (
                        employee_id, amount_paid, payment_date, payment_mode, status
                    ) VALUES (?, ?, ?, 'Bank Transfer', 'Paid')
                """, (employee_id, basic_salary, today))
        
        # Check if payroll_entries table exists
        if 'payroll_entries' in existing_tables:
            # Check if payroll_entries table has gross_salary column
            cursor.execute("PRAGMA table_info(payroll_entries)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'gross_salary' not in columns:
                print("Adding gross_salary column to payroll_entries table...")
                cursor.execute("ALTER TABLE payroll_entries ADD COLUMN gross_salary REAL DEFAULT 0")
                
                # Update existing records to set gross_salary based on basic_salary
                cursor.execute("UPDATE payroll_entries SET gross_salary = basic_salary + total_allowances")
            
            if 'payment_date' not in columns:
                print("Adding payment_date column to payroll_entries table...")
                cursor.execute("ALTER TABLE payroll_entries ADD COLUMN payment_date DATE")
                
                # Update existing records with a payment date
                cursor.execute("UPDATE payroll_entries SET payment_date = date('now') WHERE payment_date IS NULL")
        
        conn.commit()
        print("Stress test database fixed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing stress test database: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_stress_test_db()
