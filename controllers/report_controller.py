import pandas as pd
from datetime import datetime, timedelta
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
        """Get the total number of employees"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
            count = cursor.fetchone()[0]
            
            return True, count
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_monthly_payroll(self):
        """Get the total payroll amount for the current month"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get current month and year
            current_month = datetime.now().strftime('%Y-%m')
            
            # Try to get payroll data from payroll_entries table
            cursor.execute("""
                SELECT SUM(net_salary) 
                FROM payroll_entries 
                WHERE strftime('%Y-%m', payment_date) = ?
            """, (current_month,))
            
            total = cursor.fetchone()[0]
            
            # If no payroll data for current month, calculate from employee basic salaries
            if not total:
                cursor.execute("""
                    SELECT SUM(basic_salary) 
                    FROM employees 
                    WHERE is_active = 1
                """)
                total = cursor.fetchone()[0]
            
            return True, total or 0
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_active_users(self):
        """Get the number of active users"""
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
                SELECT d.name, SUM(e.basic_salary) as total
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                WHERE e.is_active = 1
                GROUP BY d.name
                ORDER BY total DESC
            """)
            
            results = cursor.fetchall()
            
            # Format data for chart
            labels = []
            values = []
            
            for row in results:
                labels.append(row[0])
                values.append(float(row[1]))
                
            return True, (labels, values)
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_attendance_stats(self):
        """Get attendance statistics for the last 7 days"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get dates for the last 7 days
            today = datetime.now().date()
            dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
            dates.reverse()  # Oldest first
            
            # Try to get attendance data if available
            cursor.execute("""
                SELECT date, COUNT(*) 
                FROM attendance 
                WHERE date >= ? 
                GROUP BY date
                ORDER BY date
            """, (dates[0],))
            
            attendance_data = cursor.fetchall()
            
            # Convert to dict for easier lookup
            attendance_dict = {row[0]: row[1] for row in attendance_data}
            
            # Get total employee count
            cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
            total_employees = cursor.fetchone()[0]
            
            # Prepare data for chart
            labels = []
            values = []
            
            for date_str in dates:
                labels.append(date_str)
                values.append(attendance_dict.get(date_str, 0))
                
            return True, (labels, values, total_employees)
            
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
