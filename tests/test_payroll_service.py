"""Unit tests for payroll service"""
import unittest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from services.payroll_service import PayrollService
from utils.exceptions import (
    PayrollValidationError, PayrollCalculationError,
    SalaryComponentError, DatabaseOperationError
)

class TestPayrollService(unittest.TestCase):
    """Test cases for PayrollService"""

    def setUp(self):
        """Set up test environment before each test"""
        self.employee_repo = Mock()
        self.payroll_repo = Mock()
        
        # Create the service with mocked repositories
        self.service = PayrollService(self.employee_repo, self.payroll_repo)
        
        # Create a separate mock for the calculate_employee_payroll method
        self.original_calculate_employee_payroll = self.service.calculate_employee_payroll
        
    def tearDown(self):
        """Clean up after each test"""
        # Restore original method
        if hasattr(self, 'original_calculate_employee_payroll'):
            self.service.calculate_employee_payroll = self.original_calculate_employee_payroll

    def test_validate_payroll_period_success(self):
        """Test successful payroll period validation"""
        # Arrange
        period_id = 1
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        self.payroll_repo.get_by_id.return_value = period

        # Act
        success, result = self.service.validate_payroll_period(period_id)

        # Assert
        self.assertTrue(success)
        self.assertEqual(result, period)
        self.payroll_repo.get_by_id.assert_called_once_with('payroll_periods', period_id)

    def test_validate_payroll_period_invalid_status(self):
        """Test payroll period validation with invalid status"""
        # Arrange
        period_id = 1
        period = {
            'id': period_id,
            'status': 'closed',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        self.payroll_repo.get_by_id.return_value = period

        # Mock the validate_payroll_period method to raise an exception
        self.payroll_repo.validate_payroll_period.side_effect = PayrollValidationError(
            "Cannot generate payroll for period in closed status"
        )

        # Act & Assert
        with self.assertRaises(PayrollValidationError):
            self.service.validate_payroll_period(period_id)

    def test_calculate_employee_payroll_full_time(self):
        """Test payroll calculation for full-time employee"""
        # Arrange
        employee_id = 1
        period_id = 1
        employee = {
            'id': employee_id,
            'employee_type': 'Full Time',
            'basic_salary': '5000.00'
        }
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        salary_result = {
            'basic_salary': Decimal('5000.00'),
            'total_allowances': Decimal('1000.00'),
            'tax_exempt_allowances': Decimal('500.00'),
            'total_deductions': Decimal('800.00'),
            'overtime_pay': Decimal('200.00'),
            'holiday_premium': Decimal('300.00'),
            'leave_deductions': Decimal('0.00'),
            'tax': Decimal('500.00'),
            'net_salary': Decimal('5200.00')
        }

        self.employee_repo.get_employee_details.return_value = employee
        self.payroll_repo.get_by_id.return_value = period
        self.payroll_repo.calculate_net_salary.return_value = salary_result

        # Act
        result = self.service.calculate_employee_payroll(employee_id, period_id)

        # Assert
        self.assertEqual(result, salary_result)
        self.employee_repo.get_employee_details.assert_called_once_with(employee_id)
        self.payroll_repo.calculate_net_salary.assert_called_once()

    def test_calculate_employee_payroll_part_time(self):
        """Test payroll calculation for part-time employee"""
        # Arrange
        employee_id = 1
        period_id = 1
        employee = {
            'id': employee_id,
            'employee_type': 'Part Time',
            'basic_salary': '5000.00',
            'working_hours': '20'
        }
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        salary_result = {
            'basic_salary': Decimal('2500.00'),  # Prorated for 20 hours
            'total_allowances': Decimal('500.00'),
            'tax_exempt_allowances': Decimal('250.00'),
            'total_deductions': Decimal('400.00'),
            'overtime_pay': Decimal('100.00'),
            'holiday_premium': Decimal('150.00'),
            'leave_deductions': Decimal('0.00'),
            'tax': Decimal('250.00'),
            'net_salary': Decimal('2600.00')
        }

        self.employee_repo.get_employee_details.return_value = employee
        self.payroll_repo.get_by_id.return_value = period
        self.payroll_repo.calculate_net_salary.return_value = salary_result

        # Act
        result = self.service.calculate_employee_payroll(employee_id, period_id)

        # Assert
        self.assertEqual(result, salary_result)
        self.employee_repo.get_employee_details.assert_called_once_with(employee_id)
        self.payroll_repo.calculate_net_salary.assert_called_once()

    def test_calculate_employee_payroll_contractor(self):
        """Test payroll calculation for contractor"""
        # Arrange
        employee_id = 1
        period_id = 1
        employee = {
            'id': employee_id,
            'employee_type': 'Contractor',
            'basic_salary': '5000.00'
        }
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        salary_result = {
            'basic_salary': Decimal('5000.00'),
            'total_allowances': Decimal('0.00'),
            'tax_exempt_allowances': Decimal('0.00'),
            'total_deductions': Decimal('0.00'),
            'overtime_pay': Decimal('0.00'),
            'holiday_premium': Decimal('0.00'),
            'leave_deductions': Decimal('0.00'),
            'tax': Decimal('0.00'),
            'net_salary': Decimal('5000.00')
        }

        self.employee_repo.get_employee_details.return_value = employee
        self.payroll_repo.get_by_id.return_value = period
        self.payroll_repo.calculate_contractor_salary.return_value = salary_result
    
        # Act
        result = self.service.calculate_employee_payroll(employee_id, period_id)

        # Assert
        self.assertEqual(result, salary_result)
        self.employee_repo.get_employee_details.assert_called_once_with(employee_id)
        self.payroll_repo.calculate_contractor_salary.assert_called_once()

    def test_generate_payroll_success(self):
        """Test successful payroll generation for multiple employees"""
        # Arrange
        period_id = 1
        employee_ids = [1, 2]
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        employees = [
            {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_type': 'Full Time',
                'basic_salary': '5000.00'
            },
            {
                'id': 2,
                'first_name': 'Jane',
                'last_name': 'Smith',
                'employee_type': 'Part Time',
                'basic_salary': '3000.00',
                'working_hours': '20'
            }
        ]
        
        # Mock the payroll repo
        self.payroll_repo.get_by_id.return_value = period
        self.employee_repo.get_active_employees.return_value = employees
        
        # Mock the calculate_employee_payroll method
        salary_results = [
            {
                'basic_salary': Decimal('5000.00'),
                'net_salary': Decimal('5200.00')
            },
            {
                'basic_salary': Decimal('1500.00'),
                'net_salary': Decimal('1600.00')
            }
        ]
        
        # Create a patched version of calculate_employee_payroll
        with patch.object(self.service, 'calculate_employee_payroll', side_effect=salary_results):
            # Act
            result = self.service.generate_payroll(period_id, employee_ids)
            
            # Assert
            self.assertEqual(len(result['entries']), 2)
            self.assertEqual(result['period_id'], period_id)
            self.assertEqual(len(result['errors']), 0)
            self.payroll_repo.update_payroll_period_status.assert_called_once()

    def test_generate_payroll_partial_failure(self):
        """Test payroll generation with some failures"""
        # Arrange
        period_id = 1
        employee_ids = [1, 2, 3]
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        employees = [
            {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_type': 'Full Time',
                'basic_salary': '5000.00'
            },
            {
                'id': 2,
                'first_name': 'Jane',
                'last_name': 'Smith',
                'employee_type': 'Part Time',
                'basic_salary': '3000.00'
            },
            {
                'id': 3,
                'first_name': 'Bob',
                'last_name': 'Brown',
                'employee_type': 'Full Time',
                'basic_salary': '4000.00'
            }
        ]

        self.payroll_repo.get_by_id.return_value = period
        self.employee_repo.get_active_employees.return_value = employees
        
        # Create side effects with a mix of successful results and errors
        side_effects = [
            {'basic_salary': Decimal('5000.00'), 'net_salary': Decimal('5200.00')},
            PayrollCalculationError("Error calculating salary"),
            {'basic_salary': Decimal('4000.00'), 'net_salary': Decimal('4200.00')}
        ]
        
        # Create a patched version of calculate_employee_payroll
        with patch.object(self.service, 'calculate_employee_payroll', side_effect=side_effects):
            # Act
            result = self.service.generate_payroll(period_id, employee_ids)
            
            # Assert
            self.assertEqual(len(result['entries']), 2)
            self.assertEqual(len(result['errors']), 1)
            self.assertEqual(result['errors'][0]['employee_id'], 2)
            self.payroll_repo.update_payroll_period_status.assert_called_once()

    def test_generate_payroll_all_failures(self):
        """Test payroll generation when all calculations fail"""
        # Arrange
        period_id = 1
        employee_ids = [1, 2]
        period = {
            'id': period_id,
            'status': 'draft',
            'start_date': date(2025, 1, 1),
            'end_date': date(2025, 1, 31)
        }
        employees = [
            {
                'id': 1,
                'first_name': 'John',
                'last_name': 'Doe',
                'employee_type': 'Full Time',
                'basic_salary': '5000.00'
            },
            {
                'id': 2,
                'first_name': 'Jane',
                'last_name': 'Smith',
                'employee_type': 'Part Time',
                'basic_salary': '3000.00'
            }
        ]
    
        self.payroll_repo.get_by_id.return_value = period
        self.employee_repo.get_active_employees.return_value = employees
        
        # Create side effects with all errors
        side_effects = [
            PayrollCalculationError("Error 1"),
            PayrollCalculationError("Error 2")
        ]
        
        # Create a patched version of calculate_employee_payroll
        with patch.object(self.service, 'calculate_employee_payroll', side_effect=side_effects):
            # Act & Assert
            with self.assertRaises(PayrollCalculationError) as context:
                self.service.generate_payroll(period_id, employee_ids)
            
            self.assertIn("All payroll calculations failed", str(context.exception))
            self.payroll_repo.rollback_transaction.assert_called_once()


if __name__ == '__main__':
    unittest.main()
