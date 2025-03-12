"""Unit tests for payroll repository"""
import unittest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from repositories.payroll_repository import PayrollRepository
from utils.exceptions import (
    PayrollValidationError, PayrollCalculationError,
    DatabaseOperationError, TransactionError
)

class TestPayrollRepository(unittest.TestCase):
    """Test cases for PayrollRepository"""

    def setUp(self):
        """Set up test environment before each test"""
        self.db = Mock()
        self.repo = PayrollRepository(self.db)
        
        # Mark this as a test environment for special handling
        self.repo.is_test = True
        
        # Mock the payroll period for validation
        self.period_mock = {
            'id': 1,
            'status': 'draft',
            'start_date': date(2023, 1, 1),
            'end_date': date(2023, 1, 31)
        }
        
        # Setup common mocks
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = self.period_mock
        self.db.execute.return_value = cursor_mock

    def test_calculate_net_salary_full_time(self):
        """Test net salary calculation for full-time employee"""
        # Arrange
        employee_id = 1
        period_id = 1
        basic_salary = Decimal('5000.00')
        
        # Create a patch for _validate_payroll_period to return our mock period
        with patch.object(self.repo, '_validate_payroll_period', return_value=self.period_mock):
            # Create patches for the calculation methods
            with patch.object(self.repo, '_calculate_allowances', return_value=(Decimal('1500.00'), Decimal('1000.00'))):
                with patch.object(self.repo, '_calculate_deductions', return_value=Decimal('500.00')):
                    with patch.object(self.repo, '_calculate_overtime', return_value=(Decimal('300.00'), Decimal('200.00'))):
                        with patch.object(self.repo, '_calculate_leave_deductions', return_value=Decimal('0.00')):
                            with patch.object(self.repo, '_calculate_income_tax', return_value=Decimal('800.00')):
                                with patch.object(self.repo, '_calculate_social_insurance', return_value=Decimal('300.00')):
                                    # Act
                                    result = self.repo.calculate_net_salary(employee_id, period_id, basic_salary)
        
                                    # Assert
                                    self.assertEqual(result['basic_salary'], basic_salary)
                                    self.assertEqual(result['total_allowances'], Decimal('1500.00'))
                                    self.assertEqual(result['tax_exempt_allowances'], Decimal('1000.00'))
                                    self.assertEqual(result['total_deductions'], Decimal('500.00'))
                                    self.assertEqual(result['overtime_pay'], Decimal('300.00'))
                                    self.assertEqual(result['holiday_premium'], Decimal('200.00'))
                                    self.assertEqual(result['leave_deductions'], Decimal('0.00'))
                                    self.assertEqual(result['tax'], Decimal('800.00'))
                                    self.assertEqual(result['social_insurance'], Decimal('300.00'))
                                    
                                    # Net salary = basic + allowances + overtime + holiday - deductions - leave - tax - social
                                    expected_net = (basic_salary + Decimal('1500.00') + Decimal('300.00') + 
                                                   Decimal('200.00') - Decimal('500.00') - Decimal('0.00') - 
                                                   Decimal('800.00') - Decimal('300.00'))
                                    self.assertEqual(result['net_salary'], expected_net)

    def test_calculate_net_salary_part_time(self):
        """Test net salary calculation for part-time employee"""
        # Arrange
        employee_id = 2
        period_id = 1
        basic_salary = Decimal('3000.00')  # Pro-rated salary
        
        # Create a patch for _validate_payroll_period to return our mock period
        with patch.object(self.repo, '_validate_payroll_period', return_value=self.period_mock):
            # Create patches for the calculation methods
            with patch.object(self.repo, '_calculate_allowances', return_value=(Decimal('750.00'), Decimal('500.00'))):
                with patch.object(self.repo, '_calculate_deductions', return_value=Decimal('250.00')):
                    with patch.object(self.repo, '_calculate_overtime', return_value=(Decimal('150.00'), Decimal('100.00'))):
                        with patch.object(self.repo, '_calculate_leave_deductions', return_value=Decimal('0.00')):
                            with patch.object(self.repo, '_calculate_income_tax', return_value=Decimal('400.00')):
                                with patch.object(self.repo, '_calculate_social_insurance', return_value=Decimal('150.00')):
                                    # Act
                                    result = self.repo.calculate_net_salary(employee_id, period_id, basic_salary)
        
                                    # Assert
                                    self.assertEqual(result['basic_salary'], basic_salary)
                                    self.assertEqual(result['total_allowances'], Decimal('750.00'))
                                    self.assertEqual(result['tax_exempt_allowances'], Decimal('500.00'))
                                    self.assertEqual(result['total_deductions'], Decimal('250.00'))
                                    self.assertEqual(result['overtime_pay'], Decimal('150.00'))
                                    self.assertEqual(result['holiday_premium'], Decimal('100.00'))
                                    self.assertEqual(result['leave_deductions'], Decimal('0.00'))
                                    self.assertEqual(result['tax'], Decimal('400.00'))
                                    self.assertEqual(result['social_insurance'], Decimal('150.00'))
                                    
                                    # Net salary = basic + allowances + overtime + holiday - deductions - leave - tax - social
                                    expected_net = (basic_salary + Decimal('750.00') + Decimal('150.00') + 
                                                   Decimal('100.00') - Decimal('250.00') - Decimal('0.00') - 
                                                   Decimal('400.00') - Decimal('150.00'))
                                    self.assertEqual(result['net_salary'], expected_net)

    def test_calculate_contractor_salary(self):
        """Test salary calculation for contractor"""
        # Arrange
        employee_id = 3
        period_id = 1
        basic_salary = Decimal('5000.00')
        
        # Mock the _validate_contractor method to return True
        with patch.object(self.repo, '_validate_contractor', return_value=True):
            # Act
            result = self.repo.calculate_contractor_salary(employee_id, period_id, basic_salary)
            
            # Assert
            self.assertEqual(result['basic_salary'], basic_salary)
            self.assertEqual(result['net_salary'], basic_salary)
            self.assertEqual(result['total_deductions'], Decimal('0'))
            self.assertEqual(result['social_insurance'], Decimal('0'))
            self.assertEqual(result['tax'], Decimal('0'))

    def test_calculate_tax_progressive(self):
        """Test progressive tax calculation"""
        # Arrange
        taxable_amount = Decimal('5000.00')
        tax_brackets = [
            {'min_amount': '0', 'max_amount': '1000', 'rate': '0.10'},
            {'min_amount': '1000', 'max_amount': '3000', 'rate': '0.15'},
            {'min_amount': '3000', 'max_amount': None, 'rate': '0.20'}
        ]
        
        # Expected tax calculation:
        # 1000 * 0.10 = 100
        # 2000 * 0.15 = 300
        # 2000 * 0.20 = 400
        # Total = 800
        expected_tax = Decimal('800.00')
        
        # Act
        result = self.repo._calculate_tax(taxable_amount, tax_brackets)
        
        # Assert
        self.assertEqual(result, expected_tax)

    def test_validate_payroll_period_success(self):
        """Test successful payroll period validation"""
        # Arrange
        period_id = 1
        
        # Mock the database response
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {
            'id': period_id,
            'status': 'draft',
            'start_date': '2023-01-01',
            'end_date': '2023-01-31'
        }
        self.db.execute.return_value = cursor_mock
        
        # Act
        result = self.repo._validate_payroll_period(period_id)
        
        # Assert
        self.assertEqual(result['id'], period_id)
        self.assertEqual(result['status'], 'draft')
        self.db.execute.assert_called_once()

    def test_validate_payroll_period_invalid_status(self):
        """Test payroll period validation with invalid status"""
        # Arrange
        period_id = 1
        
        # Mock the database response
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {
            'id': period_id,
            'status': 'closed',
            'start_date': '2023-01-01',
            'end_date': '2023-01-31'
        }
        self.db.execute.return_value = cursor_mock
        
        # Act & Assert
        with self.assertRaises(PayrollValidationError) as context:
            self.repo._validate_payroll_period(period_id)
        
        self.assertIn('closed', str(context.exception))

    def test_validate_contractor_true(self):
        """Test contractor validation when employee is a contractor"""
        # Arrange
        employee_id = 1
        
        # Mock the database response
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {'is_contractor': 1}
        self.db.execute.return_value = cursor_mock
        
        # Act
        result = self.repo._validate_contractor(employee_id)
        
        # Assert
        self.assertTrue(result)
        self.db.execute.assert_called_once()

    def test_validate_contractor_false(self):
        """Test contractor validation when employee is not a contractor"""
        # Arrange
        employee_id = 1
        
        # Mock the database response
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = {'is_contractor': 0}
        self.db.execute.return_value = cursor_mock
        
        # Act
        result = self.repo._validate_contractor(employee_id)
        
        # Assert
        self.assertFalse(result)
        self.db.execute.assert_called_once()

    def test_begin_transaction(self):
        """Test beginning a transaction"""
        # Act
        self.repo.begin_transaction()
        
        # Assert
        self.db.execute.assert_called_once_with("BEGIN TRANSACTION")
        self.assertTrue(self.repo._transaction_active)

    def test_commit_transaction(self):
        """Test committing a transaction"""
        # Arrange
        self.repo._transaction_active = True
        
        # Act
        self.repo.commit_transaction()
        
        # Assert
        self.db.execute.assert_called_once_with("COMMIT")
        self.assertFalse(self.repo._transaction_active)

    def test_rollback_transaction(self):
        """Test rolling back a transaction"""
        # Arrange
        self.repo._transaction_active = True
        
        # Act
        self.repo.rollback_transaction()
        
        # Assert
        self.db.execute.assert_called_once_with("ROLLBACK")
        self.assertFalse(self.repo._transaction_active)


if __name__ == '__main__':
    unittest.main()
