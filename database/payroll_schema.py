PAYROLL_TABLES_SQL = {
    'salary_components': '''
        CREATE TABLE IF NOT EXISTS salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('allowance', 'deduction')),
            allowance_type TEXT CHECK (
                type != 'allowance' OR 
                allowance_type IN (
                    'housing', 'transportation', 'medical',
                    'education', 'meals', 'other'
                )
            ),
            is_taxable INTEGER DEFAULT 1,
            is_percentage INTEGER DEFAULT 0,
            value DECIMAL(10,2),
            percentage DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id),
            CHECK (
                (is_percentage = 0 AND value IS NOT NULL AND percentage IS NULL) OR
                (is_percentage = 1 AND percentage IS NOT NULL AND value IS NULL)
            ),
            CHECK (
                (percentage IS NULL OR (percentage >= 0 AND percentage <= 100)) AND
                (value IS NULL OR value >= 0)
            )
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
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (component_id) REFERENCES salary_components (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            CHECK (start_date <= end_date OR end_date IS NULL)
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
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
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
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    ''',
    
    'payroll_periods': '''
        CREATE TABLE IF NOT EXISTS payroll_periods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_year INTEGER NOT NULL,
            period_month INTEGER NOT NULL CHECK (period_month BETWEEN 1 AND 12),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            payment_date DATE,
            status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'approved', 'cancelled', 'closed')),
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
            UNIQUE(period_year, period_month),
            CHECK (start_date <= end_date)
        )
    ''',
    
    'payroll_entries': '''
        CREATE TABLE IF NOT EXISTS payroll_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_period_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            basic_salary DECIMAL(10,2) NOT NULL CHECK (basic_salary >= 0 AND basic_salary <= 1000000),
            total_allowances DECIMAL(10,2) DEFAULT 0,
            tax_exempt_allowances DECIMAL(10,2) DEFAULT 0,
            total_deductions DECIMAL(10,2) DEFAULT 0,
            overtime_pay DECIMAL(10,2) DEFAULT 0,
            holiday_premium DECIMAL(10,2) DEFAULT 0,
            leave_deductions DECIMAL(10,2) DEFAULT 0,
            net_salary DECIMAL(10,2) NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'processing', 'paid', 'cancelled', 'failed')),
            payment_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (payroll_period_id) REFERENCES payroll_periods(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
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
            FOREIGN KEY (payroll_entry_id) REFERENCES payroll_entries (id) ON DELETE CASCADE,
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
            FOREIGN KEY (payroll_entry_id) REFERENCES payroll_entries (id) ON DELETE CASCADE,
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
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
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
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
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
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
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
            attendance_date DATE NOT NULL,
            check_in TIMESTAMP,
            check_out TIMESTAMP,
            total_hours DECIMAL(5,2),
            status TEXT DEFAULT 'present',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            CHECK (status IN ('present', 'absent', 'late', 'half-day', 'leave')),
            CHECK (total_hours >= 0 OR total_hours IS NULL)
        )
    ''',
    
    'overtime_records': '''
        CREATE TABLE IF NOT EXISTS overtime_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            record_date DATE NOT NULL,
            hours DECIMAL(5,2) NOT NULL,
            rate DECIMAL(5,2) NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            approved_by INTEGER,
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (approved_by) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            CHECK (status IN ('pending', 'approved', 'rejected')),
            CHECK (hours > 0),
            CHECK (rate > 0)
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
    ''',
    
    'employee_types': '''
        CREATE TABLE IF NOT EXISTS employee_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            working_hours_per_week INTEGER NOT NULL,
            overtime_multiplier DECIMAL(3,2) DEFAULT 1.5,
            holiday_pay_multiplier DECIMAL(3,2) DEFAULT 2.0,
            prorated_benefits INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            UNIQUE(name),
            CHECK (working_hours_per_week > 0),
            CHECK (overtime_multiplier >= 1.0),
            CHECK (holiday_pay_multiplier >= 1.0)
        )
    ''',
    
    'public_holidays': '''
        CREATE TABLE IF NOT EXISTS public_holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            holiday_date DATE NOT NULL,
            description TEXT,
            pay_multiplier DECIMAL(3,2) DEFAULT 2.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            UNIQUE(holiday_date),
            CHECK (pay_multiplier >= 1.0)
        )
    ''',
    
    'leave_types': '''
        CREATE TABLE IF NOT EXISTS leave_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            annual_days INTEGER NOT NULL,
            paid BOOLEAN NOT NULL DEFAULT 1,
            requires_approval BOOLEAN NOT NULL DEFAULT 1,
            affects_salary BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            UNIQUE(name),
            CHECK (annual_days >= 0)
        )
    ''',
    
    'leave_balances': '''
        CREATE TABLE IF NOT EXISTS leave_balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type_id INTEGER NOT NULL,
            year INTEGER NOT NULL,
            total_days DECIMAL(5,2) NOT NULL,
            used_days DECIMAL(5,2) DEFAULT 0,
            remaining_days DECIMAL(5,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (leave_type_id) REFERENCES leave_types (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            UNIQUE(employee_id, leave_type_id, year),
            CHECK (total_days >= 0),
            CHECK (used_days >= 0),
            CHECK (remaining_days >= 0),
            CHECK (used_days <= total_days),
            CHECK (remaining_days = total_days - used_days)
        )
    ''',
    
    'leave_requests': '''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_days DECIMAL(5,2) NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            approved_by INTEGER,
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (leave_type_id) REFERENCES leave_types (id),
            FOREIGN KEY (approved_by) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),
            CHECK (total_days > 0),
            CHECK (start_date <= end_date)
        )
    ''',
    
    'tax_exempt_allowances': '''
        CREATE TABLE IF NOT EXISTS tax_exempt_allowances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            max_amount DECIMAL(10,2),
            max_percentage DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
        )
    ''',
    
    'employees': '''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            hire_date DATE NOT NULL,
            employee_type_id INTEGER NOT NULL,
            department_id INTEGER,
            position_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_type_id) REFERENCES employee_types (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (position_id) REFERENCES positions (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            CHECK (status IN ('active', 'inactive', 'terminated', 'on_leave'))
        )
    ''',
    
    'employee_details': '''
        CREATE TABLE IF NOT EXISTS employee_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL UNIQUE,
            basic_salary DECIMAL(10,2) NOT NULL,
            bank_name TEXT,
            bank_account TEXT,
            tax_id TEXT,
            social_insurance_number TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id),
            CHECK (basic_salary >= 0)
        )
    ''',
    
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (role IN ('admin', 'manager', 'hr', 'employee'))
        )
    ''',
    
    'indexes': [
        # Composite indexes for common query patterns
        """
        CREATE INDEX IF NOT EXISTS idx_payroll_entries_employee_period ON payroll_entries(
            employee_id, payroll_period_id, payment_status
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendance_records(
            employee_id, date, status
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_salary_components_type ON salary_components(
            type, is_active, allowance_type
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_payroll_periods_year_month ON payroll_periods(
            period_year, period_month, status
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_employee_salary_components ON employee_salary_components(
            employee_id, component_id, is_active
        )
        """
    ],
    
    'foreign_keys': [
        # Add ON DELETE CASCADE for appropriate relationships
        """
        PRAGMA foreign_keys = ON;
        """,
        """
        CREATE TRIGGER IF NOT EXISTS delete_employee_cascade
        AFTER DELETE ON employees
        FOR EACH ROW
        BEGIN
            DELETE FROM employee_salary_components WHERE employee_id = OLD.id;
            DELETE FROM payroll_entries WHERE employee_id = OLD.id;
            DELETE FROM attendance_records WHERE employee_id = OLD.id;
        END;
        """
    ]
}

# Export schema queries
SCHEMA_QUERIES = {
    'salary_components': PAYROLL_TABLES_SQL['salary_components'],
    'employee_salary_components': PAYROLL_TABLES_SQL['employee_salary_components'],
    'payroll_periods': PAYROLL_TABLES_SQL['payroll_periods'],
    'payroll_entries': PAYROLL_TABLES_SQL['payroll_entries'],
    'payment_methods': PAYROLL_TABLES_SQL['payment_methods'],
    'public_holidays': PAYROLL_TABLES_SQL['public_holidays'],
    'leave_types': PAYROLL_TABLES_SQL['leave_types'],
    'leave_balances': PAYROLL_TABLES_SQL['leave_balances'],
    'leave_requests': PAYROLL_TABLES_SQL['leave_requests'],
    'tax_exempt_allowances': PAYROLL_TABLES_SQL['tax_exempt_allowances'],
    'create_indexes': PAYROLL_TABLES_SQL['indexes'],
    'add_constraints': PAYROLL_TABLES_SQL['foreign_keys']
}

# Initial data for salary components
INITIAL_SALARY_COMPONENTS = [
    ('بدل سكن', 'Housing Allowance', 'allowance', 'housing', 1, 0, 1000.00, None),
    ('بدل مواصلات', 'Transportation Allowance', 'allowance', 'transportation', 1, 0, 500.00, None),
    ('بدل هاتف', 'Phone Allowance', 'allowance', 'other', 1, 0, 100.00, None),
    ('تأمين طبي', 'Medical Insurance', 'deduction', None, 0, 1, None, 2.5),
    ('تأمينات اجتماعية', 'Social Insurance', 'deduction', None, 0, 1, None, 10.0)
]

# Initial data for users
INITIAL_USERS = [
    ('admin', 'admin@company.com', 'pbkdf2:sha256:600000$dummypasswordhash', 'System', 'Admin', 'admin', 1)
]

# Initial data for employee types
INITIAL_EMPLOYEE_TYPES = [
    ('Full Time', 'دوام كامل', 40, 1.5, 2.0, 1),
    ('Part Time', 'دوام جزئي', 20, 1.5, 2.0, 0),
    ('Contractor', 'متعاقد', 40, 1.0, 1.0, 0),
    ('Temporary', 'مؤقت', 40, 1.5, 2.0, 0)
]

# Initial data for payment methods
INITIAL_PAYMENT_METHODS = [
    ('Bank Transfer', 'تحويل بنكي'),
    ('Cash', 'نقدي'),
    ('Check', 'شيك')
]

# Initial data for leave types
INITIAL_LEAVE_TYPES = [
    ('Annual Leave', 'إجازة سنوية', 21, 1, 1),
    ('Sick Leave', 'إجازة مرضية', 14, 1, 1),
    ('Unpaid Leave', 'إجازة بدون راتب', 0, 0, 1),
    ('Public Holiday', 'عطلة رسمية', 0, 1, 0)
]

# Initial data for tax exempt allowances
INITIAL_TAX_EXEMPT_ALLOWANCES = [
    ('Housing Allowance', 25000.00, 40.0),
    ('Transportation Allowance', 12000.00, 20.0),
    ('Education Allowance', 15000.00, 25.0),
    ('Medical Insurance', 10000.00, 15.0)
]
