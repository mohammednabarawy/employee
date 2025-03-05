import sys
import os
import sqlite3
from datetime import datetime, timedelta
import random
from PyQt5.QtWidgets import QApplication
from database.database import Database
from controllers.salary_controller import SalaryController
from controllers.attendance_controller import AttendanceController
from controllers.employee_controller import EmployeeController

class SalaryAttendanceTest:
    def __init__(self, db_path="test_employee.db"):
        self.db_path = db_path
        self.db = Database(db_path)
        self.salary_controller = SalaryController(self.db)
        self.attendance_controller = AttendanceController(self.db)
        self.employee_controller = EmployeeController(self.db)
        
        # Ensure we have a clean test database
        if os.path.exists(db_path):
            os.remove(db_path)
        
        # Initialize database with schema
        self.db.create_tables()
        
        # Test results
        self.results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
    def setup_test_data(self):
        """Create test data for our tests"""
        print("Setting up test data...")
        
        # Create a test user
        self.db.execute_query("""
            INSERT INTO users (username, password, email, full_name, role)
            VALUES ('testadmin', 'password123', 'admin@test.com', 'Test Admin', 'admin')
        """)
        
        # Get the user ID
        user_result = self.db.fetch_query("SELECT last_insert_rowid()")
        self.user_id = user_result[0][0]
        
        # Create departments
        self.db.execute_query("INSERT INTO departments (name) VALUES ('IT')")
        self.db.execute_query("INSERT INTO departments (name) VALUES ('HR')")
        
        # Create positions
        self.db.execute_query("INSERT INTO positions (name, department_id) VALUES ('Developer', 1)")
        self.db.execute_query("INSERT INTO positions (name, department_id) VALUES ('HR Manager', 2)")
        
        # Create shifts
        self.db.execute_query("""
            INSERT INTO shifts (shift_name, start_time, end_time, max_regular_hours)
            VALUES ('Day Shift', '09:00', '17:00', 8)
        """)
        
        # Get the shift ID
        shift_result = self.db.fetch_query("SELECT last_insert_rowid()")
        shift_id = shift_result[0][0]
        
        # Create employees with code field
        self.db.execute_query(f"""
            INSERT INTO employees (name, email, phone, department_id, position_id, hire_date, code, shift_id)
            VALUES ('John Doe', 'john@example.com', '1234567890', 1, 1, '2023-01-01', 'EMP001', {shift_id})
        """)
        
        # Get the employee ID
        employee_result = self.db.fetch_query("SELECT last_insert_rowid()")
        self.employee_id = employee_result[0][0]
        
        # Create salary structure
        self.db.execute_query("""
            INSERT INTO salary_structures (structure_name, base_percentage, allowance_percentage, bonus_percentage)
            VALUES ('Standard', 70, 20, 10)
        """)
        
        # Get the structure ID
        structure_result = self.db.fetch_query("SELECT last_insert_rowid()")
        self.structure_id = structure_result[0][0]
        
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
        
        # Get the payroll period ID
        period_result = self.db.fetch_query("SELECT last_insert_rowid()")
        self.period_id = period_result[0][0]
        
        # Assign salary structure to employee
        self.db.execute_query(f"""
            INSERT INTO employee_salary_structure (employee_id, structure_id, effective_date)
            VALUES ({self.employee_id}, {self.structure_id}, '2023-01-01')
        """)
        
        # Assign salary
        self.db.execute_query(f"""
            INSERT INTO salaries (employee_id, base_salary, allowances, bonuses, deductions, total_salary, effective_date)
            VALUES ({self.employee_id}, 5000, 1000, 500, 0, 6500, '2023-01-01')
        """)
        
        # Create tax brackets
        tax_brackets = [
            (2025, 0, 1000, 0.0),
            (2025, 1000, 5000, 0.1),
            (2025, 5000, 10000, 0.2),
            (2025, 10000, None, 0.3)
        ]
        for year, min_income, max_income, rate in tax_brackets:
            max_val = f"'{max_income}'" if max_income is not None else "NULL"
            self.db.execute_query(f"""
                INSERT INTO tax_brackets (tax_year, min_income, max_income, rate)
                VALUES ({year}, {min_income}, {max_val}, {rate})
            """)
        
        # Add employee benefits
        self.db.execute_query(f"""
            INSERT INTO employee_benefits (employee_id, benefit_type, amount, is_percentage, start_date)
            VALUES ({self.employee_id}, 'Health Insurance', 200, 0, '2023-01-01')
        """)
        
        # Add employee deductions
        self.db.execute_query(f"""
            INSERT INTO deductions (employee_id, deduction_type, amount, is_percentage, recurring, start_date)
            VALUES ({self.employee_id}, 'Income Tax', 15, 1, 1, '2023-01-01')
        """)
        
        print("Test data setup complete!")
        
    def test_database_schema(self):
        """Test that all required tables and columns exist"""
        print("\nTesting database schema...")
        
        required_tables = [
            'attendance_records', 'shifts', 'pay_grades', 'tax_brackets',
            'employee_benefits', 'deductions', 'payslip_templates',
            'salary_structures', 'employee_salary_structure'
        ]
        
        # Check tables exist
        for table in required_tables:
            try:
                self.db.execute_query(f"SELECT 1 FROM {table} LIMIT 1")
                print(f"✓ Table '{table}' exists")
                self.results["passed"] += 1
            except Exception as e:
                print(f"✗ Table '{table}' missing: {str(e)}")
                self.results["failed"] += 1
                self.results["errors"].append(f"Missing table: {table}")
        
        # Check specific columns
        column_checks = [
            ('attendance_records', 'check_in'),
            ('attendance_records', 'check_out'),
            ('attendance_records', 'total_hours'),
            ('attendance_records', 'status'),
            ('shifts', 'shift_name'),
            ('shifts', 'start_time'),
            ('shifts', 'end_time'),
            ('tax_brackets', 'tax_year'),
            ('tax_brackets', 'min_income'),
            ('tax_brackets', 'max_income'),
            ('tax_brackets', 'rate')
        ]
        
        for table, column in column_checks:
            try:
                self.db.execute_query(f"SELECT {column} FROM {table} LIMIT 1")
                print(f"✓ Column '{column}' exists in '{table}'")
                self.results["passed"] += 1
            except Exception as e:
                print(f"✗ Column '{column}' missing from '{table}': {str(e)}")
                self.results["failed"] += 1
                self.results["errors"].append(f"Missing column: {column} in {table}")
                
    def test_attendance_system(self):
        """Test attendance system functionality"""
        print("\nTesting attendance system...")
        
        # Test check-in
        try:
            self.attendance_controller.record_check_in(self.employee_id)
            print("✓ Check-in successful")
            self.results["passed"] += 1
            
            # Verify record exists
            query = f"""
                SELECT * FROM attendance_records 
                WHERE employee_id = {self.employee_id} 
                AND DATE(check_in) = DATE('now')
            """
            result = self.db.fetch_query(query)
            
            if result and len(result) > 0:
                print("✓ Attendance record created")
                self.results["passed"] += 1
            else:
                print("✗ Attendance record not found")
                self.results["failed"] += 1
                self.results["errors"].append("Attendance record not created after check-in")
                
            # Test duplicate check-in
            try:
                self.attendance_controller.record_check_in(self.employee_id)
                print("✗ Duplicate check-in should fail")
                self.results["failed"] += 1
                self.results["errors"].append("Duplicate check-in was allowed")
            except Exception as e:
                print("✓ Duplicate check-in rejected correctly")
                self.results["passed"] += 1
                
            # Test check-out
            try:
                self.attendance_controller.record_check_out(self.employee_id)
                print("✓ Check-out successful")
                self.results["passed"] += 1
                
                # Verify check-out recorded
                query = f"""
                    SELECT * FROM attendance_records 
                    WHERE employee_id = {self.employee_id} 
                    AND DATE(check_in) = DATE('now')
                    AND check_out IS NOT NULL
                """
                result = self.db.fetch_query(query)
                
                if result and len(result) > 0:
                    print("✓ Check-out time recorded")
                    self.results["passed"] += 1
                else:
                    print("✗ Check-out time not recorded")
                    self.results["failed"] += 1
                    self.results["errors"].append("Check-out time not recorded")
                    
            except Exception as e:
                print(f"✗ Check-out failed: {str(e)}")
                self.results["failed"] += 1
                self.results["errors"].append(f"Check-out failed: {str(e)}")
                
        except Exception as e:
            print(f"✗ Check-in failed: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Check-in failed: {str(e)}")
            
    def test_salary_calculation(self):
        """Test salary calculation with attendance integration"""
        print("\nTesting salary calculation...")
        
        # Create attendance records for a period
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        
        # Clear any existing records
        self.db.execute_query(f"DELETE FROM attendance_records WHERE employee_id = {self.employee_id}")
        
        # Create 20 attendance records (workdays in a month)
        current_date = start_date
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday to Friday
                check_in = current_date.replace(hour=9, minute=0, second=0)
                
                # Randomize hours worked (7-9 hours)
                hours_worked = random.uniform(7, 9)
                check_out = check_in + timedelta(hours=hours_worked)
                
                # Determine status
                status = "present"
                if check_in.hour > 9 or check_in.minute > 15:  # Late if after 9:15
                    status = "late"
                
                self.db.execute_query(f"""
                    INSERT INTO attendance_records (
                        employee_id, check_in, check_out, status
                    ) VALUES (
                        {self.employee_id}, 
                        '{check_in.strftime('%Y-%m-%d %H:%M:%S')}', 
                        '{check_out.strftime('%Y-%m-%d %H:%M:%S')}',
                        '{status}'
                    )
                """)
            
            current_date += timedelta(days=1)
        
        # Test salary calculation
        try:
            period_start = start_date.strftime('%Y-%m-%d')
            period_end = end_date.strftime('%Y-%m-%d')
            
            salary_data = self.salary_controller.calculate_salary(
                self.employee_id, period_start, period_end
            )
            
            print("✓ Salary calculation successful")
            self.results["passed"] += 1
            
            # Verify salary components
            if 'base_salary' in salary_data and salary_data['base_salary'] > 0:
                print("✓ Base salary calculated")
                self.results["passed"] += 1
            else:
                print("✗ Base salary not calculated")
                self.results["failed"] += 1
                self.results["errors"].append("Base salary not calculated")
                
            if 'attendance' in salary_data and len(salary_data['attendance']) > 0:
                print(f"✓ Attendance data integrated ({len(salary_data['attendance'])} records)")
                self.results["passed"] += 1
            else:
                print("✗ Attendance data not integrated")
                self.results["failed"] += 1
                self.results["errors"].append("Attendance data not integrated in salary calculation")
                
            # Check for overtime calculation
            if 'overtime_pay' in salary_data:
                print(f"✓ Overtime calculated: ${salary_data['overtime_pay']:.2f}")
                self.results["passed"] += 1
            else:
                print("✗ Overtime not calculated")
                self.results["failed"] += 1
                self.results["errors"].append("Overtime not calculated")
                
            # Check for benefits
            if 'benefits' in salary_data and salary_data['benefits']['total_benefits'] > 0:
                print(f"✓ Benefits calculated: ${salary_data['benefits']['total_benefits']:.2f}")
                self.results["passed"] += 1
            else:
                print("✗ Benefits not calculated")
                self.results["failed"] += 1
                self.results["errors"].append("Benefits not calculated")
                
            # Check for deductions
            if 'deductions' in salary_data and salary_data['deductions']['total_deductions'] > 0:
                print(f"✓ Deductions calculated: ${salary_data['deductions']['total_deductions']:.2f}")
                self.results["passed"] += 1
            else:
                print("✗ Deductions not calculated")
                self.results["failed"] += 1
                self.results["errors"].append("Deductions not calculated")
                
            # Check for tax calculation
            if 'tax_deductions' in salary_data and salary_data['tax_deductions'] > 0:
                print(f"✓ Tax calculated: ${salary_data['tax_deductions']:.2f}")
                self.results["passed"] += 1
            else:
                print("✗ Tax not calculated")
                self.results["failed"] += 1
                self.results["errors"].append("Tax not calculated")
                
            # Check for net salary
            if 'net_salary' in salary_data and salary_data['net_salary'] > 0:
                print(f"✓ Net salary calculated: ${salary_data['net_salary']:.2f}")
                self.results["passed"] += 1
            else:
                print("✗ Net salary not calculated")
                self.results["failed"] += 1
                self.results["errors"].append("Net salary not calculated")
                
        except Exception as e:
            print(f"✗ Salary calculation failed: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Salary calculation failed: {str(e)}")
            
    def test_payslip_generation(self):
        """Test payslip generation"""
        print("\nTesting payslip generation...")
        
        try:
            period_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            period_end = datetime.now().strftime('%Y-%m-%d')
            
            payslip = self.salary_controller.generate_payslip(
                self.employee_id, period_start, period_end
            )
            
            print("✓ Payslip generated successfully")
            self.results["passed"] += 1
            
            # Check payslip components
            required_fields = [
                'employee_name', 'employee_id', 'department', 'position',
                'pay_period', 'payment_date', 'salary_components', 'ytd_totals'
            ]
            
            for field in required_fields:
                if field in payslip:
                    print(f"✓ Payslip contains {field}")
                    self.results["passed"] += 1
                else:
                    print(f"✗ Payslip missing {field}")
                    self.results["failed"] += 1
                    self.results["errors"].append(f"Payslip missing {field}")
            
            # Check payslip saved to database
            query = f"""
                SELECT * FROM payroll_entries
                WHERE employee_id = {self.employee_id}
                AND period_start = '{period_start}'
                AND period_end = '{period_end}'
            """
            result = self.db.fetch_query(query)
            
            if result and len(result) > 0:
                print("✓ Payslip saved to database")
                self.results["passed"] += 1
            else:
                print("✗ Payslip not saved to database")
                self.results["failed"] += 1
                self.results["errors"].append("Payslip not saved to database")
                
        except Exception as e:
            print(f"✗ Payslip generation failed: {str(e)}")
            self.results["failed"] += 1
            self.results["errors"].append(f"Payslip generation failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests and report results"""
        print("Starting salary and attendance system tests...")
        
        # Setup test data
        self.setup_test_data()
        
        # Run tests
        self.test_database_schema()
        self.test_attendance_system()
        self.test_salary_calculation()
        self.test_payslip_generation()
        
        # Report results
        print("\n=== TEST RESULTS ===")
        print(f"Tests passed: {self.results['passed']}")
        print(f"Tests failed: {self.results['failed']}")
        
        if self.results["failed"] > 0:
            print("\nErrors:")
            for error in self.results["errors"]:
                print(f"- {error}")
        
        if self.results["failed"] == 0:
            print("\nAll tests passed! The salary management and attendance systems are working correctly.")
        else:
            print(f"\nSome tests failed. Please review the {len(self.results['errors'])} errors above.")
        
        # Clean up test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        return self.results["failed"] == 0

if __name__ == "__main__":
    # Create QApplication instance for any UI components that might be used
    app = QApplication(sys.argv)
    
    # Run tests
    tester = SalaryAttendanceTest()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
