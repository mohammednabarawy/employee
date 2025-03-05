@echo off
echo Committing changes...

git add database/database.py
git add database/payroll_schema.py
git add controllers/report_controller.py
git add controllers/salary_controller.py
git add database_maintenance.py
git add verify_database_consistency.py
git add stress_test.py

git commit -m "fix: Ensure database schema consistency across all databases

This commit implements comprehensive changes to ensure the Employee Management System
behaves consistently regardless of which database it's using:

1. Enhanced the Database class with automatic schema validation and repair:
   - Added validate_schema() method to check for missing tables and columns
   - Modified __init__ and change_database methods to validate schema on connection
   - Updated import_database and restore_database methods to validate after operations

2. Improved backup and restore functionality:
   - Enhanced backup_database method with better error handling
   - Added automatic cleanup of old backups
   - Ensured restored databases maintain schema consistency

3. Created comprehensive database verification utilities:
   - Added database_maintenance.py for checking and fixing database schemas
   - Added verify_database_consistency.py to check and fix all databases at once

These changes ensure that any database used by the application - whether newly
created, restored from backup, or imported - will always have the correct schema
with all necessary tables and columns for reliable operation."

echo Done!
pause
