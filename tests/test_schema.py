import os
import sqlite3
from datetime import datetime, timedelta
from database.database import Database

def test_database_schema():
    """Test that all required tables exist in the database"""
    print("Testing database schema...")
    
    # Create a fresh test database
    db_path = "schema_test.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize database with schema
    db = Database(db_path)
    
    # List of tables to check
    required_tables = [
        'users', 'employees', 'departments', 'positions', 'shifts',
        'attendance_records', 'pay_grades', 'tax_brackets',
        'employee_benefits', 'deductions', 'salary_structures',
        'salaries', 'salary_payments', 'payroll_entries'
    ]
    
    # Connect directly to database to query schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Check each required table
    missing_tables = []
    for table in required_tables:
        if table not in tables:
            missing_tables.append(table)
            print(f"✗ Missing table: {table}")
        else:
            print(f"✓ Table exists: {table}")
    
    # Close connection
    conn.close()
    
    # Clean up
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except:
            print("Note: Could not remove test database file")
    
    # Return results
    if missing_tables:
        print(f"\n❌ Schema test failed: Missing {len(missing_tables)} tables")
        return False
    else:
        print("\n✅ Schema test passed: All required tables exist")
        return True

def test_table_creation_order():
    """Test that tables are created in the correct order to respect foreign key constraints"""
    print("\nTesting table creation order...")
    
    # Get the Database class and inspect the create_tables method
    db = Database(":memory:")  # Use in-memory database
    
    # Get the table_order from the create_tables method
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Define some key dependencies
    dependencies = {
        'positions': ['departments'],
        'employees': ['departments', 'positions', 'shifts'],
        'attendance_records': ['employees', 'shifts'],
        'employee_salary_structure': ['employees', 'salary_structures'],
        'payroll_entries': ['employees', 'payroll_periods']
    }
    
    # Get the actual table creation order from the database.py file
    try:
        # Open the database.py file and extract the table_order list
        with open("database/database.py", "r") as f:
            content = f.read()
            
        # Find the table_order list in the create_tables method
        start_index = content.find("table_order = [")
        if start_index == -1:
            print("❌ Could not find table_order list in database.py")
            return False
            
        # Extract the list
        end_index = content.find("]", start_index)
        table_order_str = content[start_index:end_index+1]
        
        # Convert to a Python list
        table_order = []
        for line in table_order_str.split("\n"):
            if "'" in line:
                table_name = line.split("'")[1]
                table_order.append(table_name)
        
        print(f"Found table creation order: {table_order}")
        
        # Check each dependency
        all_passed = True
        for table, depends_on in dependencies.items():
            if table not in table_order:
                print(f"✗ Table '{table}' is not in the table_order list")
                all_passed = False
                continue
                
            table_index = table_order.index(table)
            
            for dependency in depends_on:
                if dependency not in table_order:
                    print(f"✗ Dependency '{dependency}' for '{table}' is not in the table_order list")
                    all_passed = False
                    continue
                    
                dependency_index = table_order.index(dependency)
                
                if dependency_index > table_index:
                    print(f"✗ Table '{table}' is created before its dependency '{dependency}'")
                    all_passed = False
                else:
                    print(f"✓ Table '{table}' is correctly created after '{dependency}'")
        
        if all_passed:
            print("\n✅ Table creation order test passed")
            return True
        else:
            print("\n❌ Table creation order test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error analyzing table creation order: {str(e)}")
        return False

def run_tests():
    """Run all tests"""
    print("=== STARTING SCHEMA VALIDATION TESTS ===\n")
    
    # Run tests
    schema_test_passed = test_database_schema()
    order_test_passed = test_table_creation_order()
    
    # Report overall results
    print("\n=== TEST RESULTS ===")
    if schema_test_passed and order_test_passed:
        print("✅ All schema validation tests passed!")
        return True
    else:
        print("❌ Some schema validation tests failed")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
