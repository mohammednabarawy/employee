from .database import Database
from .payroll_schema import PAYROLL_TABLES_SQL, INITIAL_SALARY_COMPONENTS, INITIAL_PAYMENT_METHODS

def migrate_database():
    """Migrate database to include payroll tables while preserving existing data"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Drop existing tables if they exist
        tables = [
            'payroll_entry_details',
            'payroll_entries',
            'employee_salary_components',
            'salary_components',
            'payroll_periods',
            'payment_methods'
        ]
        
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Create new tables
        for table_name, create_sql in PAYROLL_TABLES_SQL.items():
            print(f"Creating table: {table_name}")
            cursor.execute(create_sql)
        
        # Add initial salary components
        cursor.executemany("""
            INSERT INTO salary_components (
                name_ar, name, type, is_taxable,
                is_percentage, value, percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, INITIAL_SALARY_COMPONENTS)
        
        # Add initial payment methods
        cursor.executemany("""
            INSERT INTO payment_methods (
                name_ar, name
            ) VALUES (?, ?)
        """, INITIAL_PAYMENT_METHODS)
        
        # Create default salary components for existing employees
        cursor.execute("""
            SELECT e.id, ed.basic_salary 
            FROM employees e 
            JOIN employment_details ed ON e.id = ed.employee_id
            WHERE ed.employee_status = 'نشط'
        """)
        
        employees = cursor.fetchall()
        
        # Get housing allowance component id
        cursor.execute("SELECT id FROM salary_components WHERE name_ar = 'بدل سكن' LIMIT 1")
        housing_id = cursor.fetchone()[0]
        
        # Get transportation allowance component id
        cursor.execute("SELECT id FROM salary_components WHERE name_ar = 'بدل مواصلات' LIMIT 1")
        transport_id = cursor.fetchone()[0]
        
        # Add default components for each employee
        for emp_id, basic_salary in employees:
            # Add housing allowance (25% of basic salary)
            cursor.execute("""
                INSERT INTO employee_salary_components (
                    employee_id, component_id, value,
                    start_date, is_active
                ) VALUES (?, ?, ?, CURRENT_DATE, 1)
            """, (emp_id, housing_id, basic_salary * 0.25))
            
            # Add transportation allowance (fixed 500)
            cursor.execute("""
                INSERT INTO employee_salary_components (
                    employee_id, component_id, value,
                    start_date, is_active
                ) VALUES (?, ?, ?, CURRENT_DATE, 1)
            """, (emp_id, transport_id, 500))
        
        # Commit all changes
        conn.commit()
        print("Migration completed successfully!")
        return True, "Migration completed successfully!"
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {str(e)}")
        return False, f"Migration failed: {str(e)}"
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
