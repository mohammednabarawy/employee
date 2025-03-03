import bcrypt
import uuid
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

class AuthController(QObject):
    """Controller for user authentication and authorization"""
    
    # Signals
    user_logged_in = pyqtSignal(dict)
    user_logged_out = pyqtSignal()
    
    # User roles
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_HR = 'hr'
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_EMPLOYEE = 'employee'
    
    # Role permissions
    PERMISSIONS = {
        ROLE_ADMIN: [
            'manage_users', 'view_all_employees', 'manage_employees', 
            'view_all_salaries', 'manage_salaries', 'view_reports',
            'manage_settings', 'manage_departments', 'manage_positions',
            'export_data', 'import_data', 'view_audit_log'
        ],
        ROLE_MANAGER: [
            'view_all_employees', 'manage_employees', 
            'view_all_salaries', 'view_reports',
            'manage_departments', 'manage_positions'
        ],
        ROLE_HR: [
            'view_all_employees', 'manage_employees', 
            'view_reports', 'manage_departments', 'manage_positions'
        ],
        ROLE_ACCOUNTANT: [
            'view_all_employees', 'view_all_salaries', 
            'manage_salaries', 'view_reports', 'export_data'
        ],
        ROLE_EMPLOYEE: [
            'view_own_profile', 'view_own_salary'
        ]
    }
    
    ROLE_TEMPLATES = {
        'admin': {
            'permissions': {
                'manage_users': True,
                'edit_payroll': True,
                'view_reports': True,
                'export_data': True
            },
            'description': 'Full system access'
        },
        'hr_manager': {
            'permissions': {
                'manage_employees': True,
                'view_payroll': True,
                'generate_reports': True,
                'export_data': True
            },
            'description': 'HR management access'
        },
        'accountant': {
            'permissions': {
                'manage_payroll': True,
                'view_reports': True,
                'export_financials': True
            },
            'description': 'Financial processing access'
        },
        'viewer': {
            'permissions': {
                'view_employees': True,
                'view_reports': False
            },
            'description': 'Read-only basic access'
        }
    }
    
    def __init__(self, database):
        super().__init__()
        self.db = database
        self.current_user = None
        self.session_token = None
        self.session_expiry = None
    
    def hash_password(self, password):
        """Hash a password for storing"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, stored_password, provided_password):
        """Verify a stored password against a provided password"""
        return bcrypt.checkpw(
            provided_password.encode('utf-8'), 
            stored_password.encode('utf-8')
        )
    
    def create_user(self, username, password, email, full_name, role):
        """Create a new user"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return False, "اسم المستخدم موجود بالفعل"
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return False, "البريد الإلكتروني موجود بالفعل"
            
            # Hash the password
            hashed_password = self.hash_password(password)
            
            # Insert the new user
            cursor.execute("""
                INSERT INTO users (username, password, email, full_name, role, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                username, 
                hashed_password, 
                email, 
                full_name, 
                role, 
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                1
            ))
            
            conn.commit()
            return True, "تم إنشاء المستخدم بنجاح"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def login(self, username, password):
        """Authenticate a user and create a session"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get user by username
            cursor.execute("""
                SELECT id, username, password, email, full_name, role, is_active
                FROM users
                WHERE username = ?
            """, (username,))
            
            user = cursor.fetchone()
            if not user:
                return False, "اسم المستخدم أو كلمة المرور غير صحيحة"
            
            # Convert to dict
            user_dict = {
                'id': user[0],
                'username': user[1],
                'password': user[2],
                'email': user[3],
                'full_name': user[4],
                'role': user[5],
                'is_active': user[6]
            }
            
            # Check if user is active
            if not user_dict['is_active']:
                return False, "الحساب غير نشط. يرجى الاتصال بالمسؤول"
            
            # Verify password
            if not self.verify_password(user_dict['password'], password):
                # Log failed login attempt
                self._log_activity(user_dict['id'], 'login_failed', 'Failed login attempt')
                return False, "اسم المستخدم أو كلمة المرور غير صحيحة"
            
            # Create session
            self.current_user = user_dict
            self.session_token = str(uuid.uuid4())
            self.session_expiry = datetime.now() + timedelta(hours=8)
            
            # Log successful login
            self._log_activity(user_dict['id'], 'login', 'User logged in')
            
            # Emit signal
            self.user_logged_in.emit(user_dict)
            
            return True, user_dict
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def logout(self):
        """Log out the current user"""
        if self.current_user:
            # Log logout
            self._log_activity(self.current_user['id'], 'logout', 'User logged out')
            
            # Clear session
            self.current_user = None
            self.session_token = None
            self.session_expiry = None
            
            # Emit signal
            self.user_logged_out.emit()
            
            return True, "تم تسجيل الخروج بنجاح"
        
        return False, "لا يوجد مستخدم مسجل الدخول"
    
    def is_authenticated(self):
        """Check if a user is currently authenticated"""
        if not self.current_user or not self.session_token or not self.session_expiry:
            return False
        
        # Check if session has expired
        if datetime.now() > self.session_expiry:
            self.logout()
            return False
        
        return True
    
    def has_permission(self, permission):
        """Check if the current user has a specific permission"""
        if not self.is_authenticated():
            return False
        
        user_role = self.current_user['role']
        
        # Admin has all permissions
        if user_role == self.ROLE_ADMIN:
            return True
        
        # Check role permissions
        if user_role in self.PERMISSIONS:
            return permission in self.PERMISSIONS[user_role]
        
        return False
    
    def get_all_users(self):
        """Get all users from the database"""
        if not self.has_permission('manage_users'):
            return False, "ليس لديك صلاحية لإدارة المستخدمين"
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, full_name, role, created_at, is_active
                FROM users
                ORDER BY username
            """)
            
            columns = [column[0] for column in cursor.description]
            users = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return True, users
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
    
    def update_user(self, user_id, data):
        """Update a user's information"""
        if not self.has_permission('manage_users'):
            return False, "ليس لديك صلاحية لإدارة المستخدمين"
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False, "المستخدم غير موجود"
            
            # Build update query
            update_fields = []
            params = []
            
            if 'email' in data:
                update_fields.append("email = ?")
                params.append(data['email'])
            
            if 'full_name' in data:
                update_fields.append("full_name = ?")
                params.append(data['full_name'])
            
            if 'role' in data:
                update_fields.append("role = ?")
                params.append(data['role'])
            
            if 'is_active' in data:
                update_fields.append("is_active = ?")
                params.append(data['is_active'])
            
            if 'password' in data:
                update_fields.append("password = ?")
                params.append(self.hash_password(data['password']))
            
            if not update_fields:
                return False, "لم يتم تحديد أي حقول للتحديث"
            
            # Add user_id to params
            params.append(user_id)
            
            # Execute update
            cursor.execute(f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
            
            conn.commit()
            
            # Log activity
            self._log_activity(self.current_user['id'], 'update_user', f"Updated user {user_id}")
            
            return True, "تم تحديث المستخدم بنجاح"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def delete_user(self, user_id):
        """Delete a user"""
        if not self.has_permission('manage_users'):
            return False, "ليس لديك صلاحية لإدارة المستخدمين"
        
        # Cannot delete yourself
        if self.current_user and str(self.current_user['id']) == str(user_id):
            return False, "لا يمكنك حذف حسابك الخاص"
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return False, "المستخدم غير موجود"
            
            # Delete user
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            
            # Log activity
            self._log_activity(self.current_user['id'], 'delete_user', f"Deleted user {user_id}")
            
            return True, "تم حذف المستخدم بنجاح"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def change_password(self, old_password, new_password):
        """Change the current user's password"""
        if not self.is_authenticated():
            return False, "يجب تسجيل الدخول لتغيير كلمة المرور"
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Verify old password
            if not self.verify_password(self.current_user['password'], old_password):
                return False, "كلمة المرور الحالية غير صحيحة"
            
            # Hash new password
            hashed_password = self.hash_password(new_password)
            
            # Update password
            cursor.execute("""
                UPDATE users
                SET password = ?
                WHERE id = ?
            """, (hashed_password, self.current_user['id']))
            
            conn.commit()
            
            # Update current user
            self.current_user['password'] = hashed_password
            
            # Log activity
            self._log_activity(self.current_user['id'], 'change_password', "Changed password")
            
            return True, "تم تغيير كلمة المرور بنجاح"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def create_role(self, role_name, permissions=None):
        """Create new role from template"""
        template = self.ROLE_TEMPLATES.get(role_name.lower())
        if template:
            return self._save_role_to_db(role_name, template)
        # Handle custom roles
        return self._save_role_to_db(role_name, permissions or {})
    
    def _save_role_to_db(self, role_name, role_data):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if role already exists
            cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            if cursor.fetchone():
                return False, "Role already exists"
            
            # Insert the new role
            cursor.execute("""
                INSERT INTO roles (name, permissions, description)
                VALUES (?, ?, ?)
            """, (
                role_name, 
                str(role_data['permissions']), 
                role_data['description']
            ))
            
            conn.commit()
            return True, "Role created successfully"
            
        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def _log_activity(self, user_id, action, description):
        """Log user activity"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO audit_log (user_id, action, description, timestamp, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                action,
                description,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '127.0.0.1'  # In a real app, you'd get the actual IP
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error logging activity: {e}")
        finally:
            conn.close()
