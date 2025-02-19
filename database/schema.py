from .payroll_schema import PAYROLL_TABLES_SQL

SCHEMA = {
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE,
            is_active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            basic_salary DECIMAL(10,2) NOT NULL DEFAULT 0,
            hire_date DATE NOT NULL,
            birth_date DATE,
            gender TEXT CHECK(gender IN ('male', 'female')),
            marital_status TEXT,
            national_id TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            address TEXT,
            bank_account TEXT,
            bank_name TEXT,
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
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_ar TEXT,
            manager_id INTEGER,
            parent_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES employees (id),
            FOREIGN KEY (parent_id) REFERENCES departments (id)
        )
    ''',
    
    'positions': '''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            name_ar TEXT,
            department_id INTEGER,
            grade INTEGER,
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
            name_ar TEXT,
            type TEXT CHECK(type IN ('allowance', 'deduction')) NOT NULL,
            is_percentage INTEGER DEFAULT 0,
            percentage DECIMAL(5,2),
            value DECIMAL(10,2),
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            basic_salary DECIMAL(10,2) NOT NULL,
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
    
    'employee_salary_components': '''
        CREATE TABLE IF NOT EXISTS employee_salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            value DECIMAL(10,2),
            is_active INTEGER DEFAULT 1,
            effective_date DATE,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (component_id) REFERENCES salary_components (id)
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
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
    '''
}

SCHEMA.update(PAYROLL_TABLES_SQL)
