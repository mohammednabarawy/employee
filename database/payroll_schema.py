PAYROLL_TABLES_SQL = {
    'salary_components': '''
        CREATE TABLE IF NOT EXISTS salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            type TEXT NOT NULL,  -- 'allowance' or 'deduction'
            is_taxable INTEGER DEFAULT 1,
            is_percentage INTEGER DEFAULT 0,
            value DECIMAL(10,2),
            percentage DECIMAL(5,2),
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
    ''',
    
    'employee_salary_components': '''
        CREATE TABLE IF NOT EXISTS employee_salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            value DECIMAL(10,2),
            percentage DECIMAL(5,2),
            start_date DATE NOT NULL,
            end_date DATE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (component_id) REFERENCES salary_components (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
    ''',
    
    'salaries': '''
        CREATE TABLE IF NOT EXISTS salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            base_salary REAL NOT NULL,
            allowances REAL DEFAULT 0,
            bonuses REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            overtime_pay REAL DEFAULT 0,
            total_salary REAL NOT NULL,
            effective_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''',
    
    'salary_payments': '''
        CREATE TABLE IF NOT EXISTS salary_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            amount_paid REAL NOT NULL,
            payment_date DATE NOT NULL,
            payment_mode TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''',
    
    'payroll_periods': '''
        CREATE TABLE IF NOT EXISTS payroll_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_year INTEGER NOT NULL,
            period_month INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            payment_date DATE,
            status TEXT NOT NULL DEFAULT 'draft',  -- draft, processing, approved, paid
            total_amount DECIMAL(12,2),
            total_employees INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            approved_by INTEGER,
            approved_at TIMESTAMP,
            processed_by INTEGER,
            processed_at TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            FOREIGN KEY (approved_by) REFERENCES users (id),
            FOREIGN KEY (processed_by) REFERENCES users (id),
            UNIQUE(period_year, period_month)
        )
    ''',
    
    'payroll_entries': '''
        CREATE TABLE IF NOT EXISTS payroll_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_period_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            basic_salary DECIMAL(10,2) NOT NULL,
            total_allowances DECIMAL(10,2) DEFAULT 0,
            total_deductions DECIMAL(10,2) DEFAULT 0,
            net_salary DECIMAL(10,2) NOT NULL,
            gross_salary DECIMAL(10,2) DEFAULT 0,
            payment_date DATE,
            payment_method TEXT,
            payment_status TEXT DEFAULT 'pending',  -- pending, paid, failed
            payment_reference TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (payroll_period_id) REFERENCES payroll_periods (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
    ''',
    
    'payroll_entry_details': '''
        CREATE TABLE IF NOT EXISTS payroll_entry_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_entry_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            type TEXT NOT NULL,  -- allowance or deduction
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payroll_entry_id) REFERENCES payroll_entries (id),
            FOREIGN KEY (component_id) REFERENCES salary_components (id)
        )
    ''',
    
    'payroll_entry_components': '''
        CREATE TABLE IF NOT EXISTS payroll_entry_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_entry_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            value DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payroll_entry_id) REFERENCES payroll_entries (id),
            FOREIGN KEY (component_id) REFERENCES salary_components (id)
        )
    ''',
    
    'payment_methods': '''
        CREATE TABLE IF NOT EXISTS payment_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'tax_brackets': '''
        CREATE TABLE IF NOT EXISTS tax_brackets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tax_year INTEGER NOT NULL,
            min_income REAL NOT NULL,
            max_income REAL,
            rate REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'employee_benefits': '''
        CREATE TABLE IF NOT EXISTS employee_benefits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            benefit_type TEXT NOT NULL,
            amount REAL NOT NULL,
            is_percentage INTEGER DEFAULT 0,
            start_date DATE NOT NULL,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''',
    
    'deductions': '''
        CREATE TABLE IF NOT EXISTS deductions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            deduction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            is_percentage INTEGER DEFAULT 0,
            recurring INTEGER DEFAULT 1,
            start_date DATE NOT NULL,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''',
    
    'payslip_templates': '''
        CREATE TABLE IF NOT EXISTS payslip_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL,
            template_html TEXT NOT NULL,
            is_default INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'salary_structures': '''
        CREATE TABLE IF NOT EXISTS salary_structures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            structure_name TEXT NOT NULL,
            base_percentage REAL NOT NULL,
            allowance_percentage REAL NOT NULL,
            bonus_percentage REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'employee_salary_structure': '''
        CREATE TABLE IF NOT EXISTS employee_salary_structure (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            structure_id INTEGER NOT NULL,
            effective_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (structure_id) REFERENCES salary_structures(id)
        )
    ''',
    
    'shifts': '''
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            max_regular_hours REAL DEFAULT 8,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'attendance_records': '''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            check_in TIMESTAMP NOT NULL,
            check_out TIMESTAMP,
            total_hours REAL,
            status TEXT DEFAULT 'present',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    ''',
    
    'pay_grades': '''
        CREATE TABLE IF NOT EXISTS pay_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_name TEXT NOT NULL,
            min_salary REAL NOT NULL,
            max_salary REAL NOT NULL,
            overtime_rate REAL DEFAULT 1.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

# Initial data for salary components
INITIAL_SALARY_COMPONENTS = [
    ('بدل سكن', 'Housing Allowance', 'allowance', 1, 0, 1000.00, None),
    ('بدل مواصلات', 'Transportation Allowance', 'allowance', 1, 0, 500.00, None),
    ('بدل هاتف', 'Phone Allowance', 'allowance', 1, 0, 100.00, None),
    ('تأمين طبي', 'Medical Insurance', 'deduction', 0, 1, None, 2.5),
    ('تأمينات اجتماعية', 'Social Insurance', 'deduction', 0, 1, None, 10.0)
]

# Initial data for payment methods
INITIAL_PAYMENT_METHODS = [
    ('تحويل بنكي', 'Bank Transfer'),
    ('شيك', 'Cheque'),
    ('نقدي', 'Cash')
]
