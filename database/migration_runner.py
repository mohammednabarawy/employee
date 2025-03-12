"""
Migration runner to handle database schema updates
"""
import os
import importlib.util
import traceback
import logging
import sys

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_migrations(db):
    """
    Run all migration scripts in the migrations directory
    
    Args:
        db: Database connection object
    
    Returns:
        list: List of (success, message) tuples for each migration
    """
    results = []
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    
    # Create migrations directory if it doesn't exist
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
        logging.info(f"Created migrations directory: {migrations_dir}")
        return results
    
    # Get all Python files in the migrations directory
    try:
        migration_files = [f for f in os.listdir(migrations_dir) 
                           if f.endswith('.py') and f != '__init__.py']
        
        # Sort files to ensure they run in the correct order
        migration_files.sort()
        
        logging.info(f"Found migration files: {migration_files}")
        
        # Run each migration
        for migration_file in migration_files:
            try:
                migration_path = os.path.join(migrations_dir, migration_file)
                logging.info(f"Processing migration: {migration_file}")
                
                # Load the module dynamically
                spec = importlib.util.spec_from_file_location(
                    f"migrations.{migration_file[:-3]}", 
                    migration_path
                )
                migration_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(migration_module)
                
                # Run the migration
                if hasattr(migration_module, 'run_migration'):
                    try:
                        success, message = migration_module.run_migration(db)
                        results.append((migration_file, success, message))
                        
                        if success:
                            logging.info(f"Migration {migration_file} successful: {message}")
                        else:
                            logging.warning(f"Migration {migration_file} failed: {message}")
                    except Exception as migration_error:
                        error_details = traceback.format_exc()
                        results.append((migration_file, False, f"Migration execution error: {str(migration_error)}\n{error_details}"))
                        logging.error(f"Migration {migration_file} execution error: {error_details}")
                else:
                    error_msg = "No run_migration function found"
                    results.append((migration_file, False, error_msg))
                    logging.error(f"Migration {migration_file}: {error_msg}")
            
            except Exception as e:
                error_details = traceback.format_exc()
                results.append((migration_file, False, f"Error: {str(e)}\n{error_details}"))
                logging.error(f"Error processing migration {migration_file}: {error_details}")
    
    except Exception as e:
        error_details = traceback.format_exc()
        results.append(("migration_runner", False, f"Error in migration runner: {str(e)}\n{error_details}"))
        logging.critical(f"Critical error in migration runner: {error_details}")
    
    return results
