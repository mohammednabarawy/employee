import os
import sqlite3
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import Database

def fix_database_schema(db_path="employee.db"):
    """Fix the identified issues in the database schema"""
    print(f"Fixing database schema for: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} does not exist")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Fix issues one by one
    fixes_applied = []
    
    # 1. Check if employees table is missing shift_id column
    cursor.execute("PRAGMA table_info(employees)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    if 'shift_id' not in columns:
        try:
            print("Adding shift_id column to employees table...")
            cursor.execute("""
                ALTER TABLE employees 
                ADD COLUMN shift_id INTEGER REFERENCES shifts(id)
            """)
            fixes_applied.append("Added shift_id column to employees table")
        except Exception as e:
            print(f"Error adding shift_id column to employees table: {str(e)}")
    
    # 2. Check if attendance_records table is missing shift_id column
    cursor.execute("PRAGMA table_info(attendance_records)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    if 'shift_id' not in columns:
        try:
            print("Adding shift_id column to attendance_records table...")
            cursor.execute("""
                ALTER TABLE attendance_records 
                ADD COLUMN shift_id INTEGER REFERENCES shifts(id)
            """)
            fixes_applied.append("Added shift_id column to attendance_records table")
        except Exception as e:
            print(f"Error adding shift_id column to attendance_records table: {str(e)}")
    
    # 3. Check if salaries table is missing effective_date column
    cursor.execute("PRAGMA table_info(salaries)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    if 'effective_date' not in columns:
        try:
            print("Adding effective_date column to salaries table...")
            cursor.execute("""
                ALTER TABLE salaries 
                ADD COLUMN effective_date DATE
            """)
            fixes_applied.append("Added effective_date column to salaries table")
            
            # Update existing records with a default date
            cursor.execute("""
                UPDATE salaries 
                SET effective_date = '2023-01-01' 
                WHERE effective_date IS NULL
            """)
            fixes_applied.append("Updated existing salary records with default effective_date")
        except Exception as e:
            print(f"Error adding effective_date column to salaries table: {str(e)}")
    
    # 4. Fix the foreign key issue in loan_payments table
    try:
        # Check if the payroll table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payroll'")
        payroll_exists = cursor.fetchone() is not None
        
        if not payroll_exists:
            # Get the foreign key constraint
            cursor.execute("PRAGMA foreign_key_list(loan_payments)")
            fks = cursor.fetchall()
            
            payroll_fk = None
            for fk in fks:
                if fk['table'] == 'payroll':
                    payroll_fk = fk
                    break
            
            if payroll_fk:
                print("Fixing foreign key reference to non-existent payroll table...")
                
                # Create a backup of the loan_payments table
                cursor.execute("""
                    CREATE TABLE loan_payments_backup AS 
                    SELECT * FROM loan_payments
                """)
                
                # Drop the original table
                cursor.execute("DROP TABLE loan_payments")
                
                # Create a new table with corrected foreign key
                cursor.execute("""
                    CREATE TABLE loan_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        loan_id INTEGER NOT NULL,
                        payroll_entry_id INTEGER,
                        amount DECIMAL(10,2) NOT NULL,
                        payment_date DATE NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (loan_id) REFERENCES loans (id),
                        FOREIGN KEY (payroll_entry_id) REFERENCES payroll_entries (id)
                    )
                """)
                
                # Copy data back, mapping payroll_id to payroll_entry_id
                cursor.execute("""
                    INSERT INTO loan_payments (
                        id, loan_id, payroll_entry_id, amount, payment_date, notes, created_at
                    )
                    SELECT 
                        id, loan_id, payroll_id, amount, payment_date, notes, created_at 
                    FROM loan_payments_backup
                """)
                
                # Drop the backup table
                cursor.execute("DROP TABLE loan_payments_backup")
                
                fixes_applied.append("Fixed foreign key reference in loan_payments table")
        else:
            print("Payroll table exists, no need to fix loan_payments foreign key")
    except Exception as e:
        print(f"Error fixing loan_payments foreign key: {str(e)}")
    
    # Commit changes
    conn.commit()
    
    # Close connection
    conn.close()
    
    # Report results
    if fixes_applied:
        print("\nThe following fixes were applied:")
        for fix in fixes_applied:
            print(f"  - {fix}")
        print("\nDatabase schema has been updated successfully.")
        return True
    else:
        print("\nNo fixes were applied. Database schema is already correct.")
        return True

if __name__ == "__main__":
    success = fix_database_schema()
    print("\nSchema fix " + ("completed successfully" if success else "failed"))
    exit(0 if success else 1)
