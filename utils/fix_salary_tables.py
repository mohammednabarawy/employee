#!/usr/bin/env python
"""
Script to add missing salary and reporting tables for stress testing
"""

import sqlite3
import os
from datetime import datetime

def create_missing_tables():
    """Create missing tables required for stress testing"""
    print("Creating missing tables for stress testing...")
    
    # Use the correct database file
    db_file = "employee.db"
    
    if not os.path.exists(db_file):
        print(f"Database file not found at {db_file}")
        return
    
    conn = sqlite3.connect(db_file)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    
    try:
        # Get existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"Existing tables: {existing_tables}")
        
        # Create payroll_periods table if it doesn't exist
        if 'payroll_periods' not in existing_tables:
            print("Creating payroll_periods table...")
            cursor.execute("""
                CREATE TABLE payroll_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
        # Create payroll_entries table if it doesn't exist
        if 'payroll_entries' not in existing_tables:
            print("Creating payroll_entries table...")
            cursor.execute("""
                CREATE TABLE payroll_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    payroll_period_id INTEGER NOT NULL,
                    basic_salary REAL NOT NULL,
                    total_allowances REAL DEFAULT 0,
                    total_deductions REAL DEFAULT 0,
                    net_salary REAL NOT NULL,
                    gross_salary REAL NOT NULL,
                    payment_date DATE,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (payroll_period_id) REFERENCES payroll_periods(id)
                )
            """)
        else:
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
        
        # Check if salaries table exists and drop it to recreate with correct structure
        if 'salaries' in existing_tables:
            print("Dropping existing salaries table to recreate with correct structure...")
            cursor.execute("DROP TABLE salaries")
        
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
        
        # Check if salary_payments table exists and drop it to recreate with correct structure
        if 'salary_payments' in existing_tables:
            print("Dropping existing salary_payments table to recreate with correct structure...")
            cursor.execute("DROP TABLE salary_payments")
        
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
        
        # Create attendance table if it doesn't exist
        if 'attendance' not in existing_tables:
            print("Creating attendance table...")
            cursor.execute("""
                CREATE TABLE attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    status TEXT NOT NULL,
                    check_in TIME,
                    check_out TIME,
                    overtime_hours REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)
        
        # Create sample payroll period and entries if needed
        cursor.execute("SELECT COUNT(*) FROM payroll_periods")
        if cursor.fetchone()[0] == 0:
            # Create a payroll period
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT INTO payroll_periods (start_date, end_date, status)
                VALUES (?, ?, 'Completed')
            """, (start_date, end_date))
            
            period_id = cursor.lastrowid
            
            # Create payroll entries for this period
            cursor.execute("SELECT id, basic_salary FROM employees WHERE is_active = 1")
            employees = cursor.fetchall()
            
            for employee_id, basic_salary in employees:
                # Simple calculation for testing
                net_salary = basic_salary * 0.85  # After deductions
                gross_salary = basic_salary * 1.1  # Base + allowances
                
                cursor.execute("""
                    INSERT INTO payroll_entries (
                        employee_id, payroll_period_id, basic_salary,
                        total_allowances, total_deductions, net_salary,
                        gross_salary, payment_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Paid')
                """, (
                    employee_id, period_id, basic_salary,
                    basic_salary * 0.1, basic_salary * 0.15, net_salary,
                    gross_salary, end_date, 
                ))
        else:
            # Check if existing payroll entries have the gross_salary column populated
            cursor.execute("SELECT COUNT(*) FROM payroll_entries WHERE gross_salary IS NULL OR gross_salary = 0")
            if cursor.fetchone()[0] > 0:
                print("Updating existing payroll entries with gross_salary...")
                cursor.execute("UPDATE payroll_entries SET gross_salary = basic_salary + total_allowances WHERE gross_salary IS NULL OR gross_salary = 0")
        
        conn.commit()
        print("Tables created/updated successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_missing_tables()
