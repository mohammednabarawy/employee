import os
import shutil
from datetime import datetime

def organize_project():
    """Organize the project files and clean up unnecessary files"""
    print("Starting project organization...")
    
    # Root directory of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create directories if they don't exist
    directories = [
        'tests',
        'docs',
        'utils',
        'logs',
        'temp'
    ]
    
    for directory in directories:
        dir_path = os.path.join(root_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {directory}")
    
    # Files to delete (temporary files, old test databases, etc.)
    files_to_delete = [
        'test2.db',
        'test_employee.db',
        'test_employee_simple.db',
        'test_salary_attendance_basic.db',
        'stress_test.db',
        'app.txt',
        'fix_issues_log.txt'
    ]
    
    # Delete unnecessary files
    for file in files_to_delete:
        file_path = os.path.join(root_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted file: {file}")
    
    # Move test files to tests directory
    test_files = [
        'test_salary_attendance.py',
        'test_salary_attendance_basic.py',
        'test_salary_simple.py',
        'test_schema.py',
        'stress_test.py',
        'run_tests.py',
        'run_stress_tests.bat'
    ]
    
    for file in test_files:
        src_path = os.path.join(root_dir, file)
        dst_path = os.path.join(root_dir, 'tests', file)
        
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)
            print(f"Moved {file} to tests directory")
    
    # Move documentation files to docs directory
    doc_files = [
        'README.md',
        'STRESS_TESTING.md'
    ]
    
    for file in doc_files:
        src_path = os.path.join(root_dir, file)
        dst_path = os.path.join(root_dir, 'docs', file)
        
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)
            print(f"Moved {file} to docs directory")
    
    # Move utility scripts to utils directory
    util_files = [
        'fix_database_schema.py',
        'check_database_schema.py',
        'database_maintenance.py',
        'fix_issues.py',
        'fix_salary_tables.py',
        'fix_stress_test_db.py',
        'init_db.py',
        'check_db.py',
        'create_backup.bat',
        'commit_changes.bat'
    ]
    
    for file in util_files:
        src_path = os.path.join(root_dir, file)
        dst_path = os.path.join(root_dir, 'utils', file)
        
        if os.path.exists(src_path):
            shutil.move(src_path, dst_path)
            print(f"Moved {file} to utils directory")
    
    # Clean up backups - keep only the 5 most recent
    backup_dir = os.path.join(root_dir, 'backups')
    if os.path.exists(backup_dir):
        backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')]
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Keep only the 5 most recent backups
        if len(backup_files) > 5:
            for old_backup in backup_files[5:]:
                os.remove(old_backup)
                print(f"Deleted old backup: {os.path.basename(old_backup)}")
    
    print("\nProject organization completed!")
    print("\nNew project structure:")
    
    # Print the new project structure
    for root, dirs, files in os.walk(root_dir, topdown=True):
        level = root.replace(root_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        
        # Limit the number of files shown per directory to avoid clutter
        if len(files) > 10:
            for f in files[:5]:
                print(f"{sub_indent}{f}")
            print(f"{sub_indent}... ({len(files) - 5} more files)")
        else:
            for f in files:
                print(f"{sub_indent}{f}")

if __name__ == "__main__":
    organize_project()
