from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date
from .base_repository import BaseRepository, ValidationError
from utils.exceptions import PayrollValidationError, PayrollCalculationError, TransactionError, DatabaseOperationError
import logging

class EmployeeRepository(BaseRepository):
    """Repository for employee-related database operations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
        self._transaction_active = False
    
    def begin_transaction(self):
        """Begin a new database transaction"""
        try:
            if self._transaction_active:
                raise TransactionError("Transaction already in progress")
            
            self.db.execute("BEGIN TRANSACTION")
            self._transaction_active = True
            
        except Exception as e:
            self.logger.error(f"Error starting transaction: {str(e)}")
            raise TransactionError(f"Failed to start transaction: {str(e)}")
    
    def commit_transaction(self):
        """Commit the current transaction"""
        try:
            if not self._transaction_active:
                raise TransactionError("No active transaction to commit")
            
            self.db.execute("COMMIT")
            self._transaction_active = False
            
        except Exception as e:
            self.logger.error(f"Error committing transaction: {str(e)}")
            raise TransactionError(f"Failed to commit transaction: {str(e)}")
    
    def rollback_transaction(self):
        """Rollback the current transaction"""
        try:
            if not self._transaction_active:
                raise TransactionError("No active transaction to rollback")
            
            self.db.execute("ROLLBACK")
            self._transaction_active = False
            
        except Exception as e:
            self.logger.error(f"Error rolling back transaction: {str(e)}")
            raise TransactionError(f"Failed to rollback transaction: {str(e)}")
    
    def get_employee_with_details(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee data with type and salary details"""
        try:
            query = """
                SELECT 
                    e.*,
                    et.name as employee_type,
                    et.working_hours_per_week,
                    et.overtime_multiplier,
                    et.holiday_pay_multiplier,
                    et.prorated_benefits,
                    ed.basic_salary,
                    ed.bank_name,
                    ed.bank_account,
                    ed.tax_id,
                    ed.social_insurance_number
                FROM employees e
                JOIN employee_types et ON e.employee_type_id = et.id
                JOIN employee_details ed ON e.id = ed.employee_id
                WHERE e.id = ?
            """
            
            result = self.execute_query(query, (employee_id,), fetch=True)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error fetching employee details: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to fetch employee details",
                operation="select",
                details={'employee_id': employee_id}
            )
    
    def get_active_employees(self) -> List[Dict[str, Any]]:
        """Get all active employees with their types"""
        try:
            query = """
                SELECT 
                    e.*,
                    et.name as employee_type,
                    et.working_hours_per_week
                FROM employees e
                JOIN employee_types et ON e.employee_type_id = et.id
                WHERE e.status = 'active'
            """
            
            return self.execute_query(query, fetch=True)
            
        except Exception as e:
            self.logger.error(f"Error fetching active employees: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to fetch active employees",
                operation="select"
            )
    
    def get_employee_details(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee details including type information"""
        try:
            query = """
                SELECT 
                    e.*,
                    ed.*,
                    et.name as employee_type,
                    et.is_contractor,
                    et.overtime_multiplier,
                    et.holiday_pay_multiplier,
                    et.working_hours_per_week
                FROM employees e
                JOIN employee_types et ON e.employee_type_id = et.id
                JOIN employee_details ed ON e.id = ed.employee_id
                WHERE e.id = ?
            """
            
            result = self.execute_query(query, (employee_id,), fetch=True)
            return result[0] if result else None
            
        except Exception as e:
            self.logger.error(f"Error fetching employee details: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to fetch employee details",
                operation="select",
                details={'employee_id': employee_id}
            )
    
    def create_employee(
            self,
            employee_data: Dict[str, Any],
            details_data: Dict[str, Any],
            created_by: int
        ) -> int:
        """Create a new employee with details"""
        try:
            if not self._transaction_active:
                raise TransactionError(
                    "Employee creation must be part of a transaction"
                )
            
            # Validate employee type
            if not self.exists('employee_types', {'id': employee_data['employee_type_id']}):
                raise ValidationError("Invalid employee type")
            
            # Validate salary
            if Decimal(str(details_data['basic_salary'])) < 0:
                raise ValidationError("Basic salary cannot be negative")
            
            with self.transaction():
                # Create employee
                employee_id = self.create('employees', employee_data, created_by)
                
                # Create employee details
                details_data['employee_id'] = employee_id
                self.create('employee_details', details_data, created_by)
                
                return employee_id
                
        except (EmployeeValidationError, TransactionError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating employee: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to create employee: {str(e)}",
                operation="insert"
            )
    
    def update_employee(
            self,
            employee_id: int,
            employee_data: Dict[str, Any],
            details_data: Dict[str, Any],
            updated_by: int
        ) -> bool:
        """Update employee and details"""
        try:
            if not self._transaction_active:
                raise TransactionError(
                    "Employee update must be part of a transaction"
                )
            
            if 'employee_type_id' in employee_data:
                if not self.exists('employee_types', {'id': employee_data['employee_type_id']}):
                    raise ValidationError("Invalid employee type")
            
            if 'basic_salary' in details_data:
                if Decimal(str(details_data['basic_salary'])) < 0:
                    raise ValidationError("Basic salary cannot be negative")
            
            with self.transaction():
                # Update employee
                if employee_data:
                    self.update('employees', employee_id, employee_data, updated_by)
                
                # Update employee details
                if details_data:
                    details_id = self.execute_query(
                        "SELECT id FROM employee_details WHERE employee_id = ?",
                        (employee_id,),
                        fetch=True
                    )[0]['id']
                    self.update('employee_details', details_id, details_data, updated_by)
                
                return True
                
        except (EmployeeValidationError, TransactionError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating employee: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to update employee: {str(e)}",
                operation="update",
                details={'employee_id': employee_id}
            )
    
    def get_employee_attendance(
            self,
            employee_id: int,
            start_date: date,
            end_date: date
        ) -> Dict[str, Any]:
        """Get employee attendance summary for a period"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_days,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days,
                    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_days,
                    SUM(CASE WHEN status = 'late' THEN 1 ELSE 0 END) as late_days,
                    SUM(CASE WHEN status = 'half-day' THEN 0.5 ELSE 0 END) as half_days,
                    SUM(CASE WHEN status = 'leave' THEN 1 ELSE 0 END) as leave_days,
                    SUM(total_hours) as total_hours
                FROM attendance_records
                WHERE employee_id = ?
                AND date BETWEEN ? AND ?
            """
            
            result = self.execute_query(
                query,
                (employee_id, start_date, end_date),
                fetch=True
            )
            
            return result[0] if result else {
                'total_days': 0,
                'present_days': 0,
                'absent_days': 0,
                'late_days': 0,
                'half_days': 0,
                'leave_days': 0,
                'total_hours': 0
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching employee attendance: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to fetch employee attendance",
                operation="select",
                details={'employee_id': employee_id}
            )
    
    def get_employee_leave_balance(
            self,
            employee_id: int,
            year: int
        ) -> List[Dict[str, Any]]:
        """Get employee leave balances for the year"""
        try:
            query = """
                SELECT 
                    lt.name,
                    lt.paid,
                    lb.total_days,
                    lb.used_days,
                    lb.remaining_days
                FROM leave_balances lb
                JOIN leave_types lt ON lb.leave_type_id = lt.id
                WHERE lb.employee_id = ?
                AND lb.year = ?
            """
            
            return self.execute_query(query, (employee_id, year), fetch=True)
            
        except Exception as e:
            self.logger.error(f"Error fetching employee leave balance: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to fetch employee leave balance",
                operation="select",
                details={'employee_id': employee_id}
            )
    
    def record_attendance(
            self,
            employee_id: int,
            date: date,
            status: str,
            check_in: Optional[datetime] = None,
            check_out: Optional[datetime] = None,
            total_hours: Optional[Decimal] = None,
            notes: Optional[str] = None,
            created_by: int = None
        ) -> int:
        """Record employee attendance"""
        try:
            if not self._transaction_active:
                raise TransactionError(
                    "Attendance record must be part of a transaction"
                )
            
            if status not in ['present', 'absent', 'late', 'half-day', 'leave']:
                raise ValidationError("Invalid attendance status")
            
            data = {
                'employee_id': employee_id,
                'date': date,
                'status': status,
                'check_in': check_in,
                'check_out': check_out,
                'total_hours': total_hours,
                'notes': notes
            }
            
            return self.create('attendance_records', data, created_by)
            
        except (EmployeeValidationError, TransactionError):
            raise
        except Exception as e:
            self.logger.error(f"Error recording attendance: {str(e)}")
            raise DatabaseOperationError(
                f"Failed to record attendance: {str(e)}",
                operation="insert"
            )

    def execute_query(self, query, params=None, fetch=False):
        """Execute a database query and optionally fetch results"""
        try:
            cursor = self.db.execute(query, params or ())
            
            if fetch:
                return cursor.fetchall()
            return cursor
            
        except Exception as e:
            self.logger.error(f"Database query error: {str(e)}")
            raise DatabaseOperationError(
                f"Database operation failed: {str(e)}",
                operation="query"
            )
