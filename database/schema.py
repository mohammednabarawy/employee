from .payroll_schema import PAYROLL_TABLES_SQL

SCHEMA = {
    'company_info': '''
        CREATE TABLE IF NOT EXISTS company_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            commercial_register_number TEXT,
            social_insurance_number TEXT,
            tax_number TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            logo_data BLOB,
            logo_mime_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            full_name TEXT,
            role TEXT CHECK(role IN ('admin', 'manager', 'hr', 'accountant', 'employee')) NOT NULL DEFAULT 'employee',
            last_login TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'employees': '''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_ar TEXT,
            department_id INTEGER,
            position_id INTEGER,
            basic_salary REAL DEFAULT 0,
            hire_date DATE NOT NULL,
            birth_date DATE,
            gender TEXT CHECK(gender IN ('male', 'female')),
            marital_status TEXT,
            national_id TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            salary_currency TEXT NOT NULL DEFAULT 'SAR',
            salary_type TEXT CHECK(salary_type IN ('monthly', 'hourly', 'daily')) NOT NULL DEFAULT 'monthly',
            working_hours REAL DEFAULT 40,
            bank_account TEXT,
            bank_name TEXT,
            photo_data BLOB,
            photo_mime_type TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (position_id) REFERENCES positions (id)
        )
    ''',
    
    'departments': '''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'positions': '''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT,
            department_id INTEGER,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
    ''',
    
    'salary_components': '''
        CREATE TABLE IF NOT EXISTS salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT NOT NULL,
            type TEXT CHECK(type IN ('allowance', 'deduction')) NOT NULL,
            is_taxable INTEGER DEFAULT 0,
            is_percentage INTEGER DEFAULT 0,
            value REAL,
            percentage REAL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'employee_salary_components': '''
        CREATE TABLE IF NOT EXISTS employee_salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            value REAL,
            percentage REAL,
            start_date DATE NOT NULL,
            end_date DATE,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (component_id) REFERENCES salary_components (id)
        )
    ''',
    
    'employment_details': '''
        CREATE TABLE IF NOT EXISTS employment_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            position_id INTEGER NOT NULL,
            hire_date DATE NOT NULL,
            contract_type TEXT NOT NULL,
            contract_end_date DATE,
            probation_end_date DATE,
            employee_status TEXT NOT NULL DEFAULT 'نشط',
            work_location TEXT,
            manager_id INTEGER,
            salary_currency TEXT NOT NULL DEFAULT 'USD',
            salary_type TEXT NOT NULL,
            working_hours DECIMAL(5,2),
            bank_name TEXT,
            bank_account TEXT,
            bank_branch TEXT,
            iban TEXT,
            swift_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (position_id) REFERENCES positions (id),
            FOREIGN KEY (manager_id) REFERENCES employees (id)
        )
    ''',
    
    'employee_allowances': '''
        CREATE TABLE IF NOT EXISTS employee_allowances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            allowance_type TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'SAR',
            effective_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''',
    
    'attendance': '''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date DATE NOT NULL,
            check_in DATETIME,
            check_out DATETIME,
            status TEXT NOT NULL,
            working_hours DECIMAL(5,2),
            overtime_hours DECIMAL(5,2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''',
    
    'leaves': '''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_days INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            reason TEXT,
            approved_by INTEGER,
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''',
    
    'loans': '''
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            interest_rate DECIMAL(5,2),
            total_installments INTEGER NOT NULL,
            installment_amount DECIMAL(10,2) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            approved_by INTEGER,
            approved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''',
    
    'loan_payments': '''
        CREATE TABLE IF NOT EXISTS loan_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            payroll_id INTEGER,
            amount DECIMAL(10,2) NOT NULL,
            payment_date DATE NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES loans (id),
            FOREIGN KEY (payroll_id) REFERENCES payroll (id)
        )
    ''',
    
    'documents': '''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_data BLOB,
            mime_type TEXT,
            description TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    ''',
    
    'audit_log': '''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            description TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''',
    
    'settings': '''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, key)
        )
    ''',
    
    'salary_adjustments': '''
        CREATE TABLE IF NOT EXISTS salary_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            adjustment_type TEXT CHECK(
                adjustment_type IN ('increase', 'decrease', 'one_time')
            ) NOT NULL,
            amount REAL NOT NULL,
            percentage REAL,
            reason TEXT NOT NULL,
            effective_date DATE NOT NULL,
            end_date DATE,
            status TEXT CHECK(
                status IN ('pending', 'approved', 'rejected')
            ) NOT NULL DEFAULT 'pending',
            approved_by INTEGER,
            approved_at TIMESTAMP,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (approved_by) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    '''
}

SCHEMA.update(PAYROLL_TABLES_SQL)
