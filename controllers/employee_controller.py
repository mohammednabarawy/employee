from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class EmployeeController(QObject):
    employee_added = pyqtSignal(dict)
    employee_updated = pyqtSignal(dict)
    employee_deleted = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.db = database

    def add_employee(self, employee_data):
        """Add a new employee to the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO employees (
                    name, dob, gender, phone, email, position,
                    department, hire_date, salary_type, basic_salary,
                    bank_account, photo_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            cursor.execute(query, (
                employee_data['name'],
                employee_data['dob'],
                employee_data['gender'],
                employee_data['phone'],
                employee_data['email'],
                employee_data['position'],
                employee_data['department'],
                employee_data['hire_date'],
                employee_data['salary_type'],
                employee_data['basic_salary'],
                employee_data['bank_account'],
                employee_data.get('photo_path', None)
            ))
            
            employee_id = cursor.lastrowid
            conn.commit()
            employee_data['id'] = employee_id
            self.employee_added.emit(employee_data)
            return True, employee_id
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def update_employee(self, employee_id, employee_data):
        """Update an existing employee's information"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                UPDATE employees SET
                    name = ?, dob = ?, gender = ?, phone = ?,
                    email = ?, position = ?, department = ?,
                    hire_date = ?, salary_type = ?, basic_salary = ?,
                    bank_account = ?, photo_path = ?
                WHERE id = ?
            """
            
            cursor.execute(query, (
                employee_data['name'],
                employee_data['dob'],
                employee_data['gender'],
                employee_data['phone'],
                employee_data['email'],
                employee_data['position'],
                employee_data['department'],
                employee_data['hire_date'],
                employee_data['salary_type'],
                employee_data['basic_salary'],
                employee_data['bank_account'],
                employee_data.get('photo_path', None),
                employee_id
            ))
            
            conn.commit()
            employee_data['id'] = employee_id
            self.employee_updated.emit(employee_data)
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_employee(self, employee_id):
        """Delete an employee from the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # First check if there are any salary records
            cursor.execute("DELETE FROM salaries WHERE employee_id = ?", (employee_id,))
            cursor.execute("DELETE FROM salary_payments WHERE employee_id = ?", (employee_id,))
            cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
            
            conn.commit()
            self.employee_deleted.emit(employee_id)
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_employee(self, employee_id):
        """Get employee details by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM employees WHERE id = ?", (employee_id,))
            employee = cursor.fetchone()
            
            if employee:
                columns = [description[0] for description in cursor.description]
                employee_dict = dict(zip(columns, employee))
                return True, employee_dict
            return False, "Employee not found"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_all_employees(self):
        """Get all employees from the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT e.*, s.base_salary as basic_salary, s.total_salary
                FROM employees e
                LEFT JOIN salaries s ON e.id = s.employee_id
            """
            
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            employees = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return True, employees
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_employee_stats(self):
        """Get employee statistics"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total employees
            cursor.execute("SELECT COUNT(*) FROM employees")
            stats['total_employees'] = cursor.fetchone()[0]
            
            # Department distribution
            cursor.execute("SELECT department, COUNT(*) FROM employees GROUP BY department")
            stats['department_distribution'] = dict(cursor.fetchall())
            
            # Salary ranges
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN base_salary < 5000 THEN '0-5,000'
                        WHEN base_salary < 10000 THEN '5,000-10,000'
                        WHEN base_salary < 15000 THEN '10,000-15,000'
                        WHEN base_salary < 20000 THEN '15,000-20,000'
                        ELSE '20,000+'
                    END as range,
                    COUNT(*) as count,
                    AVG(base_salary) as avg_salary,
                    SUM(base_salary) as total_salary
                FROM salaries
                GROUP BY 
                    CASE 
                        WHEN base_salary < 5000 THEN '0-5,000'
                        WHEN base_salary < 10000 THEN '5,000-10,000'
                        WHEN base_salary < 15000 THEN '10,000-15,000'
                        WHEN base_salary < 20000 THEN '15,000-20,000'
                        ELSE '20,000+'
                    END
                ORDER BY MIN(base_salary)
            """)
            stats['salary_ranges'] = [dict(zip(['range', 'count', 'avg_salary', 'total_salary'], row)) 
                                    for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            return {}
        finally:
            conn.close()

    def search_employees(self, search_term, filters=None):
        """Search employees with optional filters"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM employees WHERE 1=1"
            params = []
            
            if search_term:
                query += """ AND (
                    name LIKE ? OR
                    email LIKE ? OR
                    phone LIKE ? OR
                    position LIKE ? OR
                    department LIKE ?
                )"""
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 5)
            
            if filters:
                if 'department' in filters:
                    query += " AND department = ?"
                    params.append(filters['department'])
                if 'salary_range' in filters:
                    min_salary, max_salary = filters['salary_range']
                    query += " AND basic_salary BETWEEN ? AND ?"
                    params.extend([min_salary, max_salary])
            
            cursor.execute(query, params)
            employees = cursor.fetchall()
            
            columns = [description[0] for description in cursor.description]
            employee_list = [dict(zip(columns, employee)) for employee in employees]
            
            return True, employee_list
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
