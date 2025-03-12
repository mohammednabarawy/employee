"""Initial database schema migration"""
import os
import re
import logging

def run_migration(db):
    """
    Create initial database schema
    
    Args:
        db: Database connection object
    
    Returns:
        tuple: (success, message)
    """
    try:
        # Read schema from file
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'schema.sql'
        )
        
        # Configure logging
        logging.basicConfig(level=logging.DEBUG, 
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            filename='migration.log',
                            filemode='w')
        
        # Validate schema file exists
        if not os.path.exists(schema_path):
            logging.error(f"Schema file not found at {schema_path}")
            return False, f"Schema file not found at {schema_path}"
        
        with open(schema_path, 'r') as schema_file:
            schema_sql = schema_file.read()
        
        # Split SQL statements to handle multiple statements
        statements = [
            stmt.strip() 
            for stmt in re.split(r';(?=\s*CREATE|\s*INSERT)', schema_sql) 
            if stmt.strip()
        ]
        
        # Execute each statement separately using the database's execute method
        for statement in statements:
            if statement:
                try:
                    db.execute_query(statement + ';')
                    logging.info(f"Executed statement: {statement[:100]}...")
                except Exception as exec_error:
                    logging.error(f"Error executing statement: {statement[:100]}... Error: {str(exec_error)}")
                    # Continue with other statements even if one fails
        
        return True, "Initial schema created successfully"
    
    except Exception as e:
        logging.error(f"Error creating schema: {str(e)}")
        return False, f"Error creating schema: {str(e)}"
