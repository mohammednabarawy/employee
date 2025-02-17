CREATE_TABLES_SQL = {
    'employees': '''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_code TEXT UNIQUE,
            name TEXT NOT NULL,
            name_ar TEXT,
            dob DATE NOT NULL,
            gender TEXT NOT NULL,
            marital_status TEXT,
            nationality TEXT,
            national_id TEXT UNIQUE,
            passport_number TEXT,
            phone_primary TEXT NOT NULL,
            phone_secondary TEXT,
            email TEXT UNIQUE,
            address TEXT,
            city TEXT,
            country TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relation TEXT,
            photo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
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
            employee_status TEXT NOT NULL DEFAULT 'Active',
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
    
    'departments': '''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT,
            code TEXT UNIQUE,
            parent_id INTEGER,
            manager_id INTEGER,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES departments (id),
            FOREIGN KEY (manager_id) REFERENCES employees (id)
        )
    ''',
    
    'positions': '''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_ar TEXT,
            code TEXT UNIQUE,
            department_id INTEGER,
            description TEXT,
            min_salary DECIMAL(10,2),
            max_salary DECIMAL(10,2),
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id)
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
    
    'salary_components': '''
        CREATE TABLE IF NOT EXISTS salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_ar TEXT,
            type TEXT NOT NULL,
            calculation_type TEXT NOT NULL,
            calculation_value DECIMAL(10,2),
            taxable BOOLEAN DEFAULT 0,
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',
    
    'employee_salary_components': '''
        CREATE TABLE IF NOT EXISTS employee_salary_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            effective_date DATE NOT NULL,
            end_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (component_id) REFERENCES salary_components (id)
        )
    ''',
    
    'payroll': '''
        CREATE TABLE IF NOT EXISTS payroll (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            period_month INTEGER NOT NULL,
            period_year INTEGER NOT NULL,
            basic_salary DECIMAL(10,2) NOT NULL,
            gross_salary DECIMAL(10,2) NOT NULL,
            total_deductions DECIMAL(10,2) NOT NULL,
            net_salary DECIMAL(10,2) NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            status TEXT NOT NULL DEFAULT 'Draft',
            payment_method TEXT,
            payment_reference TEXT,
            paid_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''',
    
    'payroll_details': '''
        CREATE TABLE IF NOT EXISTS payroll_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payroll_id INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            type TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payroll_id) REFERENCES payroll (id),
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
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            expiry_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''',
    
    'users': '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            employee_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
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
