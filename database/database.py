import sqlite3
from datetime import datetime
import os
import re
import hashlib
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='database.log',
    filemode='w'
)

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
        
        try:
            # Read schema from file
            schema_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'schema.sql'
            )
            
            with open(schema_path, 'r') as schema_file:
                schema_sql = schema_file.read()
            
            # Use SQLite's executescript for better handling of multiple statements
            conn.executescript(schema_sql)
            conn.commit()
            
            logging.info("Database schema created successfully")
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Error creating tables: {e}")
            print(f"Error creating tables: {e}")
            raise
        finally:
            conn.close()
    
    def validate_schema(self):
        """Validate and update database schema if needed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check for required tables
            required_tables = [
                'employee_types', 'employees', 'employee_details', 
                'salary_components', 'employee_salary_components',
                'tax_brackets', 'social_insurance_config',
                'leave_types', 'leave_balances', 'leave_requests',
                'payroll_periods', 'payroll_entries', 'attendance_hours'
            ]
            
            # Get existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            # Check for missing tables
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logging.warning(f"Missing tables detected: {missing_tables}")
                # Re-run create_tables to add missing tables
                self.create_tables()
            
        except Exception as e:
            logging.error(f"Error validating schema: {e}")
            print(f"Error validating schema: {e}")
        finally:
            conn.close()
    
    def _hash_password(self, password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
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
            
            # Drop all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                if table[0] != 'sqlite_sequence':  # Don't drop internal SQLite tables
                    cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            
            # Recreate tables
            conn.close()  # Close current connection
            self.create_tables()
            
            print("Tables recreated successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"Error recreating tables: {e}")
            raise e
        finally:
            if not conn.closed:
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
