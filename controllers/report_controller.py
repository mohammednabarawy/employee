import pandas as pd
from datetime import datetime
from PyQt5.QtCore import QObject

class ReportController(QObject):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def generate_payroll_report(self, start_date, end_date):
        """Generate comprehensive payroll report"""
        query = f"""
            SELECT 
                e.name AS employee_name,
                d.name AS department,
                SUM(p.gross_salary) AS total_gross,
                SUM(p.net_salary) AS total_net,
                COUNT(p.id) AS payment_count
            FROM payroll_entries p
            JOIN employees e ON p.employee_id = e.id
            JOIN departments d ON e.department_id = d.id
            WHERE p.payment_date BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY e.id
            ORDER BY d.name, e.name
        """
        return self._execute_query(query)

    def generate_attendance_report(self, month, year):
        """Generate monthly attendance summary"""
        query = f"""
            SELECT
                e.name,
                COUNT(CASE WHEN a.status = 'present' THEN 1 END) AS days_present,
                COUNT(CASE WHEN a.status = 'absent' THEN 1 END) AS days_absent,
                SUM(a.overtime_hours) AS total_overtime
            FROM attendance a
            JOIN employees e ON a.employee_id = e.id
            WHERE strftime('%Y-%m', a.date) = '{year}-{month:02d}'
            GROUP BY e.id
        """
        return self._execute_query(query)
        
    def get_employee_count(self):
        """Get total number of employees"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            return True, count
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_monthly_payroll(self):
        """Get total monthly payroll amount"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute("""
                SELECT SUM(net_salary) 
                FROM payroll_entries 
                WHERE strftime('%Y-%m', payment_date) = ?
            """, (current_month,))
            total = cursor.fetchone()[0] or 0
            return True, total
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_active_users(self):
        """Get count of active system users"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            count = cursor.fetchone()[0]
            return True, count
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_payroll_distribution(self):
        """Get payroll distribution by department"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.name, SUM(p.net_salary)
                FROM payroll_entries p
                JOIN employees e ON p.employee_id = e.id
                JOIN departments d ON e.department_id = d.id
                WHERE strftime('%Y-%m', p.payment_date) = strftime('%Y-%m', 'now')
                GROUP BY d.name
            """)
            result = {row[0]: row[1] for row in cursor.fetchall()}
            return True, result
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_attendance_stats(self):
        """Get attendance statistics by department"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.name, 
                       COUNT(CASE WHEN a.status = 'present' THEN 1 END) * 100.0 / COUNT(*) as rate
                FROM attendance a
                JOIN employees e ON a.employee_id = e.id
                JOIN departments d ON e.department_id = d.id
                WHERE strftime('%Y-%m', a.date) = strftime('%Y-%m', 'now')
                GROUP BY d.name
            """)
            results = cursor.fetchall()
            departments = [row[0] for row in results]
            rates = [row[1] for row in results]
            return True, {'departments': departments, 'attendance_rates': rates}
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def _execute_query(self, query):
        try:
            conn = self.db.get_connection()
            df = pd.read_sql(query, conn)
            return True, df
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
