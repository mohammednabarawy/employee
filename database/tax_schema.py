"""Tax-related database schema and initial data"""

TAX_SCHEMA = {
    'tax_brackets': """
        CREATE TABLE IF NOT EXISTS tax_brackets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            min_amount DECIMAL(12,2) NOT NULL,
            max_amount DECIMAL(12,2),
            rate DECIMAL(5,4) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """,
    'tax_exempt_allowances': """
        CREATE TABLE IF NOT EXISTS tax_exempt_allowances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            max_amount DECIMAL(12,2),
            max_percentage DECIMAL(5,2),
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """,
    'employee_tax_exemptions': """
        CREATE TABLE IF NOT EXISTS employee_tax_exemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            allowance_id INTEGER NOT NULL,
            amount DECIMAL(12,2),
            percentage DECIMAL(5,2),
            start_date DATE NOT NULL,
            end_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (allowance_id) REFERENCES tax_exempt_allowances(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """
}

# Initial tax brackets (progressive tax system)
TAX_BRACKETS_DATA = [
    {
        'min_amount': 0,
        'max_amount': 15000,
        'rate': 0,
        'description': 'Tax-free bracket'
    },
    {
        'min_amount': 15000,
        'max_amount': 30000,
        'rate': 0.1,
        'description': '10% tax bracket'
    },
    {
        'min_amount': 30000,
        'max_amount': 45000,
        'rate': 0.15,
        'description': '15% tax bracket'
    },
    {
        'min_amount': 45000,
        'max_amount': 60000,
        'rate': 0.2,
        'description': '20% tax bracket'
    },
    {
        'min_amount': 60000,
        'max_amount': 200000,
        'rate': 0.225,
        'description': '22.5% tax bracket'
    },
    {
        'min_amount': 200000,
        'max_amount': None,  # No upper limit
        'rate': 0.25,
        'description': '25% tax bracket'
    }
]

# Initial tax exempt allowances
TAX_EXEMPT_ALLOWANCES_DATA = [
    {
        'name': 'Housing Allowance',
        'max_amount': 8000,
        'max_percentage': 25,
        'description': 'Housing allowance exemption up to 8,000 or 25% of basic salary'
    },
    {
        'name': 'Transportation Allowance',
        'max_amount': 2000,
        'max_percentage': 10,
        'description': 'Transportation allowance exemption up to 2,000 or 10% of basic salary'
    },
    {
        'name': 'Medical Insurance',
        'max_amount': 5000,
        'max_percentage': 15,
        'description': 'Medical insurance exemption up to 5,000 or 15% of basic salary'
    },
    {
        'name': 'Education Allowance',
        'max_amount': 7000,
        'max_percentage': 20,
        'description': 'Education allowance exemption up to 7,000 or 20% of basic salary'
    },
    {
        'name': 'Meal Allowance',
        'max_amount': 1200,
        'max_percentage': 5,
        'description': 'Meal allowance exemption up to 1,200 or 5% of basic salary'
    }
]
