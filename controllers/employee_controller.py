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
                
                # Only process photo if photo_path is provided and not None
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
                    employee_data['code'],
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
                    employee_data.get('is_active', 1)
                ))
                
                # Get the ID of the newly inserted employee
                cursor.execute("SELECT last_insert_rowid()")
                employee_id = cursor.fetchone()[0]
                
                # Create employment details record
                employment_query = """
                    INSERT INTO employment_details (
                        employee_id, department_id, position_id, manager_id,
                        employee_status, employment_type, contract_type,
                        start_date, end_date, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                
                cursor.execute(employment_query, (
                    employee_id,
                    employee_data.get('department_id'),
                    employee_data.get('position_id'),
                    employee_data.get('manager_id'),
                    'نشط',  # Default status is Active in Arabic
                    employee_data.get('employment_type', 'دوام كامل'),  # Default is Full Time in Arabic
                    employee_data.get('contract_type', 'دائم'),  # Default is Permanent in Arabic
                    employee_data.get('hire_date'),
                    employee_data.get('end_date'),
                ))
                
                cursor.execute("COMMIT")
                
                # Get the complete employee data with photo
                success, new_employee = self.get_employee(employee_id)
                if not success:
                    return False, "Failed to retrieve new employee data"
                
                self.employee_added.emit(new_employee)
                return True, new_employee
                
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
                
                # Check if photo_path is explicitly set to None (photo cleared)
                clear_photo = 'photo_path' in employee_data and employee_data['photo_path'] is None
                
                if 'photo_path' in employee_data and employee_data['photo_path']:
                    # New photo selected
                    photo_data = self._read_image_file(employee_data['photo_path'])
                    photo_mime_type = self._get_mime_type(employee_data['photo_path'])

                # Prepare the query - if clear_photo is True, we'll explicitly set photo_data and photo_mime_type to NULL
                if clear_photo:
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
                            photo_data = NULL,
                            photo_mime_type = NULL,
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
                        employee_data.get('is_active'),
                        employee_id
                    ))
                else:
                    # Only update photo if a new one was provided
                    if photo_data and photo_mime_type:
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
                                photo_data = ?,
                                photo_mime_type = ?,
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
                    else:
                        # Don't update photo fields if no new photo was provided
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
                            employee_data.get('is_active'),
                            employee_id
                        ))
                
                cursor.execute("COMMIT")
                
                # Get the updated employee data with photo
                success, updated_employee = self.get_employee(employee_id)
                if not success:
                    return False, "Failed to retrieve updated employee data"
                
                # Update the employee_data with the updated values
                employee_data = updated_employee
                
                self.employee_updated.emit(employee_data)
                return True, employee_data
                
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
                    e.is_active,
                    e.photo_data,
                    e.photo_mime_type
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                ORDER BY e.name
            """
            
            cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            employees = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Convert photo data to QPixmap for each employee
            for employee in employees:
                if employee.get('photo_data') and employee.get('photo_mime_type'):
                    employee['photo_pixmap'] = self._pixmap_from_data(
                        employee['photo_data'],
                        employee['photo_mime_type']
                    )
            
            return True, employees
            
        except Exception as e:
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
            
            # Active employees
            cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
            stats['active_employees'] = cursor.fetchone()[0]
            
            # Department distribution
            cursor.execute("""
                SELECT d.name, COUNT(e.id) 
                FROM departments d
                LEFT JOIN employees e ON d.id = e.department_id
                WHERE d.is_active = 1
                GROUP BY d.name
            """)
            stats['department_distribution'] = dict(cursor.fetchall())
            
            # Total salary
            cursor.execute("SELECT SUM(basic_salary) FROM employees WHERE is_active = 1")
            stats['total_salary'] = cursor.fetchone()[0] or 0
            
            # Average salary
            cursor.execute("SELECT AVG(basic_salary) FROM employees WHERE is_active = 1")
            stats['average_salary'] = cursor.fetchone()[0] or 0
            
            # Salary ranges
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN basic_salary < 5000 THEN '0-5,000'
                        WHEN basic_salary < 10000 THEN '5,000-10,000'
                        WHEN basic_salary < 15000 THEN '10,000-15,000'
                        WHEN basic_salary < 20000 THEN '15,000-20,000'
                        ELSE '20,000+'
                    END as range,
                    COUNT(*) as count,
                    AVG(basic_salary) as avg_salary,
                    SUM(basic_salary) as total_salary
                FROM employees
                WHERE is_active = 1
                GROUP BY 
                    CASE 
                        WHEN basic_salary < 5000 THEN '0-5,000'
                        WHEN basic_salary < 10000 THEN '5,000-10,000'
                        WHEN basic_salary < 15000 THEN '10,000-15,000'
                        WHEN basic_salary < 20000 THEN '15,000-20,000'
                        ELSE '20,000+'
                    END
                ORDER BY MIN(basic_salary)
            """)
            stats['salary_ranges'] = [dict(zip(['range', 'count', 'avg_salary', 'total_salary'], row)) 
                                    for row in cursor.fetchall()]
            
            return stats
            
        except Exception as e:
            print(f"Error getting employee stats: {e}")
            return {}
        finally:
            conn.close()

    def search_employees(self, search_term, filters=None):
        """Search employees with optional filters"""
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
                    e.is_active,
                    e.photo_data,
                    e.photo_mime_type
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                WHERE 1=1
            """
            params = []
            
            if search_term:
                query += """ AND (
                    e.name LIKE ? OR
                    e.name_ar LIKE ? OR
                    e.email LIKE ? OR
                    e.phone LIKE ? OR
                    e.code LIKE ? OR
                    e.national_id LIKE ? OR
                    p.name LIKE ? OR
                    d.name LIKE ?
                )"""
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern] * 8)
            
            if filters:
                if 'department_id' in filters:
                    query += " AND e.department_id = ?"
                    params.append(filters['department_id'])
                if 'position_id' in filters:
                    query += " AND e.position_id = ?"
                    params.append(filters['position_id'])
                if 'is_active' in filters:
                    query += " AND e.is_active = ?"
                    params.append(filters['is_active'])
                if 'salary_range' in filters:
                    min_salary, max_salary = filters['salary_range']
                    query += " AND e.basic_salary BETWEEN ? AND ?"
                    params.extend([min_salary, max_salary])
            
            query += " ORDER BY e.name"
            
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            employees = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Convert photo data to QPixmap for each employee
            for employee in employees:
                if employee.get('photo_data') and employee.get('photo_mime_type'):
                    employee['photo_pixmap'] = self._pixmap_from_data(
                        employee['photo_data'],
                        employee['photo_mime_type']
                    )
            
            return True, employees
            
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
        """Get all departments from the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, name_ar, description 
                FROM departments 
                WHERE is_active = 1
                ORDER BY name
            """)
            
            columns = [column[0] for column in cursor.description]
            departments = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return True, departments
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_positions(self):
        """Get all positions from the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, name_ar, department_id, description 
                FROM positions 
                WHERE is_active = 1
                ORDER BY name
            """)
            
            columns = [column[0] for column in cursor.description]
            positions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return True, positions
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def export_employees_to_csv(self, filename):
        """Export employees data to CSV file"""
        try:
            success, employees = self.get_all_employees()
            if not success:
                return False, "Failed to retrieve employee data"
                
            import csv
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Define CSV headers
                fieldnames = [
                    'code', 'name', 'name_ar', 'department_name', 'position_name',
                    'basic_salary', 'hire_date', 'birth_date', 'gender',
                    'marital_status', 'national_id', 'phone', 'email',
                    'address', 'bank_account', 'bank_name', 'is_active'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write employee data
                for emp in employees:
                    # Filter only the fields we want to export
                    emp_data = {field: emp.get(field, '') for field in fieldnames}
                    writer.writerow(emp_data)
                    
            return True, filename
            
        except Exception as e:
            return False, str(e)

    def add_department(self, department_data):
        """Add a new department to the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if department with same name exists
            cursor.execute("SELECT id FROM departments WHERE name = ?", (department_data.get('name'),))
            if cursor.fetchone():
                return False, "قسم بنفس الاسم موجود بالفعل"
            
            # Insert department
            cursor.execute("""
                INSERT INTO departments (name, name_ar, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                department_data.get('name'),
                department_data.get('name_ar'),
                department_data.get('description'),
                department_data.get('is_active', 1)
            ))
            
            department_id = cursor.lastrowid
            conn.commit()
            
            department_data['id'] = department_id
            return True, department_id
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def update_department(self, department_id, department_data):
        """Update an existing department"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if department exists
            cursor.execute("SELECT id FROM departments WHERE id = ?", (department_id,))
            if not cursor.fetchone():
                return False, "القسم غير موجود"
            
            # Check if another department with same name exists
            cursor.execute("SELECT id FROM departments WHERE name = ? AND id != ?", 
                          (department_data.get('name'), department_id))
            if cursor.fetchone():
                return False, "قسم بنفس الاسم موجود بالفعل"
            
            # Update department
            cursor.execute("""
                UPDATE departments 
                SET name = ?, 
                    name_ar = ?, 
                    description = ?, 
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                department_data.get('name'),
                department_data.get('name_ar'),
                department_data.get('description'),
                department_data.get('is_active', 1),
                department_id
            ))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def delete_department(self, department_id):
        """Delete a department if it has no employees"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if department exists
            cursor.execute("SELECT id FROM departments WHERE id = ?", (department_id,))
            if not cursor.fetchone():
                return False, "القسم غير موجود"
            
            # Check if department has employees
            cursor.execute("SELECT COUNT(*) FROM employees WHERE department_id = ?", (department_id,))
            if cursor.fetchone()[0] > 0:
                return False, "لا يمكن حذف القسم لأنه يحتوي على موظفين. قم بنقل الموظفين إلى قسم آخر أولاً"
            
            # Delete department
            cursor.execute("DELETE FROM departments WHERE id = ?", (department_id,))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def add_position(self, position_data):
        """Add a new position to the database"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if position with same name exists in the same department
            cursor.execute("""
                SELECT id FROM positions 
                WHERE name = ? AND department_id = ?
            """, (position_data.get('name'), position_data.get('department_id')))
            
            if cursor.fetchone():
                return False, "وظيفة بنفس الاسم موجودة بالفعل في هذا القسم"
            
            # Insert position
            cursor.execute("""
                INSERT INTO positions (name, name_ar, department_id, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                position_data.get('name'),
                position_data.get('name_ar'),
                position_data.get('department_id'),
                position_data.get('description'),
                position_data.get('is_active', 1)
            ))
            
            position_id = cursor.lastrowid
            conn.commit()
            
            position_data['id'] = position_id
            return True, position_id
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def update_position(self, position_id, position_data):
        """Update an existing position"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if position exists
            cursor.execute("SELECT id FROM positions WHERE id = ?", (position_id,))
            if not cursor.fetchone():
                return False, "المسمى الوظيفي غير موجود"
            
            # Check if another position with same name exists in the same department
            cursor.execute("""
                SELECT id FROM positions 
                WHERE name = ? AND department_id = ? AND id != ?
            """, (
                position_data.get('name'), 
                position_data.get('department_id'),
                position_id
            ))
            
            if cursor.fetchone():
                return False, "مسمى وظيفي بنفس الاسم موجود بالفعل في هذا القسم"
            
            # Update position
            cursor.execute("""
                UPDATE positions 
                SET name = ?, 
                    name_ar = ?, 
                    department_id = ?,
                    description = ?, 
                    is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                position_data.get('name'),
                position_data.get('name_ar'),
                position_data.get('department_id'),
                position_data.get('description'),
                position_data.get('is_active', 1),
                position_id
            ))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def delete_position(self, position_id):
        """Delete a position if it has no employees"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if position exists
            cursor.execute("SELECT id FROM positions WHERE id = ?", (position_id,))
            if not cursor.fetchone():
                return False, "المسمى الوظيفي غير موجود"
            
            # Check if position has employees
            cursor.execute("SELECT COUNT(*) FROM employees WHERE position_id = ?", (position_id,))
            if cursor.fetchone()[0] > 0:
                return False, "لا يمكن حذف المسمى الوظيفي لأنه مرتبط بموظفين. قم بتغيير المسمى الوظيفي للموظفين أولاً"
            
            # Delete position
            cursor.execute("DELETE FROM positions WHERE id = ?", (position_id,))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
