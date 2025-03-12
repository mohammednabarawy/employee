-- Company Information
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
);

-- Users
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
);

-- Departments
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_ar TEXT,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positions
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
);

-- Shifts
CREATE TABLE IF NOT EXISTS shifts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_ar TEXT,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    name_ar TEXT,
    department_id INTEGER,
    position_id INTEGER,
    shift_id INTEGER,
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
    FOREIGN KEY (position_id) REFERENCES positions (id),
    FOREIGN KEY (shift_id) REFERENCES shifts (id)
);

-- Employment Details
CREATE TABLE IF NOT EXISTS employment_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    position_id INTEGER NOT NULL,
    hire_date DATE NOT NULL,
    contract_type TEXT NOT NULL,
    contract_end_date DATE,
    probation_end_date DATE,
    employee_status TEXT NOT NULL DEFAULT 'äÔØ',
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
);

-- Salary Components
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
);

-- Employee Salary Components
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
);

-- Employee Allowances
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
);

-- Attendance
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
);

-- Leaves
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees (id),
    FOREIGN KEY (approved_by) REFERENCES users (id)
);

-- Payroll Periods
CREATE TABLE IF NOT EXISTS payroll_periods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'processing', 'completed', 'error')),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payroll Entries
CREATE TABLE IF NOT EXISTS payroll_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payroll_period_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    basic_salary DECIMAL(12,2) NOT NULL CHECK (basic_salary >= 0),
    total_allowances DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax_exempt_allowances DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_deductions DECIMAL(12,2) NOT NULL DEFAULT 0,
    leave_deductions DECIMAL(12,2) NOT NULL DEFAULT 0,
    social_insurance DECIMAL(12,2) NOT NULL DEFAULT 0,
    overtime_pay DECIMAL(12,2) NOT NULL DEFAULT 0,
    holiday_premium DECIMAL(12,2) NOT NULL DEFAULT 0,
    tax DECIMAL(12,2) NOT NULL DEFAULT 0,
    net_salary DECIMAL(12,2) NOT NULL CHECK (net_salary >= 0),
    payment_method TEXT,
    payment_status TEXT DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed')),
    payment_date DATE,
    payment_reference TEXT,
    notes TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'paid')),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_adjustments DECIMAL(12,2) DEFAULT 0,
    gross_salary DECIMAL(12,2) DEFAULT 0,
    FOREIGN KEY (employee_id) REFERENCES employees (id),
    FOREIGN KEY (payroll_period_id) REFERENCES payroll_periods (id)
);

-- Payment Methods
CREATE TABLE IF NOT EXISTS payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_ar TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);