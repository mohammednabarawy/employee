import os
import sqlite3
from datetime import datetime, timedelta
from database.database import Database
from controllers.salary_controller import SalaryController
from controllers.attendance_controller import AttendanceController

class SalaryAttendanceTester:
    def __init__(self):
        # Use a test database
        self.db_path = "test_salary_attendance_basic.db"
        
        # Ensure we have a clean test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Initialize database
        self.db = Database(self.db_path)
        
        # Initialize controllers
        self.salary_controller = SalaryController(self.db)
        self.attendance_controller = AttendanceController(self.db)
        
        # Test data
        self.user_id = None
        self.employee_id = None
        self.shift_id = None
        self.period_id = None
        
    def setup_test_data(self):
        """Set up test data for salary and attendance tests"""
        print("Setting up test data...")
        
        try:
            # Create a test user
            self.db.execute_query("""
                INSERT INTO users (username, password, email, full_name, role)
                VALUES ('testadmin', 'password123', 'admin@test.com', 'Test Admin', 'admin')
            """)
            
            # Get the user ID
            user_result = self.db.fetch_query("SELECT last_insert_rowid()")
            self.user_id = user_result[0][0]
            print(f"✓ Created test user with ID: {self.user_id}")
            
            # Create department
            self.db.execute_query("INSERT INTO departments (name) VALUES ('Test Department')")
            dept_id = self.db.fetch_query("SELECT last_insert_rowid()")[0][0]
            print(f"✓ Created department with ID: {dept_id}")
            
            # Create position
            self.db.execute_query(f"""
                INSERT INTO positions (name, department_id) 
                VALUES ('Test Position', {dept_id})
            """)
            pos_id = self.db.fetch_query("SELECT last_insert_rowid()")[0][0]
            print(f"✓ Created position with ID: {pos_id}")
            
            # Create shift
            self.db.execute_query("""
                INSERT INTO shifts (shift_name, start_time, end_time, max_regular_hours)
                VALUES ('Test Shift', '09:00', '17:00', 8)
            """)
            self.shift_id = self.db.fetch_query("SELECT last_insert_rowid()")[0][0]
            print(f"✓ Created shift with ID: {self.shift_id}")
            
            # Create employee
            self.db.execute_query(f"""
                INSERT INTO employees (
                    name, code, department_id, position_id, shift_id, hire_date
                ) VALUES (
                    'Test Employee', 'EMP-TEST', {dept_id}, {pos_id}, {self.shift_id}, '2023-01-01'
                )
            """)
            self.employee_id = self.db.fetch_query("SELECT last_insert_rowid()")[0][0]
            print(f"✓ Created employee with ID: {self.employee_id}")
            
            # Create payroll period
            current_year = datetime.now().year
            current_month = datetime.now().month
            self.db.execute_query(f"""
                INSERT INTO payroll_periods (
                    period_year, period_month, start_date, end_date, 
                    payment_date, status, created_by
                ) VALUES (
                    {current_year}, {current_month}, 
                    '{datetime.now().replace(day=1).strftime('%Y-%m-%d')}', 
                    '{datetime.now().strftime('%Y-%m-%d')}',
                    '{datetime.now().strftime('%Y-%m-%d')}', 
                    'draft', {self.user_id}
                )
            """)
            self.period_id = self.db.fetch_query("SELECT last_insert_rowid()")[0][0]
            print(f"✓ Created payroll period with ID: {self.period_id}")
            
            return True
        except Exception as e:
            print(f"✗ Error setting up test data: {str(e)}")
            return False
    
    def test_attendance_record(self):
        """Test attendance record functionality"""
        print("\nTesting attendance record functionality...")
        
        try:
            # Record check-in
            check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.db.execute_query(f"""
                INSERT INTO attendance_records (
                    employee_id, check_in, status, shift_id
                ) VALUES (
                    {self.employee_id}, '{check_in_time}', 'present', {self.shift_id}
                )
            """)
            
            # Verify record exists
            result = self.db.fetch_query(f"""
                SELECT * FROM attendance_records 
                WHERE employee_id = {self.employee_id}
            """)
            
            if result and len(result) > 0:
                print("✓ Attendance record created successfully")
                
                # Update with check-out time
                check_out_time = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
                self.db.execute_query(f"""
                    UPDATE attendance_records 
                    SET check_out = '{check_out_time}', 
                        total_hours = 8.0
                    WHERE employee_id = {self.employee_id}
                """)
                
                # Verify check-out recorded
                result = self.db.fetch_query(f"""
                    SELECT * FROM attendance_records 
                    WHERE employee_id = {self.employee_id} 
                    AND check_out IS NOT NULL
                """)
                
                if result and len(result) > 0:
                    print("✓ Check-out time recorded successfully")
                    return True
                else:
                    print("✗ Failed to record check-out time")
                    return False
            else:
                print("✗ Failed to create attendance record")
                return False
                
        except Exception as e:
            print(f"✗ Attendance test failed: {str(e)}")
            return False
    
    def test_salary_record(self):
        """Test salary record functionality"""
        print("\nTesting salary record functionality...")
        
        try:
            # Create salary record
            self.db.execute_query(f"""
                INSERT INTO salaries (
                    employee_id, base_salary, allowances, bonuses, deductions, total_salary, effective_date
                ) VALUES (
                    {self.employee_id}, 5000, 1000, 500, 0, 6500, '2023-01-01'
                )
            """)
            
            # Verify record exists
            result = self.db.fetch_query(f"""
                SELECT * FROM salaries 
                WHERE employee_id = {self.employee_id}
            """)
            
            if result and len(result) > 0:
                print("✓ Salary record created successfully")
                
                # Create payroll entry
                self.db.execute_query(f"""
                    INSERT INTO payroll_entries (
                        payroll_period_id, employee_id, basic_salary, 
                        total_allowances, total_deductions, net_salary,
                        gross_salary, payment_date, payment_status
                    ) VALUES (
                        {self.period_id}, {self.employee_id}, 5000,
                        1000, 0, 6500,
                        6500, '{datetime.now().strftime('%Y-%m-%d')}', 'pending'
                    )
                """)
                
                # Verify payroll entry
                result = self.db.fetch_query(f"""
                    SELECT * FROM payroll_entries 
                    WHERE employee_id = {self.employee_id}
                """)
                
                if result and len(result) > 0:
                    print("✓ Payroll entry created successfully")
                    return True
                else:
                    print("✗ Failed to create payroll entry")
                    return False
            else:
                print("✗ Failed to create salary record")
                return False
                
        except Exception as e:
            print(f"✗ Salary test failed: {str(e)}")
            return False
    
    def run_tests(self):
        """Run all tests"""
        print("=== STARTING BASIC SALARY AND ATTENDANCE TESTS ===\n")
        
        # Set up test data
        if not self.setup_test_data():
            print("❌ Failed to set up test data, aborting tests")
            return False
        
        # Run tests
        attendance_test_passed = self.test_attendance_record()
        salary_test_passed = self.test_salary_record()
        
        # Report results
        print("\n=== TEST RESULTS ===")
        print(f"Attendance test: {'✅ Passed' if attendance_test_passed else '❌ Failed'}")
        print(f"Salary test: {'✅ Passed' if salary_test_passed else '❌ Failed'}")
        
        if attendance_test_passed and salary_test_passed:
            print("\n✅ All basic salary and attendance tests passed!")
            return True
        else:
            print("\n❌ Some tests failed. Please review the errors above.")
            return False
        
    def cleanup(self):
        """Clean up test database"""
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print("✓ Test database removed")
        except Exception as e:
            print(f"✗ Failed to remove test database: {str(e)}")

if __name__ == "__main__":
    tester = SalaryAttendanceTester()
    try:
        success = tester.run_tests()
        exit(0 if success else 1)
    finally:
        tester.cleanup()
