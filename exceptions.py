class EmployeeException(Exception):
    """Base exception for employee-related errors"""
    pass

class DatabaseInitializationError(EmployeeException):
    """Raised when there's an error initializing the database"""
    pass

class EmployeeCreationError(EmployeeException):
    """Raised when there's an error creating an employee record"""
    pass

class PayrollCalculationError(EmployeeException):
    """Raised when there's an error in payroll calculations"""
    pass

class ValidationError(EmployeeException):
    """Raised when data validation fails"""
    pass
