import re
from datetime import datetime
from PyQt5.QtCore import QDate

class ValidationUtils:
    @staticmethod
    def convert_arabic_numerals(text):
        """Convert Arabic/Persian numerals to standard numerals"""
        arabic_numerals = {
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        for arabic, standard in arabic_numerals.items():
            text = text.replace(arabic, standard)
        return text

    @staticmethod
    def parse_date(date_str):
        """Convert a date string to QDate object."""
        if not date_str:
            return QDate.currentDate()
        try:
            # Try to parse date in format YYYY-MM-DD
            year, month, day = map(int, date_str.split('-'))
            return QDate(year, month, day)
        except (ValueError, AttributeError):
            return QDate.currentDate()

    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, None
        return False, "Invalid email format"

    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        phone = ValidationUtils.convert_arabic_numerals(phone)
        pattern = r'^\+?1?\d{9,15}$'
        if re.match(pattern, phone):
            return True, None
        return False, "Invalid phone number format"

    @staticmethod
    def validate_date(date_str):
        """Validate date format (YYYY-MM-DD)"""
        try:
            # Convert Arabic numerals to standard numerals
            date_str = ValidationUtils.convert_arabic_numerals(date_str)
            datetime.strptime(date_str, '%Y-%m-%d')
            return True, None
        except ValueError:
            return False, "Invalid date format (use YYYY-MM-DD)"

    @staticmethod
    def validate_salary(salary):
        """Validate salary value"""
        try:
            if isinstance(salary, str):
                salary = ValidationUtils.convert_arabic_numerals(salary)
            salary = float(salary)
            if salary < 0:
                return False, "Salary cannot be negative"
            return True, None
        except ValueError:
            return False, "Invalid salary value"

    @staticmethod
    def validate_salary_type(salary_type):
        """Validate salary type."""
        valid_types = {'monthly', 'weekly', 'daily', 'hourly', 'project', 'commission'}
        return salary_type.lower() in valid_types

    @staticmethod
    def normalize_salary_type(salary_type):
        """Normalize salary type to database format."""
        type_mapping = {
            'monthly': 'monthly',
            'weekly': 'weekly',
            'daily': 'daily',
            'hourly': 'hourly',
            'project-based': 'project',
            'project based': 'project',
            'commission-based': 'commission',
            'commission based': 'commission'
        }
        return type_mapping.get(salary_type.lower(), '')

    @staticmethod
    def validate_bank_account(bank_account):
        """Validate bank account number format."""
        import re
        # Allow digits and dashes, minimum 8 characters
        pattern = r'^[\d-]{8,}$'
        return bool(re.match(pattern, bank_account))

    @staticmethod
    def validate_employee_data(data):
        """Validate employee data"""
        required_fields = [
            'name',
            'dob',
            'gender',
            'phone',
            'email',
            'department',
            'position',
            'hire_date',
            'contract_type',
            'salary_type',
            'basic_salary',
            'currency',
            'bank_account'
        ]
        
        # Check required fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate email
        if not ValidationUtils.validate_email(data['email']):
            return False, "Invalid email format"
        
        # Validate phone
        if not ValidationUtils.validate_phone(data['phone']):
            return False, "Invalid phone number format"
        
        # Validate secondary phone if provided
        if data.get('phone2') and not ValidationUtils.validate_phone(data['phone2']):
            return False, "Invalid secondary phone number format"
        
        # Validate national ID if provided
        if data.get('national_id') and not ValidationUtils.validate_national_id(data['national_id']):
            return False, "Invalid national ID format"
        
        # Validate passport if provided
        if data.get('passport') and not ValidationUtils.validate_passport(data['passport']):
            return False, "Invalid passport number format"
        
        # Validate gender
        if data['gender'] not in ['Male', 'Female', 'Other']:
            return False, "Invalid gender value"
        
        # Validate salary type
        if not ValidationUtils.validate_salary_type(data['salary_type']):
            return False, "Invalid salary type"
        
        # Validate bank account
        if not ValidationUtils.validate_bank_account(data['bank_account']):
            return False, "Invalid bank account format. Must be at least 8 digits and can contain dashes."
        
        return True, None

    @staticmethod
    def validate_salary_data(data):
        """Validate salary data"""
        required_fields = ['base_salary', 'bonuses', 'deductions', 'overtime_pay']
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate numeric values
        for field in required_fields:
            valid, msg = ValidationUtils.validate_salary(data[field])
            if not valid:
                return False, f"Invalid {field}: {msg}"
        
        return True, None

    @staticmethod
    def validate_payment_data(data):
        """Validate payment data"""
        required_fields = ['employee_id', 'amount_paid', 'payment_date', 'payment_mode']
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate amount
        valid, msg = ValidationUtils.validate_salary(data['amount_paid'])
        if not valid:
            return False, f"Invalid amount: {msg}"
        
        # Validate date
        valid, msg = ValidationUtils.validate_date(data['payment_date'])
        if not valid:
            return False, msg
        
        # Validate payment mode
        if data['payment_mode'] not in ['Cash', 'Bank Transfer', 'Cheque']:
            return False, "Invalid payment mode"
        
        return True, None
