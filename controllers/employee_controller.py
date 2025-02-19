from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import os
import mimetypes

class EmployeeController(QObject):
    employee_added = pyqtSignal(dict)
    employee_updated = pyqtSignal(dict)
    employee_deleted = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.db = database
    
    def _get_mime_type(self, file_path):
        """Get MIME type of a file"""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    def _read_image_file(self, file_path):
        """Read image file and return its binary data"""
        with open(file_path, 'rb') as f:
            return f.read()
    
    def _pixmap_from_data(self, photo_data, mime_type):
        """Convert binary image data to QPixmap"""
        if not photo_data:
            return None
        
        image = QImage.fromData(photo_data, mime_type.split('/')[-1].upper())
        return QPixmap.fromImage(image)

    def add_employee(self, employee_data):
        """Add a new employee to the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Get admin user id for created_by
                cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
                admin_id = cursor.fetchone()[0]
                
                # Handle photo data
                photo_data = None
                photo_mime_type = None
                if 'photo_path' in employee_data and employee_data['photo_path']:
                    photo_data = self._read_image_file(employee_data['photo_path'])
                    photo_mime_type = self._get_mime_type(employee_data['photo_path'])
                
                # Insert into employees table
                employee_query = """
                    INSERT INTO employees (
                        name, name_ar, dob, gender, nationality,
                        national_id, passport_number, phone_primary,
                        phone_secondary, email, address,
                        photo_data, photo_mime_type,
                        created_by, updated_by, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                cursor.execute(employee_query, (
                    employee_data.get('name'),
                    employee_data.get('name_ar'),
                    employee_data.get('dob'),
                    employee_data.get('gender'),
                    employee_data.get('nationality'),
                    employee_data.get('national_id'),
                    employee_data.get('passport_number'),
                    employee_data.get('phone_primary'),
                    employee_data.get('phone_secondary'),
                    employee_data.get('email'),
                    employee_data.get('address'),
                    photo_data,
                    photo_mime_type,
                    admin_id,  # created_by
                    admin_id   # updated_by
                ))
                
                employee_id = cursor.lastrowid
                
                # Get or create department
                department_name = employee_data.get('department_name', 'الإدارة العامة')
                cursor.execute("""
                    INSERT OR IGNORE INTO departments (name, code, created_by, updated_by)
                    VALUES (?, ?, ?, ?)
                """, (department_name, department_name[:3].upper(), admin_id, admin_id))
                
                cursor.execute("SELECT id FROM departments WHERE name = ?", (department_name,))
                department_id = cursor.fetchone()[0]
                
                # Get or create position
                position_title = employee_data.get('position_title', 'موظف')
                cursor.execute("""
                    INSERT OR IGNORE INTO positions (title, code, created_by, updated_by)
                    VALUES (?, ?, ?, ?)
                """, (position_title, position_title[:3].upper(), admin_id, admin_id))
                
                cursor.execute("SELECT id FROM positions WHERE title = ?", (position_title,))
                position_id = cursor.fetchone()[0]
                
                # Insert into employment_details table
                employment_query = """
                    INSERT INTO employment_details (
                        employee_id, department_id, position_id,
                        hire_date, contract_type, employee_status,
                        basic_salary, salary_currency, salary_type,
                        bank_account, created_by, updated_by,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                cursor.execute(employment_query, (
                    employee_id,
                    department_id,
                    position_id,
                    employee_data.get('hire_date'),
                    employee_data.get('contract_type', 'دوام كامل'),
                    employee_data.get('employee_status', 'نشط'),
                    employee_data.get('basic_salary', 0),
                    employee_data.get('salary_currency', 'ريال سعودي'),
                    employee_data.get('salary_type', 'شهري'),
                    employee_data.get('bank_account', ''),
                    admin_id,
                    admin_id
                ))
                
                cursor.execute("COMMIT")
                
                # Convert photo data to QPixmap for the UI
                if photo_data and photo_mime_type:
                    employee_data['photo_pixmap'] = self._pixmap_from_data(photo_data, photo_mime_type)
                
                employee_data['id'] = employee_id
                self.employee_added.emit(employee_data)
                return True, employee_id
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def update_employee(self, employee_id, employee_data):
        """Update an existing employee's information"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Get admin user id for updated_by
                cursor.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1")
                admin_id = cursor.fetchone()[0]
                
                # Handle photo data
                photo_data = None
                photo_mime_type = None
                if 'photo_path' in employee_data and employee_data['photo_path']:
                    photo_data = self._read_image_file(employee_data['photo_path'])
                    photo_mime_type = self._get_mime_type(employee_data['photo_path'])
                
                # Update employees table
                employee_query = """
                    UPDATE employees SET
                        name = ?, name_ar = ?, dob = ?, gender = ?,
                        nationality = ?, national_id = ?, passport_number = ?,
                        phone_primary = ?, phone_secondary = ?, email = ?,
                        address = ?, photo_data = COALESCE(?, photo_data),
                        photo_mime_type = COALESCE(?, photo_mime_type),
                        updated_by = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                
                cursor.execute(employee_query, (
                    employee_data.get('name'),
                    employee_data.get('name_ar'),
                    employee_data.get('dob'),
                    employee_data.get('gender'),
                    employee_data.get('nationality'),
                    employee_data.get('national_id'),
                    employee_data.get('passport_number'),
                    employee_data.get('phone_primary'),
                    employee_data.get('phone_secondary'),
                    employee_data.get('email'),
                    employee_data.get('address'),
                    photo_data,
                    photo_mime_type,
                    admin_id,  # updated_by
                    employee_id
                ))
                
                # Update employment_details table
                employment_query = """
                    UPDATE employment_details SET
                        hire_date = ?,
                        contract_type = ?,
                        employee_status = ?,
                        basic_salary = ?,
                        salary_currency = ?,
                        salary_type = ?,
                        bank_account = ?
                    WHERE employee_id = ?
                """
                
                cursor.execute(employment_query, (
                    employee_data.get('hire_date'),
                    employee_data.get('contract_type', 'دوام كامل'),
                    employee_data.get('employee_status', 'نشط'),
                    employee_data.get('basic_salary', 0),
                    employee_data.get('salary_currency', 'SAR'),
                    employee_data.get('salary_type', 'شهري'),
                    employee_data.get('bank_account'),
                    employee_id
                ))
                
                cursor.execute("COMMIT")
                
                # Convert photo data to QPixmap for the UI
                if photo_data and photo_mime_type:
                    employee_data['photo_pixmap'] = self._pixmap_from_data(photo_data, photo_mime_type)
                
                employee_data['id'] = employee_id
                self.employee_updated.emit(employee_data)
                return True, None
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def delete_employee(self, employee_id):
        """Delete an employee from the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Check if employee exists
                cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
                if not cursor.fetchone():
                    cursor.execute("ROLLBACK")
                    return False, "الموظف غير موجود"
                
                # Check if employee is a manager in departments
                cursor.execute("SELECT id FROM departments WHERE manager_id = ?", (employee_id,))
                if cursor.fetchone():
                    cursor.execute("ROLLBACK")
                    return False, "لا يمكن حذف الموظف لأنه مدير قسم. قم بتعيين مدير آخر أولاً"
                
                # Check if employee is a manager for other employees
                cursor.execute("SELECT id FROM employment_details WHERE manager_id = ?", (employee_id,))
                if cursor.fetchone():
                    cursor.execute("ROLLBACK")
                    return False, "لا يمكن حذف الموظف لأنه مدير لموظفين آخرين. قم بتعيين مدير آخر لهم أولاً"
                
                # Delete records in correct order to respect foreign key constraints
                tables = [
                    'payroll_details',
                    'payroll',
                    'employee_salary_components',
                    'loans',
                    'leaves',
                    'attendance',
                    'employment_details',
                    'employees'
                ]
                
                for table in tables:
                    cursor.execute(f"DELETE FROM {table} WHERE employee_id = ?", (employee_id,))
                
                # Commit the transaction
                cursor.execute("COMMIT")
                self.employee_deleted.emit(employee_id)
                return True, None
                
            except Exception as e:
                # If any error occurs, rollback the transaction
                cursor.execute("ROLLBACK")
                raise e
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_employee(self, employee_id):
        """Get employee details by ID"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT e.*, ed.*
                FROM employees e
                LEFT JOIN employment_details ed ON e.id = ed.employee_id
                WHERE e.id = ?
            """
            
            cursor.execute(query, (employee_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [description[0] for description in cursor.description]
                employee_dict = dict(zip(columns, row))
                
                # Convert photo data to QPixmap if exists
                if employee_dict.get('photo_data') and employee_dict.get('photo_mime_type'):
                    employee_dict['photo_pixmap'] = self._pixmap_from_data(
                        employee_dict['photo_data'],
                        employee_dict['photo_mime_type']
                    )
                
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
                SELECT 
                    e.id,
                    e.code,
                    e.name,
                    e.name_ar,
                    e.department_id,
                    d.name as department_name,
                    e.position_id,
                    p.name as position_name,
                    e.basic_salary,
                    e.hire_date,
                    e.birth_date,
                    e.gender,
                    e.marital_status,
                    e.national_id,
                    e.phone,
                    e.email,
                    e.address,
                    e.bank_account,
                    e.bank_name,
                    e.is_active
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                ORDER BY e.name
            """
            
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            employees = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return True, employees
            
        except Exception as e:
            print(f"Error in get_all_employees: {str(e)}")
            return False, str(e)
        finally:
            conn.close()

    def get_active_employees(self):
        """Get all active employees"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    e.id,
                    e.name,
                    e.code,
                    e.department_id,
                    d.name as department_name,
                    e.position_id,
                    p.name as position_name,
                    e.basic_salary,
                    e.hire_date,
                    e.is_active
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                WHERE e.is_active = 1
                ORDER BY e.name
            """)
            
            employees = []
            for row in cursor.fetchall():
                employee = {
                    'id': row[0],
                    'name': row[1],
                    'code': row[2],
                    'department_id': row[3],
                    'department_name': row[4],
                    'position_id': row[5],
                    'position_name': row[6],
                    'basic_salary': row[7],
                    'hire_date': row[8],
                    'is_active': row[9]
                }
                employees.append(employee)
            
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

    def fix_employee_statuses(self):
        """Fix employee statuses to use Arabic status values"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Update any 'Active' statuses to 'نشط'
            cursor.execute("""
                UPDATE employment_details 
                SET employee_status = 'نشط'
                WHERE employee_status = 'Active'
            """)
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_departments(self):
        """Get all departments"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    d.id,
                    d.name,
                    d.code,
                    d.manager_id,
                    e.name as manager_name
                FROM departments d
                LEFT JOIN employees e ON d.manager_id = e.id
                WHERE d.is_active = 1
                ORDER BY d.name
            """)
            
            departments = []
            for row in cursor.fetchall():
                department = {
                    'id': row[0],
                    'name': row[1],
                    'code': row[2],
                    'manager_id': row[3],
                    'manager_name': row[4]
                }
                departments.append(department)
            
            return True, departments
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
