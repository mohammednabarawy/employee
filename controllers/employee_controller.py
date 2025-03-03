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
        image = QImage.fromData(photo_data, mime_type.split('/')[-1].upper())
        return QPixmap.fromImage(image)

    def _generate_employee_code(self, cursor):
        """Generate a unique employee code"""
        # Get the current max code
        cursor.execute("SELECT MAX(CAST(SUBSTR(code, 2) AS INTEGER)) FROM employees WHERE code LIKE 'E%'")
        result = cursor.fetchone()[0]
        
        # Start with 1 if no existing codes, otherwise increment the max
        next_number = 1 if result is None else result + 1
        
        # Format as E0001, E0002, etc.
        return f'E{next_number:04d}'

    def add_employee(self, employee_data):
        """Add a new employee to the database"""
        try:
            # Validate required fields
            required_fields = ['name', 'hire_date']
            for field in required_fields:
                if not employee_data.get(field):
                    return False, f"الحقل {field} مطلوب"
                    
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Generate unique employee code
                employee_data['code'] = self._generate_employee_code(cursor)
                
                # Handle photo data
                photo_data = None
                photo_mime_type = None
                if 'photo_path' in employee_data and employee_data['photo_path']:
                    photo_data = self._read_image_file(employee_data['photo_path'])
                    photo_mime_type = self._get_mime_type(employee_data['photo_path'])

                # Insert into employees table
                employee_query = """
                    INSERT INTO employees (
                        code, name, name_ar, department_id, position_id,
                        basic_salary, hire_date, birth_date, gender,
                        marital_status, national_id, phone, email,
                        address, bank_account, bank_name, photo_data,
                        photo_mime_type, is_active,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                cursor.execute(employee_query, (
                    employee_data.get('code'),
                    employee_data.get('name'),
                    employee_data.get('name_ar'),
                    employee_data.get('department_id'),
                    employee_data.get('position_id'),
                    employee_data.get('basic_salary', 0),
                    employee_data.get('hire_date'),
                    employee_data.get('birth_date'),
                    employee_data.get('gender'),
                    employee_data.get('marital_status'),
                    employee_data.get('national_id'),
                    employee_data.get('phone'),
                    employee_data.get('email'),
                    employee_data.get('address'),
                    employee_data.get('bank_account'),
                    employee_data.get('bank_name'),
                    photo_data,
                    photo_mime_type,
                    employee_data.get('is_active', 1)
                ))
                
                employee_id = cursor.lastrowid
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
            # Validate required fields
            required_fields = ['name', 'hire_date']
            for field in required_fields:
                if field in employee_data and not employee_data.get(field):
                    return False, f"الحقل {field} مطلوب"
                    
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Handle photo data
                photo_data = None
                photo_mime_type = None
                if 'photo_path' in employee_data and employee_data['photo_path']:
                    photo_data = self._read_image_file(employee_data['photo_path'])
                    photo_mime_type = self._get_mime_type(employee_data['photo_path'])

                # Update employees table
                employee_query = """
                    UPDATE employees SET
                        code = COALESCE(?, code),
                        name = COALESCE(?, name),
                        name_ar = ?,
                        department_id = ?,
                        position_id = ?,
                        basic_salary = COALESCE(?, basic_salary),
                        hire_date = COALESCE(?, hire_date),
                        birth_date = ?,
                        gender = ?,
                        marital_status = ?,
                        national_id = ?,
                        phone = ?,
                        email = ?,
                        address = ?,
                        bank_account = ?,
                        bank_name = ?,
                        photo_data = COALESCE(?, photo_data),
                        photo_mime_type = COALESCE(?, photo_mime_type),
                        is_active = COALESCE(?, is_active),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                
                cursor.execute(employee_query, (
                    employee_data.get('code'),
                    employee_data.get('name'),
                    employee_data.get('name_ar'),
                    employee_data.get('department_id'),
                    employee_data.get('position_id'),
                    employee_data.get('basic_salary'),
                    employee_data.get('hire_date'),
                    employee_data.get('birth_date'),
                    employee_data.get('gender'),
                    employee_data.get('marital_status'),
                    employee_data.get('national_id'),
                    employee_data.get('phone'),
                    employee_data.get('email'),
                    employee_data.get('address'),
                    employee_data.get('bank_account'),
                    employee_data.get('bank_name'),
                    photo_data,
                    photo_mime_type,
                    employee_data.get('is_active'),
                    employee_id
                ))
                
                cursor.execute("COMMIT")
                
                # If photo was updated, convert it to QPixmap for the UI
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
            
            cursor.execute("""
                SELECT 
                    e.*, 
                    d.name as department_name,
                    p.name as position_name
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
            
            # Convert photo data to QPixmap if available
            if employee_data.get('photo_data') and employee_data.get('photo_mime_type'):
                employee_data['photo_pixmap'] = self._pixmap_from_data(
                    employee_data['photo_data'],
                    employee_data['photo_mime_type']
                )
            
            return True, employee_data
            
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
