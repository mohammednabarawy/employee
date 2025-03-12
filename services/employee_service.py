from typing import Dict, Any, Tuple, Optional
import logging
from decimal import Decimal
from datetime import datetime

from repositories.employee_repository import EmployeeRepository
from repositories.base_repository import BaseRepository
from exceptions import (
    EmployeeCreationError, 
    ValidationError, 
    PayrollCalculationError
)

class EmployeeService:
    """Service layer for employee-related business logic"""
    
    def __init__(
        self, 
        employee_repo: EmployeeRepository, 
        base_repo: BaseRepository
    ):
        """
        Initialize the employee service with repositories
        
        Args:
            employee_repo (EmployeeRepository): Repository for employee operations
            base_repo (BaseRepository): Base repository for common database operations
        """
        self.employee_repo = employee_repo
        self.base_repo = base_repo
        self.logger = logging.getLogger(__name__)
    
    def create_employee(
        self, 
        employee_data: Dict[str, Any], 
        created_by: int
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Create a new employee with comprehensive validation
        
        Args:
            employee_data (Dict[str, Any]): Employee information
            created_by (int): ID of the user creating the employee
        
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Success status and employee data
        """
        try:
            # Validate required fields
            required_fields = ['name', 'hire_date', 'department_id']
            for field in required_fields:
                if not employee_data.get(field):
                    raise ValidationError(f"الحقل {field} مطلوب")
            
            # Ensure department exists
            if not self.base_repo.exists('departments', {'id': employee_data['department_id']}):
                # If no department exists, create a default department
                default_dept_id = self._create_default_department()
                employee_data['department_id'] = default_dept_id
            
            # Generate unique employee code
            employee_data['code'] = self._generate_employee_code()
            
            # Set default values
            employee_data.setdefault('is_active', 1)
            employee_data.setdefault('created_at', datetime.now())
            
            # Begin transaction
            self.employee_repo.begin_transaction()
            
            # Create employee record
            employee_id = self.employee_repo.create_employee(
                employee_data, 
                {
                    'department_id': employee_data['department_id'],
                    'hire_date': employee_data['hire_date'],
                    'basic_salary': employee_data.get('basic_salary', 0)
                }, 
                created_by
            )
            
            # Commit transaction
            self.employee_repo.commit_transaction()
            
            # Retrieve and return the created employee
            employee = self.employee_repo.get_employee_with_details(employee_id)
            
            return True, employee
        
        except (ValidationError, EmployeeCreationError) as e:
            self.logger.error(f"Employee creation failed: {str(e)}")
            
            # Rollback transaction if active
            try:
                self.employee_repo.rollback_transaction()
            except Exception:
                pass
            
            return False, str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error in employee creation: {str(e)}")
            
            # Rollback transaction if active
            try:
                self.employee_repo.rollback_transaction()
            except Exception:
                pass
            
            return False, "حدث خطأ غير متوقع أثناء إنشاء الموظف"
    
    def _generate_employee_code(self) -> str:
        """
        Generate a unique employee code
        
        Returns:
            str: Unique employee code
        """
        try:
            # Get the last employee code and increment
            cursor = self.base_repo.db.cursor()
            cursor.execute("SELECT MAX(CAST(SUBSTR(code, 4) AS INTEGER)) as last_number FROM employees")
            last_number = cursor.fetchone()[0] or 0
            
            return f"EMP{last_number + 1:04d}"
        except Exception as e:
            self.logger.error(f"Error generating employee code: {str(e)}")
            raise EmployeeCreationError("فشل إنشاء كود الموظف")
    
    def _create_default_department(self) -> int:
        """
        Create a default department if no departments exist
        
        Returns:
            int: ID of the created default department
        """
        try:
            default_dept_data = {
                'name': 'General Department',
                'name_ar': 'القسم العام',
                'description': 'Default department for new employees',
                'is_active': 1
            }
            
            return self.base_repo.create('departments', default_dept_data, 1)
        except Exception as e:
            self.logger.error(f"Error creating default department: {str(e)}")
            raise EmployeeCreationError("فشل إنشاء القسم الافتراضي")
    
    def calculate_salary(self, employee_id: int, period: datetime) -> Dict[str, Decimal]:
        """
        Calculate salary for an employee considering various factors
        
        Args:
            employee_id (int): ID of the employee
            period (datetime): Salary calculation period
        
        Returns:
            Dict[str, Decimal]: Detailed salary breakdown
        """
        try:
            # Retrieve employee details
            employee = self.employee_repo.get_employee_with_details(employee_id)
            
            if not employee:
                raise ValidationError("الموظف غير موجود")
            
            # Base salary calculation
            base_salary = Decimal(str(employee['basic_salary']))
            
            # Allowances calculation
            allowances = self._calculate_allowances(employee_id, period)
            
            # Overtime calculation
            overtime_pay = self._calculate_overtime(employee, period)
            
            # Tax calculation
            taxable_income = base_salary + allowances.get('total_allowances', Decimal('0'))
            tax = self._calculate_tax(taxable_income)
            
            # Deductions calculation
            deductions = self._calculate_deductions(employee_id, period)
            
            # Net salary calculation
            net_salary = (
                base_salary + 
                allowances.get('total_allowances', Decimal('0')) + 
                overtime_pay - 
                tax - 
                deductions.get('total_deductions', Decimal('0'))
            )
            
            return {
                'base_salary': base_salary,
                'allowances': allowances,
                'overtime_pay': overtime_pay,
                'tax': tax,
                'deductions': deductions,
                'net_salary': net_salary
            }
        
        except Exception as e:
            self.logger.error(f"Salary calculation error: {str(e)}")
            raise PayrollCalculationError(f"فشل حساب الراتب: {str(e)}")
    
    def _calculate_allowances(self, employee_id: int, period: datetime) -> Dict[str, Decimal]:
        """
        Calculate employee allowances
        
        Args:
            employee_id (int): ID of the employee
            period (datetime): Calculation period
        
        Returns:
            Dict[str, Decimal]: Allowances breakdown
        """
        # Placeholder for allowances calculation logic
        # This would involve querying employee_salary_components and applying rules
        return {
            'housing_allowance': Decimal('0'),
            'transportation_allowance': Decimal('0'),
            'total_allowances': Decimal('0')
        }
    
    def _calculate_overtime(self, employee: Dict[str, Any], period: datetime) -> Decimal:
        """
        Calculate overtime pay
        
        Args:
            employee (Dict[str, Any]): Employee details
            period (datetime): Calculation period
        
        Returns:
            Decimal: Overtime pay amount
        """
        # Placeholder for overtime calculation logic
        return Decimal('0')
    
    def _calculate_tax(self, taxable_income: Decimal) -> Decimal:
        """
        Calculate progressive tax
        
        Args:
            taxable_income (Decimal): Taxable income amount
        
        Returns:
            Decimal: Tax amount
        """
        # Placeholder for tax calculation logic
        return Decimal('0')
    
    def _calculate_deductions(self, employee_id: int, period: datetime) -> Dict[str, Decimal]:
        """
        Calculate employee deductions
        
        Args:
            employee_id (int): ID of the employee
            period (datetime): Calculation period
        
        Returns:
            Dict[str, Decimal]: Deductions breakdown
        """
        # Placeholder for deductions calculation logic
        return {
            'social_insurance': Decimal('0'),
            'total_deductions': Decimal('0')
        }
