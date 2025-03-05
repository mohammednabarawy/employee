import os
import sys

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.schema import SCHEMA
from datetime import date
import sqlite3

def init_db():
    # Create connection to database
    conn = sqlite3.connect('employee.db')
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create tables in the correct order
    table_order = [
        'users',
        'departments',  # No foreign keys
        'positions',   # References departments
        'employees',   # References departments and positions
        'salary_components',  # No foreign keys
        'employment_details',
        'employee_allowances',
        'attendance',
        'leaves',
        'employee_salary_components',
        'loans',
        'loan_payments',
        'documents',
        'audit_log',
        'settings',
        'payroll_periods',
        'payroll_entries',
        'payroll_entry_details',
        'payroll_entry_components',
        'payment_methods'
    ]
    
    # Create tables
    for table_name in table_order:
        if table_name in SCHEMA:
            print(f"Creating table {table_name}...")
            cursor.execute(SCHEMA[table_name])
    
    # Create default user if not exists
    cursor.execute("""
        INSERT OR IGNORE INTO users (
            id, username, password, email, is_active, role
        ) VALUES (
            1, 'admin', 'admin', 'admin@example.com', 1, 'admin'
        )
    """)
    
    # Add sample departments
    departments = [
        ('General Management', 'الإدارة العامة', 'Responsible for overall company management'),
        ('Human Resources', 'الموارد البشرية', 'Handles employee affairs and recruitment'),
        ('Finance', 'المالية', 'Manages company finances and accounting'),
        ('Information Technology', 'تقنية المعلومات', 'Manages IT infrastructure and software development'),
        ('Sales', 'المبيعات', 'Handles sales and customer relationships')
    ]
    
    for name, name_ar, description in departments:
        cursor.execute("""
            INSERT OR IGNORE INTO departments (name, name_ar, description)
            VALUES (?, ?, ?)
        """, (name, name_ar, description))
    
    # Add sample positions
    positions = [
        ('General Manager', 'مدير عام', 1, 'Responsible for company management'),
        ('HR Manager', 'مدير موارد بشرية', 2, 'Manages HR department'),
        ('Accountant', 'محاسب', 3, 'Handles accounting and finances'),
        ('Software Developer', 'مطور برامج', 4, 'Develops software applications'),
        ('Sales Representative', 'مندوب مبيعات', 5, 'Handles sales and customer relations')
    ]
    
    for name, name_ar, dept_id, description in positions:
        cursor.execute("""
            INSERT OR IGNORE INTO positions (name, name_ar, department_id, description)
            VALUES (?, ?, ?, ?)
        """, (name, name_ar, dept_id, description))
    
    # Add sample employees
    employees = [
        ('Ahmed Mohamed', 'أحمد محمد', 1, 1, 15000, '2020-01-01'),
        ('Mohamed Ali', 'محمد علي', 2, 2, 12000, '2020-02-01'),
        ('Fatima Ahmed', 'فاطمة أحمد', 3, 3, 10000, '2020-03-01'),
        ('Omar Khaled', 'عمر خالد', 4, 4, 13000, '2020-04-01'),
        ('Sara Mahmoud', 'سارة محمود', 5, 5, 9000, '2020-05-01')
    ]
    
    for i, (name, name_ar, dept_id, pos_id, salary, hire_date) in enumerate(employees, 1):
        # Generate a unique code for each employee
        code = f"EMP{i:03d}"
        
        cursor.execute("""
            INSERT OR IGNORE INTO employees (
                code, name, name_ar, department_id, position_id,
                basic_salary, hire_date, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (code, name, name_ar, dept_id, pos_id, salary, hire_date))
    
    # Add sample salary components
    components = [
        ('Housing Allowance', 'بدل سكن', 'allowance', 1, 0, 25),
        ('Transportation Allowance', 'بدل مواصلات', 'allowance', 1, 0, 10),
        ('Work Nature Allowance', 'بدل طبيعة عمل', 'allowance', 1, 0, 15),
        ('Social Insurance', 'تأمينات اجتماعية', 'deduction', 1, 1, 10),
        ('Medical Insurance', 'تأمين طبي', 'deduction', 1, 0, 500)
    ]
    
    for name, name_ar, type, is_active, is_percentage, value in components:
        cursor.execute("""
            INSERT OR IGNORE INTO salary_components (
                name, name_ar, type, is_active, is_percentage, 
                percentage, value
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, name_ar, type, is_active, is_percentage, 
              value if is_percentage else None, value if not is_percentage else None))
    
    # Add payment methods
    payment_methods = [
        ('Cash', 'نقدي'),
        ('Bank Transfer', 'تحويل بنكي'),
        ('Check', 'شيك'),
        ('Digital Wallet', 'محفظة رقمية')
    ]
    
    for name, name_ar in payment_methods:
        cursor.execute("""
            INSERT OR IGNORE INTO payment_methods (name, name_ar, is_active)
            VALUES (?, ?, 1)
        """, (name, name_ar))
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
