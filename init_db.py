from database.connection import get_database
from database.schema import SCHEMA
from datetime import date

def init_db():
    db = get_database()
    conn = db.get_connection()
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
        ('DEP001', 'General Management', 'الإدارة العامة'),
        ('DEP002', 'Human Resources', 'الموارد البشرية'),
        ('DEP003', 'Finance', 'المالية'),
        ('DEP004', 'Information Technology', 'تقنية المعلومات'),
        ('DEP005', 'Sales', 'المبيعات')
    ]
    
    for code, name, name_ar in departments:
        cursor.execute("""
            INSERT OR IGNORE INTO departments (code, name, name_ar)
            VALUES (?, ?, ?)
        """, (code, name, name_ar))
    
    # Add sample positions
    positions = [
        ('POS001', 'General Manager', 'مدير عام', 1),
        ('POS002', 'HR Manager', 'مدير موارد بشرية', 2),
        ('POS003', 'Accountant', 'محاسب', 3),
        ('POS004', 'Software Developer', 'مطور برامج', 4),
        ('POS005', 'Sales Representative', 'مندوب مبيعات', 5)
    ]
    
    for code, name, name_ar, dept_id in positions:
        cursor.execute("""
            INSERT OR IGNORE INTO positions (code, name, name_ar, department_id)
            VALUES (?, ?, ?, ?)
        """, (code, name, name_ar, dept_id))
    
    # Add sample employees
    employees = [
        ('EMP001', 'Ahmed Mohamed', 'أحمد محمد', 1, 1, 15000, '2020-01-01'),
        ('EMP002', 'Mohamed Ali', 'محمد علي', 2, 2, 12000, '2020-02-01'),
        ('EMP003', 'Fatima Ahmed', 'فاطمة أحمد', 3, 3, 10000, '2020-03-01'),
        ('EMP004', 'Omar Khaled', 'عمر خالد', 4, 4, 13000, '2020-04-01'),
        ('EMP005', 'Sara Mahmoud', 'سارة محمود', 5, 5, 9000, '2020-05-01')
    ]
    
    for code, name, name_ar, dept_id, pos_id, salary, hire_date in employees:
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
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
