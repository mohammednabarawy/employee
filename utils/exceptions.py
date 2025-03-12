"""Custom exceptions for the payroll system"""

class PayrollError(Exception):
    """Base exception for payroll-related errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class PayrollValidationError(PayrollError):
    """Exception raised for validation errors in payroll data"""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field

class PayrollCalculationError(PayrollError):
    """Exception raised for errors during payroll calculations"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)

class DatabaseOperationError(PayrollError):
    """Exception raised for database operation errors"""
    def __init__(self, message: str, operation: str = None, details: dict = None):
        super().__init__(message, details)
        self.operation = operation

class TransactionError(PayrollError):
    """Exception raised for transaction-related errors"""
    pass

class EmployeeValidationError(PayrollError):
    """Exception raised for validation errors in employee data"""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field

class SalaryComponentError(PayrollError):
    """Exception raised for errors in salary component calculations"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)

class AttendanceError(PayrollError):
    """Exception raised for errors in attendance records"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)

class LeaveError(PayrollError):
    """Exception raised for errors in leave management"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)

class TaxCalculationError(PayrollError):
    """Exception raised for errors in tax calculations"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, details)

class AuthorizationError(PayrollError):
    """Exception raised for authorization-related errors"""
    def __init__(self, message: str, user_id: int = None, details: dict = None):
        super().__init__(message, details)
        self.user_id = user_id

class ConfigurationError(PayrollError):
    """Exception raised for system configuration errors"""
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(message, details)
        self.config_key = config_key
