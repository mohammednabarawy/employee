"""Database migration script"""
import os
import logging
import sqlite3
from datetime import datetime
from typing import Tuple, Any
from .payroll_schema import (
    PAYROLL_TABLES_SQL, INITIAL_USERS, INITIAL_PAYMENT_METHODS,
    INITIAL_EMPLOYEE_TYPES, INITIAL_LEAVE_TYPES, INITIAL_TAX_EXEMPT_ALLOWANCES
)

def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with proper settings"""
    db_path = os.path.join('database', 'payroll.db')
    os.makedirs('database', exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign key support
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    
    return conn

def create_tables(cursor: sqlite3.Cursor) -> Tuple[bool, str]:
    """Create tables in the database"""
    try:
        # Create tables in order of dependencies
        table_order = [
            'users',  # Base table for foreign keys
            'employee_types',
            'employees',
            'employee_details',
            'payment_methods',
            'tax_brackets',
            'salary_components',
            'employee_salary_components',
            'payroll_periods',
            'payroll_entries',
            'payroll_entry_details',
            'payroll_entry_components',
            'salary_structures',
            'employee_salary_structure',
            'shifts',
            'attendance_records',
            'overtime_records',
            'pay_grades',
            'public_holidays',
            'leave_types',
            'leave_balances',
            'leave_requests',
            'tax_exempt_allowances',
            'employee_benefits',
            'deductions',
            'payslip_templates',
            'salaries',
            'salary_payments'
        ]
        
        # Create tables in correct order
        for table_name in table_order:
            if table_name in PAYROLL_TABLES_SQL:
                try:
                    cursor.execute(PAYROLL_TABLES_SQL[table_name])
                    print(f"Creating missing table: {table_name}")
                except sqlite3.Error as e:
                    if "already exists" not in str(e):
                        print(f"Error creating table {table_name}: {e}")
                        raise
        
        return True, "Tables created successfully"
        
    except Exception as e:
        logging.error(f"Error creating tables: {str(e)}")
        return False, f"Error creating tables: {str(e)}"

def create_indexes(cursor: sqlite3.Cursor) -> Tuple[bool, str]:
    """Create indexes in the database"""
    try:
        # Create indexes individually
        if 'indexes' in PAYROLL_TABLES_SQL:
            for index_sql in PAYROLL_TABLES_SQL['indexes']:
                try:
                    cursor.execute(index_sql)
                    print("Created index successfully")
                except sqlite3.Error as e:
                    if "already exists" not in str(e):
                        print(f"Error creating index: {e}")
                        raise
        
        return True, "Indexes created successfully"
        
    except Exception as e:
        logging.error(f"Error creating indexes: {str(e)}")
        return False, f"Error creating indexes: {str(e)}"

def insert_initial_data(cursor: sqlite3.Cursor) -> Tuple[bool, str]:
    """Insert initial data into the database"""
    try:
        # Insert initial admin user
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """INSERT INTO users (
                    username, email, password_hash, first_name, last_name,
                    role, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                INITIAL_USERS
            )
            print("Inserted admin user")
        
        # Insert payment methods
        cursor.execute("SELECT COUNT(*) FROM payment_methods")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO payment_methods (name, name_ar) VALUES (?, ?)",
                INITIAL_PAYMENT_METHODS
            )
            print("Inserted payment methods")
        
        # Insert employee types
        cursor.execute("SELECT COUNT(*) FROM employee_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """INSERT INTO employee_types (
                    name, name_ar, working_hours_per_week, overtime_multiplier,
                    holiday_pay_multiplier, prorated_benefits
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                INITIAL_EMPLOYEE_TYPES
            )
            print("Inserted employee types")
        
        # Insert leave types
        cursor.execute("SELECT COUNT(*) FROM leave_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """INSERT INTO leave_types (
                    name, name_ar, annual_days, paid, requires_approval
                ) VALUES (?, ?, ?, ?, ?)""",
                INITIAL_LEAVE_TYPES
            )
            print("Inserted leave types")
        
        # Insert tax exempt allowances
        cursor.execute("SELECT COUNT(*) FROM tax_exempt_allowances")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                """INSERT INTO tax_exempt_allowances (
                    name, max_amount, max_percentage
                ) VALUES (?, ?, ?)""",
                INITIAL_TAX_EXEMPT_ALLOWANCES
            )
            print("Inserted tax exempt allowances")
        
        return True, "Initial data inserted successfully"
        
    except Exception as e:
        logging.error(f"Error inserting initial data: {str(e)}")
        return False, f"Error inserting initial data: {str(e)}"

def migrate_database() -> Tuple[bool, str]:
    """Migrate database schema and initial data"""
    try:
        db_path = os.path.join('database', 'payroll.db')
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Removed existing database")
        
        # Create new database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Create tables
            success, message = create_tables(cursor)
            if not success:
                raise Exception(message)
                
            # Create indexes
            success, message = create_indexes(cursor)
            if not success:
                raise Exception(message)
                
            # Insert initial data
            success, message = insert_initial_data(cursor)
            if not success:
                raise Exception(message)
            
            # Run specific migrations
            migrate_salary_components(conn)
            migrate_payroll_entries(conn)
            
            conn.commit()
            return True, "Database migration completed successfully"
            
        except Exception as e:
            conn.rollback()
            raise
            
        finally:
            conn.close()
            
    except Exception as e:
        logging.error(f"Database migration failed: {str(e)}")
        return False, f"Database migration failed: {str(e)}"

def migrate_salary_components(conn: sqlite3.Connection) -> None:
    """Migrate salary components to include allowance types"""
    try:
        cursor = conn.cursor()
        
        # Check if allowance_type column exists
        cursor.execute("""
            SELECT name 
            FROM pragma_table_info('salary_components') 
            WHERE name = 'allowance_type'
        """)
        
        if not cursor.fetchone():
            # Add allowance_type column
            cursor.execute("""
                ALTER TABLE salary_components 
                ADD COLUMN allowance_type TEXT
            """)
            
            # Update existing allowances with appropriate types
            cursor.execute("""
                UPDATE salary_components
                SET allowance_type = CASE
                    WHEN name LIKE '%سكن%' OR name LIKE '%Housing%' THEN 'housing'
                    WHEN name LIKE '%مواصلات%' OR name LIKE '%Transport%' THEN 'transportation'
                    WHEN name LIKE '%طبي%' OR name LIKE '%Medical%' THEN 'medical'
                    WHEN name LIKE '%تعليم%' OR name LIKE '%Education%' THEN 'education'
                    WHEN name LIKE '%طعام%' OR name LIKE '%Meal%' THEN 'meals'
                    ELSE 'other'
                END
                WHERE type = 'allowance'
            """)
            
            # Add constraint after data is updated
            cursor.execute("""
                CREATE TRIGGER validate_allowance_type
                BEFORE INSERT ON salary_components
                FOR EACH ROW
                WHEN NEW.type = 'allowance' AND (
                    NEW.allowance_type IS NULL OR 
                    NEW.allowance_type NOT IN (
                        'housing', 'transportation', 'medical',
                        'education', 'meals', 'other'
                    )
                )
                BEGIN
                    SELECT RAISE(ROLLBACK, 'Invalid allowance type');
                END;
            """)
        
        print("[OK] Salary components migration completed")
        
    except Exception as e:
        print(f"[ERROR] Error migrating salary components: {str(e)}")
        raise

def migrate_payroll_entries(conn: sqlite3.Connection) -> None:
    """Migrate payroll entries to handle tax exempt allowances"""
    try:
        cursor = conn.cursor()
        
        # Check if tax_exempt_allowances column exists
        cursor.execute("""
            SELECT name 
            FROM pragma_table_info('payroll_entries') 
            WHERE name = 'tax_exempt_allowances'
        """)
        
        if not cursor.fetchone():
            # Add tax_exempt_allowances column
            cursor.execute("""
                ALTER TABLE payroll_entries 
                ADD COLUMN tax_exempt_allowances DECIMAL(10,2) DEFAULT 0
            """)
            
            # Update existing entries to calculate tax exempt allowances
            cursor.execute("""
                UPDATE payroll_entries
                SET tax_exempt_allowances = (
                    SELECT COALESCE(SUM(
                        CASE 
                            WHEN sc.is_taxable = 0 THEN pec.value
                            WHEN tea.max_amount IS NOT NULL THEN
                                CASE
                                    WHEN tea.max_percentage IS NOT NULL THEN
                                        MIN(tea.max_amount, pec.value * tea.max_percentage / 100)
                                    ELSE
                                        MIN(tea.max_amount, pec.value)
                                END
                            ELSE 0
                        END
                    ), 0)
                    FROM payroll_entry_components pec
                    JOIN salary_components sc ON pec.component_id = sc.id
                    LEFT JOIN tax_exempt_allowances tea ON sc.allowance_type = tea.name
                    WHERE pec.payroll_entry_id = payroll_entries.id
                    AND sc.type = 'allowance'
                )
            """)
        
        print("[OK] Payroll entries migration completed")
        
    except Exception as e:
        print(f"[ERROR] Error migrating payroll entries: {str(e)}")
        raise

if __name__ == '__main__':
    migrate_database()
