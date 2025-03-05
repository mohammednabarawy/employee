import os
import shutil
import sys
from datetime import datetime

def maintain_project_structure():
    """
    Utility script to maintain the project structure:
    1. Ensure all required directories exist
    2. Move misplaced files to their correct locations
    3. Clean up temporary files and old backups
    4. Generate a report of the project structure
    """
    print("Maintaining project structure...")
    
    # Root directory of the project
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Required directories
    required_dirs = [
        'assets',
        'backups',
        'controllers',
        'database',
        'database/migrations',
        'docs',
        'logs',
        'temp',
        'tests',
        'ui',
        'utils'
    ]
    
    # Create required directories if they don't exist
    for directory in required_dirs:
        dir_path = os.path.join(root_dir, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created missing directory: {directory}")
    
    # File type mappings
    file_mappings = {
        'tests': ['.py', '.bat'] if any(f.startswith('test_') for f in os.listdir(root_dir)) else [],
        'docs': ['.md', '.txt'] if any(f.endswith('.md') for f in os.listdir(root_dir)) else [],
        'utils': ['.py', '.bat'] if any(f.startswith('fix_') or f.startswith('check_') for f in os.listdir(root_dir)) else []
    }
    
    # Move misplaced files
    for directory, extensions in file_mappings.items():
        if not extensions:
            continue
            
        for file in os.listdir(root_dir):
            file_path = os.path.join(root_dir, file)
            
            # Skip directories and specific files
            if os.path.isdir(file_path) or file in ['main.py', 'models.py', '__init__.py', 'requirements.txt', 'organize_project.py', 'maintain_project.py']:
                continue
                
            # Check if the file should be moved
            file_ext = os.path.splitext(file)[1]
            
            if directory == 'tests' and file.startswith('test_') and file_ext in extensions:
                dest_path = os.path.join(root_dir, directory, file)
                if not os.path.exists(dest_path):
                    shutil.move(file_path, dest_path)
                    print(f"Moved {file} to {directory} directory")
                    
            elif directory == 'docs' and file_ext in extensions and not file.startswith('test_'):
                dest_path = os.path.join(root_dir, directory, file)
                if not os.path.exists(dest_path):
                    shutil.move(file_path, dest_path)
                    print(f"Moved {file} to {directory} directory")
                    
            elif directory == 'utils' and (file.startswith('fix_') or file.startswith('check_')) and file_ext in extensions:
                dest_path = os.path.join(root_dir, directory, file)
                if not os.path.exists(dest_path):
                    shutil.move(file_path, dest_path)
                    print(f"Moved {file} to {directory} directory")
    
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
    
    # Clean up temp directory - delete files older than 7 days
    temp_dir = os.path.join(root_dir, 'temp')
    if os.path.exists(temp_dir):
        current_time = datetime.now().timestamp()
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                # 7 days in seconds = 7 * 24 * 60 * 60 = 604800
                if file_age > 604800:
                    os.remove(file_path)
                    print(f"Deleted old temporary file: {file}")
    
    print("\nProject structure maintenance completed!")
    
    # Generate a report
    report_path = os.path.join(root_dir, 'docs', 'project_structure_report.txt')
    with open(report_path, 'w') as f:
        f.write(f"Project Structure Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        # Count files by type
        file_counts = {}
        for root, dirs, files in os.walk(root_dir):
            rel_path = os.path.relpath(root, root_dir)
            if rel_path == '.':
                rel_path = 'root'
                
            file_counts[rel_path] = len(files)
            
            # Count by extension
            extensions = {}
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
            
            if extensions:
                f.write(f"{rel_path}: {len(files)} files\n")
                for ext, count in extensions.items():
                    f.write(f"  - {ext}: {count} files\n")
                f.write("\n")
        
        f.write("\nSummary:\n")
        f.write("=" * 80 + "\n")
        total_files = sum(file_counts.values())
        f.write(f"Total files: {total_files}\n")
        for directory, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                f.write(f"{directory}: {count} files ({count/total_files*100:.1f}%)\n")
    
    print(f"Project structure report generated: {report_path}")

if __name__ == "__main__":
    maintain_project_structure()
