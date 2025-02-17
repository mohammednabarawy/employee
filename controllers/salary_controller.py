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
            
            # Check if salary record exists
            cursor.execute("SELECT id FROM salaries WHERE employee_id = ?", (employee_id,))
            salary_record = cursor.fetchone()
            
            if salary_record:
                query = """
                    UPDATE salaries SET
                        base_salary = ?,
                        bonuses = ?,
                        deductions = ?,
                        overtime_pay = ?,
                        total_salary = ?
                    WHERE employee_id = ?
                """
            else:
                query = """
                    INSERT INTO salaries (
                        employee_id, base_salary, bonuses,
                        deductions, overtime_pay, total_salary
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """
            
            total_salary = (
                salary_data['base_salary'] +
                salary_data['bonuses'] +
                salary_data['overtime_pay'] -
                salary_data['deductions']
            )
            
            params = (
                salary_data['base_salary'],
                salary_data['bonuses'],
                salary_data['deductions'],
                salary_data['overtime_pay'],
                total_salary,
                employee_id
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
