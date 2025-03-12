import os
import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from decimal import Decimal

# Path to test database
TEST_DB_PATH = ":memory:"

@pytest.fixture
def db():
    """Create a test database connection"""
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    
    # Create schema from SQL file
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql'), 'r') as f:
        schema_sql = f.read()
        conn.executescript(schema_sql)
    
    yield conn
    
    # Close connection
    conn.close()

@pytest.fixture
def mock_db():
    """Create a mock database connection for unit tests"""
    mock = MagicMock()
    # Configure mock to return cursor with expected methods
    mock.execute.return_value.fetchone.return_value = {}
    mock.execute.return_value.fetchall.return_value = []
    mock.execute.return_value.lastrowid = 1
    return mock

@pytest.fixture
def employee_repository(mock_db):
    """Create a mock employee repository"""
    from repositories.employee_repository import EmployeeRepository
    repo = EmployeeRepository(mock_db)
    return repo

@pytest.fixture
def payroll_repository(mock_db):
    """Create a mock payroll repository"""
    from repositories.payroll_repository import PayrollRepository
    repo = PayrollRepository(mock_db)
    return repo

@pytest.fixture
def payroll_service(employee_repository, payroll_repository):
    """Create a mock payroll service"""
    from services.payroll_service import PayrollService
    service = PayrollService(employee_repository, payroll_repository)
    return service

@pytest.fixture
def employee_controller(employee_repository):
    """Create a mock employee controller"""
    from controllers.employee_controller import EmployeeController
    controller = EmployeeController(employee_repository)
    return controller

@pytest.fixture
def payroll_controller(payroll_service):
    """Create a mock payroll controller"""
    from controllers.payroll_controller import PayrollController
    controller = PayrollController(payroll_service)
    return controller

@pytest.fixture
def salary_controller(db):
    """Create a salary controller with a real database"""
    from controllers.salary_controller import SalaryController
    controller = SalaryController(db)
    return controller

@pytest.fixture
def attendance_controller(db):
    """Create an attendance controller with a real database"""
    from controllers.attendance_controller import AttendanceController
    controller = AttendanceController(db)
    return controller

@pytest.fixture
def employee_id(db):
    """Create a test employee and return its ID"""
    cursor = db.execute("""
        INSERT INTO employee_types (name, is_contractor, overtime_multiplier, holiday_pay_multiplier, working_hours_per_week)
        VALUES ('Regular', 0, 1.5, 2.0, 40.0)
    """)
    employee_type_id = cursor.lastrowid
    
    cursor = db.execute("""
        INSERT INTO employees (first_name, last_name, email, employee_type_id, status)
        VALUES ('Test', 'Employee', 'test@example.com', ?, 'active')
    """, (employee_type_id,))
    employee_id = cursor.lastrowid
    
    db.execute("""
        INSERT INTO employee_details (
            employee_id, basic_salary, date_of_birth,
            bank_name, bank_account, tax_id, social_insurance_number
        ) VALUES (?, '5000.00', '1990-01-01', 'Test Bank', '123456789', 'TX123', 'SI456')
    """, (employee_id,))
    
    db.commit()
    return employee_id
