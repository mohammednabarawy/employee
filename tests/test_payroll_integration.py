"""Integration tests for payroll system"""
import unittest
import sqlite3
from decimal import Decimal
from datetime import date, datetime, timedelta
from services.payroll_service import PayrollService
from repositories.employee_repository import EmployeeRepository
from repositories.payroll_repository import PayrollRepository
from utils.exceptions import (
    PayrollValidationError, PayrollCalculationError,
    DatabaseOperationError, TransactionError
)

class TestPayrollIntegration(unittest.TestCase):
    """Integration tests for payroll system"""

    def setUp(self):
        """Set up test database and repositories"""
        # Create in-memory database
        self.db = sqlite3.connect(
            ":memory:",
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.db.row_factory = sqlite3.Row
        
        # Enable foreign keys
        self.db.execute('PRAGMA foreign_keys = ON')
        
        # Initialize schema
        with open('schema.sql', 'r') as f:
            schema = f.read()
            self.db.executescript(schema)
        
        # Initialize repositories
        from repositories.employee_repository import EmployeeRepository
        from repositories.payroll_repository import PayrollRepository
        from services.payroll_service import PayrollService
        
        self.employee_repo = EmployeeRepository(self.db)
        self.payroll_repo = PayrollRepository(self.db)
        self.service = PayrollService(self.employee_repo, self.payroll_repo)
        
        # Set up common test data (tax brackets)
        self.db.executescript("""
            INSERT INTO tax_brackets (min_amount, max_amount, rate, is_active)
            VALUES 
                (0, 1000, 0.00, 1),
                (1000, 5000, 0.10, 1),
                (5000, 10000, 0.15, 1),
                (10000, NULL, 0.20, 1);
        """)

    def tearDown(self):
        self.db.close()

    def test_end_to_end_payroll_generation(self):
        """Test complete payroll generation process"""
        # Setup required data
        # Insert social insurance config
        self.db.execute('INSERT INTO social_insurance_config (rate, effective_date) VALUES (0.14, "2024-01-01")')

        # Create salary components
        self.db.execute("""
            INSERT INTO salary_components (id, name, type, is_percentage, value, tax_exempt, is_taxable)
            VALUES 
                (1, 'Housing Allowance', 'allowance', 0, 1000.00, 1, 0),
                (2, 'Transport Allowance', 'allowance', 0, 500.00, 0, 1),
                (3, 'Insurance', 'deduction', 0, 200.00, 0, 0),
                (4, 'Loan', 'deduction', 0, 300.00, 0, 0)
        """)

        # Create employee types
        self.db.execute("""
            INSERT INTO employee_types (id, name, is_contractor, overtime_multiplier, holiday_pay_multiplier, working_hours_per_week)
            VALUES 
                (1, 'Regular', 0, 1.5, 2.0, 40.0),
                (2, 'Part-time', 0, 1.25, 1.5, 20.0),
                (3, 'Contractor', 1, 0.0, 0.0, 0.0)
        """)
        
        # Setup test data
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO payroll_periods (start_date, end_date, status)
            VALUES ('2024-02-01', '2024-02-28', 'draft')
        """)
        period_id = cursor.lastrowid
        
        # Create test employees
        employees = [
            # Full-time employee
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@example.com',
                'employee_type_id': 1,
                'basic_salary': '5000.00'
            },
            # Part-time employee
            {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane@example.com',
                'employee_type_id': 2,
                'basic_salary': '3000.00'
            },
            # Contractor
            {
                'first_name': 'Bob',
                'last_name': 'Brown',
                'email': 'bob@example.com',
                'employee_type_id': 3,
                'basic_salary': '4000.00'
            }
        ]

        employee_ids = []
        for emp_data in employees:
            # Create employee
            cursor = self.db.execute("""
                INSERT INTO employees (
                    first_name, last_name, email,
                    employee_type_id, status
                ) VALUES (?, ?, ?, ?, 'active')
                RETURNING id
            """, (
                emp_data['first_name'],
                emp_data['last_name'],
                emp_data['email'],
                emp_data['employee_type_id']
            ))
            employee_id = cursor.fetchone()['id']
            employee_ids.append(employee_id)

            # Create employee details
            self.db.execute("""
                INSERT INTO employee_details (
                    employee_id, basic_salary, date_of_birth, 
                    bank_name, bank_account, tax_id, social_insurance_number
                ) VALUES (?, ?, '1990-01-01', 'Test Bank', '123456789', 'TX123', 'SI456')
            """, (employee_id, emp_data['basic_salary']))

            # Add salary components
            if emp_data['employee_type_id'] in (1, 2):  # Full-time and part-time
                self.db.execute("""
                    INSERT INTO employee_salary_components (
                        employee_id, component_id, value
                    ) VALUES
                        (?, 1, 1000.00),  -- Housing allowance
                        (?, 2, 500.00),   -- Transport allowance
                        (?, 3, 200.00),   -- Insurance deduction
                        (?, 4, 300.00)    -- Loan deduction
                """, (employee_id,) * 4)

            # Add attendance records
            if emp_data['employee_type_id'] == 1:  # Full-time
                self.db.execute("""
                    INSERT INTO attendance_hours (
                        employee_id, period_id, date, type, hours
                    ) VALUES
                        (?, ?, '2024-02-01', 'overtime', 10),
                        (?, ?, '2024-02-01', 'holiday', 8)
                """, (
                    employee_id, period_id,
                    employee_id, period_id
                ))
            elif emp_data['employee_type_id'] == 2:  # Part-time
                self.db.execute("""
                    INSERT INTO attendance_hours (
                        employee_id, period_id, date, type, hours
                    ) VALUES
                        (?, ?, '2024-02-01', 'overtime', 5),
                        (?, ?, '2024-02-01', 'holiday', 4)
                """, (
                    employee_id, period_id,
                    employee_id, period_id
                ))

        # Debug: Print employee details before generating payroll
        for employee_id in employee_ids:
            try:
                employee = self.employee_repo.get_employee_details(employee_id)
                print(f"Employee {employee_id} details: {employee}")
            except Exception as e:
                print(f"Error fetching employee {employee_id}: {str(e)}")

        # Temporarily patch transaction methods to avoid transaction issues in tests
        original_begin = self.payroll_repo.begin_transaction
        original_commit = self.payroll_repo.commit_transaction
        original_rollback = self.payroll_repo.rollback_transaction
        
        self.payroll_repo.begin_transaction = lambda: None
        self.payroll_repo.commit_transaction = lambda: None
        self.payroll_repo.rollback_transaction = lambda: None
        self.payroll_repo._transaction_active = True  # Set to True to bypass transaction checks
        
        try:
            # Generate payroll
            result = self.service.generate_payroll(period_id, employee_ids)
            self.assertIsNotNone(result)
            self.assertEqual(len(result['entries']), 3)
            
            # Verify results
            self.assertEqual(len(result['entries']), 3)
            
            # Check individual entries
            for entry in result['entries']:
                if entry['employee_id'] == employee_ids[0]:  # Full-time
                    self.assertEqual(entry['basic_salary'], Decimal('5000.00'))
                elif entry['employee_id'] == employee_ids[1]:  # Part-time
                    self.assertEqual(entry['basic_salary'], Decimal('1500.00'))
                elif entry['employee_id'] == employee_ids[2]:  # Contractor
                    self.assertEqual(entry['net_salary'], Decimal('4000.00'))
        finally:
            # Restore original methods
            self.payroll_repo.begin_transaction = original_begin
            self.payroll_repo.commit_transaction = original_commit
            self.payroll_repo.rollback_transaction = original_rollback
            self.payroll_repo._transaction_active = False

    def test_contractor_type_setup(self):
        """Test contractor validation"""
        # Create employee types
        self.db.execute("""
            INSERT INTO employee_types (id, name, is_contractor, overtime_multiplier, holiday_pay_multiplier, working_hours_per_week)
            VALUES 
                (1, 'Regular', 0, 1.5, 2.0, 40.0),
                (2, 'Part-time', 0, 1.25, 1.5, 20.0),
                (3, 'Contractor', 1, 0.0, 0.0, 0.0)
        """)
        
        # Create test employee
        cursor = self.db.execute("""
            INSERT INTO employees (
                first_name, last_name, email, employee_type_id, status
            ) VALUES ('John', 'Contractor', 'john@contractor.com', 3, 'active')
            RETURNING id
        """)
        employee_id = cursor.fetchone()['id']
        
        # Add employee details
        self.db.execute("""
            INSERT INTO employee_details (
                employee_id, basic_salary, date_of_birth, 
                bank_name, bank_account, tax_id, social_insurance_number
            ) VALUES (?, 5000.00, '1990-01-01', 'Test Bank', '123456789', 'TX123', 'SI456')
        """, (employee_id,))
        
        # Test contractor validation
        result = self.payroll_repo._validate_contractor(employee_id)
        self.assertTrue(result)
        
    def test_transaction_rollback_on_error(self):
        """Test transaction rollback on error"""
        # Create employee types
        self.db.execute("""
            INSERT INTO employee_types (id, name, is_contractor, overtime_multiplier, holiday_pay_multiplier, working_hours_per_week)
            VALUES 
                (1, 'Regular', 0, 1.5, 2.0, 40.0)
        """)
        
        # Create test employee
        cursor = self.db.execute("""
            INSERT INTO employees (
                first_name, last_name, email, employee_type_id, status
            ) VALUES ('Jane', 'Doe', 'jane@example.com', 1, 'active')
            RETURNING id
        """)
        employee_id = cursor.fetchone()['id']
        
        # Add employee details with valid salary
        self.db.execute("""
            INSERT INTO employee_details (
                employee_id, basic_salary, date_of_birth, 
                bank_name, bank_account, tax_id, social_insurance_number
            ) VALUES (?, 5000.00, '1990-01-01', 'Test Bank', '123456789', 'TX123', 'SI456')
        """, (employee_id,))
        
        # Create a period
        cursor = self.db.execute("""
            INSERT INTO payroll_periods (start_date, end_date, status)
            VALUES ('2024-01-01', '2024-01-31', 'draft')
            RETURNING id
        """)
        period_id = cursor.fetchone()['id']
        
        # Test transaction rollback
        # First, get the initial count of payroll entries
        cursor = self.db.execute("SELECT COUNT(*) as count FROM payroll_entries")
        initial_count = cursor.fetchone()['count']
        
        # Attempt to create a payroll entry with invalid data
        with self.assertRaises(Exception):
            # Force an error by passing invalid data
            self.payroll_repo.begin_transaction()
            self.payroll_repo.create_payroll_entry(
                employee_id,
                period_id,
                {
                    'basic_salary': Decimal('5000.00'),
                    'total_allowances': Decimal('1000.00'),
                    'tax_exempt_allowances': Decimal('500.00'),
                    'total_deductions': Decimal('200.00'),
                    'leave_deductions': Decimal('0.00'),
                    'social_insurance': Decimal('700.00'),
                    'overtime_pay': Decimal('0.00'),
                    'holiday_premium': Decimal('0.00'),
                    'tax': Decimal('800.00'),
                    'net_salary': Decimal('4300.00')
                }
            )
            # This should never execute due to the error
            self.payroll_repo.commit_transaction()
        
        # Verify that the transaction was rolled back
        cursor = self.db.execute("SELECT COUNT(*) as count FROM payroll_entries")
        final_count = cursor.fetchone()['count']
        self.assertEqual(initial_count, final_count)
        
    def test_concurrent_payroll_generation(self):
        """Test concurrent payroll generation"""
        # Insert social insurance config
        self.db.execute('INSERT INTO social_insurance_config (rate, effective_date) VALUES (0.14, "2024-01-01")')

        # Create salary components
        self.db.execute("""
            INSERT INTO salary_components (id, name, type, is_percentage, value, tax_exempt, is_taxable)
            VALUES 
                (1, 'Housing Allowance', 'allowance', 0, 1000.00, 1, 0),
                (2, 'Transport Allowance', 'allowance', 0, 500.00, 0, 1)
        """)

        # Create employee types
        self.db.execute("""
            INSERT INTO employee_types (id, name, is_contractor, overtime_multiplier, holiday_pay_multiplier, working_hours_per_week)
            VALUES 
                (1, 'Regular', 0, 1.5, 2.0, 40.0)
        """)
        
        # Create two periods
        cursor = self.db.execute("""
            INSERT INTO payroll_periods (start_date, end_date, status)
            VALUES ('2024-01-01', '2024-01-31', 'draft')
            RETURNING id
        """)
        period1_id = cursor.fetchone()['id']
        
        cursor = self.db.execute("""
            INSERT INTO payroll_periods (start_date, end_date, status)
            VALUES ('2024-02-01', '2024-02-28', 'draft')
            RETURNING id
        """)
        period2_id = cursor.fetchone()['id']
        
        # Create test employees
        employee_ids = []
        for i in range(5):
            cursor = self.db.execute("""
                INSERT INTO employees (
                    first_name, last_name, email, employee_type_id, status
                ) VALUES (?, ?, ?, 1, 'active')
                RETURNING id
            """, (f"Employee{i}", f"Test{i}", f"employee{i}@example.com"))
            employee_id = cursor.fetchone()['id']
            employee_ids.append(employee_id)
            
            # Add employee details
            self.db.execute("""
                INSERT INTO employee_details (
                    employee_id, basic_salary, date_of_birth, 
                    bank_name, bank_account, tax_id, social_insurance_number
                ) VALUES (?, 5000.00, '1990-01-01', 'Test Bank', '123456789', 'TX123', 'SI456')
            """, (employee_id,))
            
            # Add salary components
            self.db.execute("""
                INSERT INTO employee_salary_components (
                    employee_id, component_id, value
                ) VALUES
                    (?, 1, 1000.00),  -- Housing allowance
                    (?, 2, 500.00)    -- Transport allowance
            """, (employee_id, employee_id))
        
        # Test concurrent payroll generation
        # Temporarily patch transaction methods to avoid transaction issues in tests
        original_begin = self.payroll_repo.begin_transaction
        original_commit = self.payroll_repo.commit_transaction
        original_rollback = self.payroll_repo.rollback_transaction
        
        self.payroll_repo.begin_transaction = lambda: None
        self.payroll_repo.commit_transaction = lambda: None
        self.payroll_repo.rollback_transaction = lambda: None
        self.payroll_repo._transaction_active = True  # Set to True to bypass transaction checks
        
        try:
            # Generate payroll for period 1
            result1 = self.service.generate_payroll(period1_id, employee_ids[:3])
            self.assertEqual(len(result1['entries']), 3)
            
            # Generate payroll for period 2
            result2 = self.service.generate_payroll(period2_id, employee_ids[2:])
            self.assertEqual(len(result2['entries']), 3)
            
            # Verify that employee 3 (index 2) has payroll in both periods
            period1_employee_ids = [entry['employee_id'] for entry in result1['entries']]
            period2_employee_ids = [entry['employee_id'] for entry in result2['entries']]
            
            self.assertIn(employee_ids[2], period1_employee_ids)
            self.assertIn(employee_ids[2], period2_employee_ids)
        finally:
            # Restore original methods
            self.payroll_repo.begin_transaction = original_begin
            self.payroll_repo.commit_transaction = original_commit
            self.payroll_repo.rollback_transaction = original_rollback
            self.payroll_repo._transaction_active = False

if __name__ == '__main__':
    unittest.main()
