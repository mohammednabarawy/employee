import sqlite3
from datetime import datetime
import os
from .schema import SCHEMA
import hashlib
import shutil

class Database:
    def __init__(self, db_file="employee.db"):
        self.db_file = db_file
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
        # Check if the database file exists
        db_exists = os.path.exists(db_file)
        
        # Create tables or validate schema
        self.create_tables()
        
        # If the database already existed, validate and fix its schema
        if db_exists:
            self.validate_schema()
    
    def change_database(self, new_db_file):
        """Change the current database file"""
        self.db_file = new_db_file
        
        # Check if the database file exists
        db_exists = os.path.exists(new_db_file)
        
        # Create tables if needed
        self.create_tables()
        
        # If the database already existed, validate and fix its schema
        if db_exists:
            self.validate_schema()
            
        return True
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def create_tables(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create tables in order of dependencies
            table_order = [
                'users',
                'departments',
                'positions',
                'employees',
                'salary_components',
                'employee_salary_components',
                'salaries',
                'salary_payments',
                'payment_methods',
                'payroll_periods',
                'payroll_entries',
                'payroll_entry_details',
                'payroll_entry_components',
                'employment_details',
                'employee_allowances',
                'attendance',
                'leaves',
                'loans',
                'audit_log'
            ]
            
            # Create tables in correct order
            for table_name in table_order:
                if table_name in SCHEMA:
                    cursor.execute(SCHEMA[table_name])
            
            # Insert default data
            self.insert_default_data(cursor)
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print("Error creating tables:", str(e))
            raise e
        finally:
            conn.close()
    
    def _hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def insert_default_data(self, cursor):
        """Insert default data into tables"""
        try:
            # Insert default departments
            cursor.execute("""
                INSERT OR IGNORE INTO departments (id, name, name_ar, description)
                VALUES 
                    (1, 'Administration', 'الإدارة', 'Main administration department'),
                    (2, 'Human Resources', 'الموارد البشرية', 'HR department'),
                    (3, 'Finance', 'المالية', 'Finance and accounting department'),
                    (4, 'IT', 'تقنية المعلومات', 'Information technology department'),
                    (5, 'Sales', 'المبيعات', 'Sales and marketing department')
            """)

            # Insert default positions
            cursor.execute("""
                INSERT OR IGNORE INTO positions (id, name, name_ar)
                VALUES 
                    (1, 'Manager', 'مدير'),
                    (2, 'Supervisor', 'مشرف'),
                    (3, 'Employee', 'موظف'),
                    (4, 'Accountant', 'محاسب'),
                    (5, 'Developer', 'مطور')
            """)
            
            # Insert default salary components
            cursor.execute("""
                INSERT OR IGNORE INTO salary_components (id, name, name_ar, type, is_taxable, is_percentage, value, percentage)
                VALUES 
                    (1, 'Housing Allowance', 'بدل سكن', 'allowance', 1, 0, 1000.00, NULL),
                    (2, 'Transportation Allowance', 'بدل مواصلات', 'allowance', 1, 0, 500.00, NULL),
                    (3, 'Phone Allowance', 'بدل هاتف', 'allowance', 1, 0, 100.00, NULL),
                    (4, 'Medical Insurance', 'تأمين طبي', 'deduction', 0, 1, NULL, 2.5),
                    (5, 'Social Insurance', 'تأمينات اجتماعية', 'deduction', 0, 1, NULL, 10.0)
            """)
            
            # Insert default payment methods
            cursor.execute("""
                INSERT OR IGNORE INTO payment_methods (id, name, name_ar)
                VALUES 
                    (1, 'Bank Transfer', 'تحويل بنكي'),
                    (2, 'Cheque', 'شيك'),
                    (3, 'Cash', 'نقدي')
            """)

        except Exception as e:
            print("Error inserting default data:", str(e))
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
    
    def recreate_tables(self):
        """Drop and recreate all tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Disable foreign key constraint checks
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            # Drop existing tables in reverse order of dependencies
            cursor.execute("DROP TABLE IF EXISTS audit_log")
            cursor.execute("DROP TABLE IF EXISTS loans")
            cursor.execute("DROP TABLE IF EXISTS leaves")
            cursor.execute("DROP TABLE IF EXISTS attendance")
            cursor.execute("DROP TABLE IF EXISTS employee_allowances")
            cursor.execute("DROP TABLE IF EXISTS employment_details")
            cursor.execute("DROP TABLE IF EXISTS payroll_entry_components")
            cursor.execute("DROP TABLE IF EXISTS payroll_entry_details")
            cursor.execute("DROP TABLE IF EXISTS payroll_entries")
            cursor.execute("DROP TABLE IF EXISTS payroll_periods")
            cursor.execute("DROP TABLE IF EXISTS payment_methods")
            cursor.execute("DROP TABLE IF EXISTS employee_salary_components")
            cursor.execute("DROP TABLE IF EXISTS salary_components")
            cursor.execute("DROP TABLE IF EXISTS employees")
            cursor.execute("DROP TABLE IF EXISTS positions")
            cursor.execute("DROP TABLE IF EXISTS departments")
            cursor.execute("DROP TABLE IF EXISTS users")
            
            # Re-enable foreign key constraint checks
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create tables in order of dependencies
            table_order = [
                'users',
                'departments',
                'positions',
                'employees',
                'salary_components',
                'employee_salary_components',
                'salaries',
                'salary_payments',
                'payment_methods',
                'payroll_periods',
                'payroll_entries',
                'payroll_entry_details',
                'payroll_entry_components',
                'employment_details',
                'employee_allowances',
                'attendance',
                'leaves',
                'loans',
                'audit_log'
            ]
            
            # Create tables in correct order
            for table_name in table_order:
                if table_name in SCHEMA:
                    print(f"Creating table {table_name}")
                    cursor.execute(SCHEMA[table_name])
            
            # Insert default data
            self.insert_default_data(cursor)
            
            conn.commit()
            print("Tables recreated successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"Error recreating tables: {e}")
            raise e
        finally:
            conn.close()

    def validate_schema(self):
        """Validate and fix the database schema if needed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all tables in the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Check for missing tables
            for table_name in SCHEMA:
                if table_name not in tables:
                    print(f"Creating missing table: {table_name}")
                    cursor.execute(SCHEMA[table_name])
            
            # Check if payroll_entries has required columns
            if 'payroll_entries' in tables:
                cursor.execute("PRAGMA table_info(payroll_entries)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'gross_salary' not in columns:
                    print("Adding missing column 'gross_salary' to payroll_entries table")
                    cursor.execute("ALTER TABLE payroll_entries ADD COLUMN gross_salary REAL DEFAULT 0")
                    cursor.execute("UPDATE payroll_entries SET gross_salary = basic_salary + total_allowances")
                
                if 'payment_date' not in columns:
                    print("Adding missing column 'payment_date' to payroll_entries table")
                    cursor.execute("ALTER TABLE payroll_entries ADD COLUMN payment_date DATE")
                    cursor.execute("UPDATE payroll_entries SET payment_date = date('now')")
            
            # Check if salaries table exists
            if 'salaries' not in tables:
                print("Creating missing 'salaries' table")
                cursor.execute(SCHEMA['salaries'])
            
            # Check if salary_payments table exists
            if 'salary_payments' not in tables:
                print("Creating missing 'salary_payments' table")
                cursor.execute(SCHEMA['salary_payments'])
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print("Error validating schema:", str(e))
        finally:
            conn.close()
            
    def backup_database(self):
        """Create a backup of the database"""
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy the database file to the backup location
            shutil.copy2(self.db_file, backup_path)
            
            # Clean up old backups (keep only the 10 most recent)
            self._cleanup_old_backups(10)
            
            return True, f"Database backed up to {backup_path}"
        except Exception as e:
            return False, f"Error backing up database: {str(e)}"
            
    def restore_database(self, backup_file):
        """Restore database from a backup file"""
        try:
            # Check if the backup file exists
            if not os.path.exists(backup_file):
                return False, "Backup file does not exist"
            
            # Create a backup of the current database before restoring
            current_backup_result, current_backup_message = self.backup_database()
            if not current_backup_result:
                return False, f"Failed to create backup before restore: {current_backup_message}"
            
            # Copy the backup file to the database file
            shutil.copy2(backup_file, self.db_file)
            
            # Validate and fix the schema of the restored database
            self.validate_schema()
            
            return True, "Database restored successfully"
        except Exception as e:
            return False, f"Error restoring database: {str(e)}"
            
    def import_database(self, import_file):
        """Import a database from a file"""
        try:
            # Check if the import file exists
            if not os.path.exists(import_file):
                return False, "Import file does not exist"
            
            # Create a backup before importing
            backup_result, backup_message = self.backup_database()
            if not backup_result:
                return False, f"Failed to create backup before import: {backup_message}"
            
            # Copy the import file to the database file
            shutil.copy2(import_file, self.db_file)
            
            # Validate and fix the schema of the imported database
            self.validate_schema()
            
            return True, "Database imported successfully"
        except Exception as e:
            return False, f"Error importing database: {str(e)}"
    
    def _get_backups(self):
        """Get a list of available backups, sorted by date (newest first)"""
        try:
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("backup_") and filename.endswith(".db"):
                    backup_path = os.path.join(self.backup_dir, filename)
                    backups.append(backup_path)
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return backups
        except Exception as e:
            print(f"Error getting backups: {e}")
            return []
            
    def _cleanup_old_backups(self, keep_count=10):
        """Clean up old backups, keeping only the specified number of most recent backups"""
        try:
            # Get all backups sorted by date (newest first)
            backups = self._get_backups()
            
            # If we have more backups than we want to keep
            if len(backups) > keep_count:
                # Remove the oldest backups
                for old_backup in backups[keep_count:]:
                    os.remove(old_backup)
                    print(f"Removed old backup: {old_backup}")
        except Exception as e:
            print(f"Error cleaning up old backups: {str(e)}")
            
    def get_database_stats(self):
        """Get statistics about the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Count records in main tables
            tables = ['employees', 'departments', 'positions', 'payroll_entries', 'payroll_periods']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
                
            # Get database file size
            stats['db_size'] = os.path.getsize(self.db_file) / (1024 * 1024)  # Size in MB
            
            # Get last modified time
            stats['last_modified'] = datetime.fromtimestamp(os.path.getmtime(self.db_file))
            
            # Get number of backups
            stats['backup_count'] = len(self._get_backups())
            
            return stats
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
        finally:
            conn.close()
