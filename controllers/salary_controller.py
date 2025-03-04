from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class SalaryController(QObject):
    salary_updated = pyqtSignal(dict)
    payment_processed = pyqtSignal(dict)

    def __init__(self, database):
        super().__init__()
        self.db = database

    def update_salary(self, employee_id, salary_data):
        """Update or create salary structure for an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # First check if the employee exists
            cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
            if not cursor.fetchone():
                return False, f"Employee with ID {employee_id} not found"
            
            # Check if salary record exists
            cursor.execute("SELECT id FROM salaries WHERE employee_id = ?", (employee_id,))
            salary_record = cursor.fetchone()
            
            total_salary = (
                salary_data['base_salary'] +
                salary_data['bonuses'] +
                salary_data['overtime_pay'] -
                salary_data['deductions']
            )
            
            if salary_record:
                query = """
                    UPDATE salaries SET
                        base_salary = ?,
                        bonuses = ?,
                        deductions = ?,
                        overtime_pay = ?,
                        total_salary = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE employee_id = ?
                """
                params = (
                    salary_data['base_salary'],
                    salary_data['bonuses'],
                    salary_data['deductions'],
                    salary_data['overtime_pay'],
                    total_salary,
                    employee_id
                )
            else:
                query = """
                    INSERT INTO salaries (
                        employee_id, base_salary, bonuses,
                        deductions, overtime_pay, total_salary
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
                params = (
                    employee_id,
                    salary_data['base_salary'],
                    salary_data['bonuses'],
                    salary_data['deductions'],
                    salary_data['overtime_pay'],
                    total_salary
                )
            
            cursor.execute(query, params)
            conn.commit()
            
            salary_data['employee_id'] = employee_id
            salary_data['total_salary'] = total_salary
            self.salary_updated.emit(salary_data)
            
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def process_payment(self, payment_data):
        """Process a salary payment"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO salary_payments (
                    employee_id, amount_paid, payment_date,
                    payment_mode, status
                ) VALUES (?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                payment_data['employee_id'],
                payment_data['amount_paid'],
                payment_data['payment_date'],
                payment_data['payment_mode'],
                'Paid'
            ))
            
            payment_id = cursor.lastrowid
            conn.commit()
            
            payment_data['id'] = payment_id
            payment_data['status'] = 'Paid'
            self.payment_processed.emit(payment_data)
            
            return True, payment_id
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_salary_info(self, employee_id):
        """Get salary information for an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM salaries WHERE employee_id = ?", (employee_id,))
            salary = cursor.fetchone()
            
            if salary:
                columns = [description[0] for description in cursor.description]
                salary_dict = dict(zip(columns, salary))
                return True, salary_dict
            return False, "Salary information not found"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_payment_history(self, employee_id=None, start_date=None, end_date=None):
        """Get payment history with optional filters"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM salary_payments WHERE 1=1"
            params = []
            
            if employee_id:
                query += " AND employee_id = ?"
                params.append(employee_id)
            
            if start_date:
                query += " AND payment_date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND payment_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY payment_date DESC"
            
            cursor.execute(query, params)
            payments = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            payment_list = [dict(zip(columns, payment)) for payment in payments]
            
            return True, payment_list
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_payroll_summary(self, month=None, year=None, department=None):
        """Get payroll summary with optional filters"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    e.department,
                    COUNT(DISTINCT e.id) as employee_count,
                    SUM(s.total_salary) as total_payroll,
                    SUM(s.bonuses) as total_bonuses,
                    SUM(s.deductions) as total_deductions
                FROM employees e
                LEFT JOIN salaries s ON e.id = s.employee_id
                WHERE 1=1
            """
            params = []
            
            if department:
                query += " AND e.department = ?"
                params.append(department)
            
            if month and year:
                query += """ AND EXISTS (
                    SELECT 1 FROM salary_payments sp
                    WHERE sp.employee_id = e.id
                    AND strftime('%m', sp.payment_date) = ?
                    AND strftime('%Y', sp.payment_date) = ?
                )"""
                params.extend([f"{month:02d}", str(year)])
            
            query += " GROUP BY e.department"
            
            cursor.execute(query, params)
            summaries = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            summary_list = [dict(zip(columns, summary)) for summary in summaries]
            
            return True, summary_list
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_payments_by_date_range(self, start_date, end_date):
        """Get salary payments within a date range"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT p.*, e.name as employee_name
                FROM salary_payments p
                JOIN employees e ON p.employee_id = e.id
                WHERE payment_date BETWEEN ? AND ?
                ORDER BY payment_date DESC
            """
            
            cursor.execute(query, (start_date, end_date))
            columns = [col[0] for col in cursor.description]
            payments = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return payments
            
        except Exception as e:
            return []
        finally:
            conn.close()

    def get_salary_stats(self):
        """Get salary statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total salary budget
            cursor.execute("SELECT SUM(total_salary) FROM salaries")
            stats['total_salary'] = cursor.fetchone()[0] or 0
            
            # Average salary
            cursor.execute("SELECT AVG(total_salary) FROM salaries")
            stats['average_salary'] = cursor.fetchone()[0] or 0
            
            # Recent payments
            cursor.execute("""
                SELECT p.*, e.name as employee_name
                FROM salary_payments p
                JOIN employees e ON p.employee_id = e.id
                ORDER BY payment_date DESC
                LIMIT 10
            """)
            columns = [col[0] for col in cursor.description]
            stats['recent_payments'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            return {}
        finally:
            conn.close()

    def calculate_salary_projections(self, year, include_allowances=True, include_deductions=True, department_id=None):
        """Calculate salary projections for budget planning"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Base query to get employees
            query = """
                SELECT 
                    e.id, 
                    e.name,
                    e.basic_salary,
                    e.department_id,
                    d.name as department_name
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                WHERE e.is_active = 1
            """
            
            params = []
            
            if department_id:
                query += " AND e.department_id = ?"
                params.append(department_id)
                
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            employees = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Calculate projections by month
            monthly_projections = []
            annual_total = 0
            
            for month in range(1, 13):
                month_total = 0
                
                for emp in employees:
                    # Get basic salary
                    basic_salary = float(emp['basic_salary'])
                    
                    # Get allowances
                    allowances = 0
                    if include_allowances:
                        cursor.execute("""
                            SELECT 
                                sc.id,
                                esc.value,
                                esc.percentage,
                                esc.is_percentage
                            FROM employee_salary_components esc
                            JOIN salary_components sc ON esc.component_id = sc.id
                            WHERE esc.employee_id = ? AND sc.type = 'allowance'
                        """, (emp['id'],))
                        
                        for comp in cursor.fetchall():
                            comp_id, value, percentage, is_percentage = comp
                            if is_percentage:
                                allowances += basic_salary * percentage / 100
                            else:
                                allowances += value
                    
                    # Get deductions
                    deductions = 0
                    if include_deductions:
                        cursor.execute("""
                            SELECT 
                                sc.id,
                                esc.value,
                                esc.percentage,
                                esc.is_percentage
                            FROM employee_salary_components esc
                            JOIN salary_components sc ON esc.component_id = sc.id
                            WHERE esc.employee_id = ? AND sc.type = 'deduction'
                        """, (emp['id'],))
                        
                        for comp in cursor.fetchall():
                            comp_id, value, percentage, is_percentage = comp
                            if is_percentage:
                                deductions += basic_salary * percentage / 100
                            else:
                                deductions += value
                    
                    # Calculate net salary
                    net_salary = basic_salary + allowances - deductions
                    
                    # Add to month total
                    month_total += net_salary
                
                # Add month projection
                monthly_projections.append({
                    'month': month,
                    'total': month_total
                })
                
                # Add to annual total
                annual_total += month_total
            
            # Calculate department totals
            department_totals = {}
            
            for emp in employees:
                dept_id = emp['department_id']
                dept_name = emp['department_name']
                
                if dept_id not in department_totals:
                    department_totals[dept_id] = {
                        'id': dept_id,
                        'name': dept_name,
                        'total': 0
                    }
                
                # Get basic salary
                basic_salary = float(emp['basic_salary'])
                
                # Get allowances
                allowances = 0
                if include_allowances:
                    cursor.execute("""
                        SELECT 
                            sc.id,
                            esc.value,
                            esc.percentage,
                            esc.is_percentage
                        FROM employee_salary_components esc
                        JOIN salary_components sc ON esc.component_id = sc.id
                        WHERE esc.employee_id = ? AND sc.type = 'allowance'
                    """, (emp['id'],))
                    
                    for comp in cursor.fetchall():
                        comp_id, value, percentage, is_percentage = comp
                        if is_percentage:
                            allowances += basic_salary * percentage / 100
                        else:
                            allowances += value
                
                # Get deductions
                deductions = 0
                if include_deductions:
                    cursor.execute("""
                        SELECT 
                            sc.id,
                            esc.value,
                            esc.percentage,
                            esc.is_percentage
                        FROM employee_salary_components esc
                        JOIN salary_components sc ON esc.component_id = sc.id
                        WHERE esc.employee_id = ? AND sc.type = 'deduction'
                    """, (emp['id'],))
                    
                    for comp in cursor.fetchall():
                        comp_id, value, percentage, is_percentage = comp
                        if is_percentage:
                            deductions += basic_salary * percentage / 100
                        else:
                            deductions += value
                
                # Calculate net salary
                net_salary = basic_salary + allowances - deductions
                
                # Add to department total (annual)
                department_totals[dept_id]['total'] += net_salary * 12
            
            # Prepare result
            result = {
                'year': year,
                'monthly_projections': monthly_projections,
                'annual_total': annual_total,
                'department_totals': list(department_totals.values())
            }
            
            return True, result
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
