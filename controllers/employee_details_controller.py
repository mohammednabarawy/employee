from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class SalaryAdjustment:
    id: int
    employee_id: int
    adjustment_type: str  # 'increase', 'decrease', 'one_time'
    amount: Decimal
    percentage: Optional[float]
    reason: str
    effective_date: date
    end_date: Optional[date]
    status: str  # 'pending', 'approved', 'rejected'
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    created_at: datetime
    created_by: int

class EmployeeDetailsController:
    def __init__(self, db):
        self.db = db

    def get_employee_details(self, employee_id: int) -> Tuple[bool, Union[Dict, str]]:
        """Get comprehensive employee details including salary information"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get basic employee info and current salary details
            cursor.execute("""
                SELECT 
                    e.id, e.code, e.name, e.name_ar, e.basic_salary,
                    e.hire_date, e.birth_date, e.gender,
                    e.marital_status, e.national_id,
                    e.phone, e.email, e.address,
                    d.name as department_name,
                    p.name as position_name,
                    e.salary_currency,
                    e.salary_type,  -- monthly, hourly, etc.
                    e.working_hours,
                    e.bank_account,
                    e.bank_name,
                    e.is_active
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                WHERE e.id = ?
            """, (employee_id,))

            row = cursor.fetchone()
            if not row:
                return False, "الموظف غير موجود"

            columns = [column[0] for column in cursor.description]
            employee_data = dict(zip(columns, row))

            # Format dates
            for date_field in ['hire_date', 'birth_date']:
                if employee_data.get(date_field):
                    employee_data[date_field] = datetime.strptime(
                        employee_data[date_field], '%Y-%m-%d'
                    ).date()

            # Get salary components
            cursor.execute("""
                SELECT 
                    sc.id, sc.name, sc.name_ar, sc.type,
                    sc.is_taxable, sc.is_percentage,
                    COALESCE(esc.value, sc.value) as value,
                    COALESCE(esc.percentage, sc.percentage) as percentage,
                    esc.start_date, esc.end_date
                FROM employee_salary_components esc
                JOIN salary_components sc ON esc.component_id = sc.id
                WHERE esc.employee_id = ?
                  AND esc.is_active = 1
                  AND (esc.end_date IS NULL OR esc.end_date >= CURRENT_DATE)
            """, (employee_id,))

            salary_components = []
            for row in cursor.fetchall():
                columns = [column[0] for column in cursor.description]
                component = dict(zip(columns, row))
                salary_components.append(component)

            # Get salary adjustment history
            cursor.execute("""
                SELECT 
                    id, adjustment_type, amount, percentage,
                    reason, effective_date, end_date,
                    status, approved_by, approved_at,
                    created_at, created_by
                FROM salary_adjustments
                WHERE employee_id = ?
                ORDER BY effective_date DESC
            """, (employee_id,))

            salary_adjustments = []
            for row in cursor.fetchall():
                columns = [column[0] for column in cursor.description]
                adjustment = dict(zip(columns, row))
                salary_adjustments.append(adjustment)

            employee_data['salary_components'] = salary_components
            employee_data['salary_adjustments'] = salary_adjustments

            return True, employee_data

        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def update_employee_salary(
        self, 
        employee_id: int, 
        basic_salary: float,
        effective_date: date,
        reason: str,
        adjustment_type: str = 'increase',
        percentage: Optional[float] = None,
        created_by: int = None
    ) -> Tuple[bool, Union[int, str]]:
        """Update employee's basic salary with audit trail"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get current salary
            cursor.execute("""
                SELECT basic_salary 
                FROM employees 
                WHERE id = ?
            """, (employee_id,))
            
            current_salary = cursor.fetchone()[0]
            
            # Calculate adjustment amount
            amount = basic_salary - current_salary

            # Create salary adjustment record
            cursor.execute("""
                INSERT INTO salary_adjustments (
                    employee_id, adjustment_type,
                    amount, percentage, reason,
                    effective_date, status,
                    created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
            """, (
                employee_id, adjustment_type,
                amount, percentage, reason,
                effective_date, created_by
            ))

            adjustment_id = cursor.lastrowid

            # Update employee's basic salary
            cursor.execute("""
                UPDATE employees 
                SET basic_salary = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (basic_salary, employee_id))

            conn.commit()
            return True, adjustment_id

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def add_salary_component(
        self,
        employee_id: int,
        component_id: int,
        value: Optional[float] = None,
        percentage: Optional[float] = None,
        start_date: date = None,
        end_date: Optional[date] = None
    ) -> Tuple[bool, Union[int, str]]:
        """Add a salary component to an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Validate component exists
            cursor.execute("""
                SELECT is_percentage 
                FROM salary_components 
                WHERE id = ?
            """, (component_id,))

            row = cursor.fetchone()
            if not row:
                return False, "عنصر الراتب غير موجود"

            is_percentage = row[0]

            # Validate value/percentage based on component type
            if is_percentage and percentage is None:
                return False, "يجب تحديد النسبة المئوية"
            if not is_percentage and value is None:
                return False, "يجب تحديد القيمة"

            # Add component
            cursor.execute("""
                INSERT INTO employee_salary_components (
                    employee_id, component_id,
                    value, percentage,
                    start_date, end_date,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                employee_id, component_id,
                value, percentage,
                start_date or date.today(),
                end_date
            ))

            conn.commit()
            return True, cursor.lastrowid

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def update_salary_component(
        self,
        component_id: int,
        value: Optional[float] = None,
        percentage: Optional[float] = None,
        end_date: Optional[date] = None
    ) -> Tuple[bool, str]:
        """Update an employee's salary component"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            update_fields = []
            params = []

            if value is not None:
                update_fields.append("value = ?")
                params.append(value)

            if percentage is not None:
                update_fields.append("percentage = ?")
                params.append(percentage)

            if end_date is not None:
                update_fields.append("end_date = ?")
                params.append(end_date)

            if not update_fields:
                return False, "لم يتم تحديد أي تغييرات"

            params.append(component_id)
            
            cursor.execute(f"""
                UPDATE employee_salary_components
                SET {', '.join(update_fields)},
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, params)

            if cursor.rowcount == 0:
                return False, "عنصر الراتب غير موجود"

            conn.commit()
            return True, None

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def get_salary_history(
        self, 
        employee_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Tuple[bool, Union[List[Dict], str]]:
        """Get employee's salary history including adjustments and components"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT 
                    'adjustment' as entry_type,
                    sa.id,
                    sa.adjustment_type,
                    sa.amount,
                    sa.percentage,
                    sa.reason,
                    sa.effective_date as date,
                    sa.status,
                    u.name as approved_by_name
                FROM salary_adjustments sa
                LEFT JOIN users u ON sa.approved_by = u.id
                WHERE sa.employee_id = ?
                
                UNION ALL
                
                SELECT 
                    'component' as entry_type,
                    esc.id,
                    sc.type as adjustment_type,
                    esc.value as amount,
                    esc.percentage,
                    sc.name_ar as reason,
                    esc.start_date as date,
                    CASE 
                        WHEN esc.end_date IS NULL OR esc.end_date >= CURRENT_DATE 
                        THEN 'active' 
                        ELSE 'inactive' 
                    END as status,
                    NULL as approved_by_name
                FROM employee_salary_components esc
                JOIN salary_components sc ON esc.component_id = sc.id
                WHERE esc.employee_id = ?
            """

            params = [employee_id, employee_id]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]

            return True, history

        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def approve_salary_adjustment(
        self,
        adjustment_id: int,
        approved_by: int,
        status: str = 'approved'
    ) -> Tuple[bool, str]:
        """Approve or reject a salary adjustment"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Update adjustment status
            cursor.execute("""
                UPDATE salary_adjustments
                SET status = ?,
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, approved_by, adjustment_id))

            if cursor.rowcount == 0:
                return False, "التعديل غير موجود"

            conn.commit()
            return True, None

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
