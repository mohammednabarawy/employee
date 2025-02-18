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
        if not isinstance(text, str):
            return text
        for arabic, standard in arabic_numerals.items():
            text = text.replace(arabic, standard)
        return text

    @staticmethod
    def parse_date(date_str):
        """Parse date string to QDate."""
        if not date_str:
            return QDate.currentDate()
        try:
            return QDate.fromString(date_str, 'yyyy-MM-dd')
        except:
            return QDate.currentDate()

    @staticmethod
    def validate_email(email):
        """Validate email format."""
        if not email:
            return False
        # Basic email validation
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    @staticmethod
    def validate_phone(phone):
        """Validate phone number format."""
        if not phone:
            return False
        # Convert Arabic numerals if present
        phone = ValidationUtils.convert_arabic_numerals(phone)
        # Remove spaces, dashes, and plus sign
        phone = re.sub(r'[ \-+]', '', phone)
        # Check if the remaining string is all digits and has appropriate length
        return bool(re.match(r'^\d{8,15}$', phone))

    @staticmethod
    def validate_national_id(national_id):
        """Validate national ID format."""
        if not national_id:
            return True  # Optional field
        # Convert Arabic numerals if present
        national_id = ValidationUtils.convert_arabic_numerals(national_id)
        # Remove any spaces
        national_id = national_id.replace(' ', '')
        # National ID should be 10-14 digits
        return bool(re.match(r'^\d{10,14}$', national_id))

    @staticmethod
    def validate_passport(passport):
        """Validate passport number format."""
        if not passport:
            return True  # Optional field
        # Convert to uppercase and remove spaces
        passport = passport.upper().replace(' ', '')
        # Passport number should be 6-9 characters, letters and numbers
        return bool(re.match(r'^[A-Z0-9]{6,9}$', passport))

    @staticmethod
    def validate_bank_account(account):
        """Validate bank account format."""
        # Accept any non-empty string for bank account
        return bool(account and account.strip())

    @staticmethod
    def validate_salary_type(salary_type):
        """Validate salary type."""
        valid_types = {
            'شهري', 'أسبوعي', 'يومي', 'بالساعة', 'بالمشروع', 'بالعمولة',  # Arabic
            'monthly', 'weekly', 'daily', 'hourly', 'project', 'commission'  # English
        }
        return salary_type in valid_types

    @staticmethod
    def normalize_salary_type(salary_type):
        """Convert display salary type to database format."""
        type_map = {
            # Arabic
            'شهري': 'monthly',
            'أسبوعي': 'weekly',
            'يومي': 'daily',
            'بالساعة': 'hourly',
            'بالمشروع': 'project',
            'بالعمولة': 'commission',
            # English
            'Monthly': 'monthly',
            'Weekly': 'weekly',
            'Daily': 'daily',
            'Hourly': 'hourly',
            'Project-based': 'project',
            'Commission-based': 'commission'
        }
        return type_map.get(salary_type, salary_type.lower())

    @staticmethod
    def validate_salary(salary):
        """Validate salary value"""
        try:
            if isinstance(salary, str):
                salary = ValidationUtils.convert_arabic_numerals(salary)
            salary = float(salary)
            if salary < 0:
                return False, "لا يمكن أن يكون الراتب بالسالب"
            return True, None
        except ValueError:
            return False, "قيمة الراتب غير صحيحة"

    @staticmethod
    def validate_date(date_str):
        """Validate date format (YYYY-MM-DD)"""
        try:
            # Convert Arabic numerals to standard numerals
            date_str = ValidationUtils.convert_arabic_numerals(date_str)
            datetime.strptime(date_str, '%Y-%m-%d')
            return True, None
        except ValueError:
            return False, "صيغة التاريخ غير صحيحة (استخدم YYYY-MM-DD)"

    @staticmethod
    def validate_employee_data(data):
        """Validate employee data"""
        # Only name and hire_date are strictly required
        required_fields = {
            'name': 'الاسم',
            'hire_date': 'تاريخ التعيين'
        }
        
        # Check required fields
        missing_fields = [required_fields[field] for field in required_fields if not data.get(field)]
        if missing_fields:
            return False, f"الحقول المطلوبة غير مكتملة: {' ، '.join(missing_fields)}"
        
        # Validate email if provided
        if data.get('email') and not ValidationUtils.validate_email(data['email']):
            return False, "صيغة البريد الإلكتروني غير صحيحة"
        
        # Validate phone if provided
        if data.get('phone_primary') and not ValidationUtils.validate_phone(data['phone_primary']):
            return False, "صيغة رقم الهاتف غير صحيحة"
        
        # Validate secondary phone if provided
        if data.get('phone_secondary') and not ValidationUtils.validate_phone(data['phone_secondary']):
            return False, "صيغة رقم الهاتف البديل غير صحيحة"
        
        # Validate national ID if provided
        if data.get('national_id') and not ValidationUtils.validate_national_id(data['national_id']):
            return False, "صيغة رقم الهوية غير صحيحة"
        
        # Validate passport if provided
        if data.get('passport_number') and not ValidationUtils.validate_passport(data['passport_number']):
            return False, "صيغة رقم جواز السفر غير صحيحة"
        
        # Validate gender if provided
        if data.get('gender'):
            valid_genders = {'ذكر', 'أنثى', 'Male', 'Female', 'Other'}
            if data['gender'] not in valid_genders:
                return False, "قيمة الجنس غير صحيحة"
        
        # Validate dates if provided
        if data.get('dob'):
            success, error = ValidationUtils.validate_date(data['dob'])
            if not success:
                return False, f"تاريخ الميلاد: {error}"
        
        if data.get('hire_date'):
            success, error = ValidationUtils.validate_date(data['hire_date'])
            if not success:
                return False, f"تاريخ التعيين: {error}"
        
        # Validate salary type if provided
        if data.get('salary_type') and not ValidationUtils.validate_salary_type(data['salary_type']):
            return False, "نوع الراتب غير صحيح"
        
        # Validate salary if provided
        if data.get('basic_salary') is not None:
            success, error = ValidationUtils.validate_salary(data['basic_salary'])
            if not success:
                return False, f"الراتب الأساسي: {error}"
        
        # Validate bank account if provided
        if data.get('bank_account') and not ValidationUtils.validate_bank_account(data['bank_account']):
            return False, "رقم الحساب البنكي غير صحيح"
        
        return True, None

    @staticmethod
    def validate_salary_data(data):
        """Validate salary data"""
        required_fields = {
            'employee_id': 'رقم الموظف',
            'basic_salary': 'الراتب الأساسي',
            'payment_date': 'تاريخ الدفع',
            'payment_method': 'طريقة الدفع',
            'payment_status': 'حالة الدفع'
        }
        
        # Check required fields
        missing_fields = [required_fields[field] for field in required_fields if not data.get(field)]
        if missing_fields:
            return False, f"الحقول المطلوبة غير مكتملة: {' ، '.join(missing_fields)}"
        
        # Validate employee ID
        if not str(data['employee_id']).strip():
            return False, "رقم الموظف مطلوب"
        
        # Validate basic salary
        success, error = ValidationUtils.validate_salary(data['basic_salary'])
        if not success:
            return False, f"الراتب الأساسي: {error}"
        
        # Validate payment date
        success, error = ValidationUtils.validate_date(data['payment_date'])
        if not success:
            return False, f"تاريخ الدفع: {error}"
        
        # Validate payment method
        valid_methods = {'تحويل بنكي', 'نقدي', 'شيك'}
        if data['payment_method'] not in valid_methods:
            return False, "طريقة الدفع غير صحيحة"
        
        # Validate payment status
        valid_statuses = {'تم الدفع', 'معلق', 'ملغي'}
        if data['payment_status'] not in valid_statuses:
            return False, "حالة الدفع غير صحيحة"
        
        return True, None
