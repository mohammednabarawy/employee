import sqlite3
from datetime import datetime
import os
from .schema import CREATE_TABLES_SQL
import hashlib

class Database:
    def __init__(self, db_file="employee.db"):
        self.db_file = db_file
        self.create_tables()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def create_tables(self):
        """Create all database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create tables in the correct order to respect foreign key constraints
            table_order = [
                'users',  # Create users first since employees references it
                'employees',
                'departments',
                'positions',
                'employment_details',
                'attendance',
                'leaves',
                'salary_components',
                'employee_salary_components',
                'payroll',
                'payroll_details',
                'loans',
                'audit_log'
            ]
            
            for table in table_order:
                if table in CREATE_TABLES_SQL:
                    cursor.execute(CREATE_TABLES_SQL[table])
            
            # Insert default data
            self.insert_default_data(cursor)
            
            conn.commit()
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            raise e
        finally:
            conn.close()
    
    def _hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def insert_default_data(self, cursor):
        """Insert default data into the tables"""
        try:
            # Check if users table is empty
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                # Insert default admin user
                cursor.execute("""
                    INSERT INTO users (username, password, email, role, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, ('admin', self._hash_password('admin123'), 'admin@example.com', 'admin', 1))
            
            # Check if departments table is empty
            cursor.execute("SELECT COUNT(*) FROM departments")
            if cursor.fetchone()[0] == 0:
                # Insert default department
                cursor.execute("""
                    INSERT INTO departments (name, name_ar, code, description, active)
                    VALUES ('الإدارة العامة', 'الإدارة العامة', 'GEN', 'الإدارة العامة للشركة', 1)
                """)
            
            # Check if positions table is empty
            cursor.execute("SELECT COUNT(*) FROM positions")
            if cursor.fetchone()[0] == 0:
                # Insert default position
                cursor.execute("""
                    INSERT INTO positions (title, title_ar, code, description, active)
                    VALUES ('موظف', 'موظف', 'EMP', 'موظف عام', 1)
                """)
            
            # Check if salary_components table is empty
            cursor.execute("SELECT COUNT(*) FROM salary_components")
            if cursor.fetchone()[0] == 0:
                # Insert default salary components
                cursor.execute("""
                    INSERT INTO salary_components (name, name_ar, type, calculation_type, calculation_value, taxable, active)
                    VALUES 
                    ('الراتب الأساسي', 'الراتب الأساسي', 'earning', 'fixed', 0, 1, 1),
                    ('بدل سكن', 'بدل سكن', 'earning', 'percentage', 25, 1, 1),
                    ('بدل مواصلات', 'بدل مواصلات', 'earning', 'fixed', 500, 1, 1)
                """)
        except Exception as e:
            print(f"Error inserting default data: {str(e)}")
            raise e
    
    def execute_query(self, query, parameters=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, parameters)
        conn.commit()
        return cursor
    
    def fetch_query(self, query, parameters=()):
        cursor = self.execute_query(query, parameters)
        results = cursor.fetchall()
        cursor.connection.close()
        return results
