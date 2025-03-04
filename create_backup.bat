@echo off
echo Creating backup of modified files...

:: Create backup directory if it doesn't exist
if not exist "code_backup" mkdir code_backup

:: Copy all modified files to the backup directory
copy database\database.py code_backup\
copy database\payroll_schema.py code_backup\
copy controllers\report_controller.py code_backup\
copy controllers\salary_controller.py code_backup\
copy database_maintenance.py code_backup\
copy verify_database_consistency.py code_backup\
copy stress_test.py code_backup\

:: Create a text file with the commit message
copy commit_message.txt code_backup\

echo Backup created in the code_backup directory!
echo You can commit these files later when Git issues are resolved.
pause
