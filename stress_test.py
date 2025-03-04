#!/usr/bin/env python
"""
Stress Test Script for Employee Management System
This script performs comprehensive tests to identify potential issues in the application.
"""

import os
import sys
import time
import random
import string
import sqlite3
import threading
import traceback
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QDate

# Import application components
from database.database import Database
from controllers.employee_controller import EmployeeController
from controllers.payroll_controller import PayrollController
from controllers.auth_controller import AuthController
from controllers.salary_controller import SalaryController
from controllers.report_controller import ReportController
from utils.validation import ValidationUtils

class StressTestLogger:
    """Logger for stress test results"""
    
    def __init__(self, log_file="stress_test_results.log"):
        self.log_file = log_file
        # Create or clear the log file
        with open(self.log_file, 'w') as f:
            f.write(f"Stress Test Started at {datetime.now()}\n")
            f.write("="*80 + "\n\n")
    
    def log(self, message, error=False):
        """Log a message to the log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = "[ERROR]" if error else "[INFO]"
        with open(self.log_file, 'a') as f:
            f.write(f"{timestamp} {prefix} {message}\n")
        
        # Also print to console
        print(f"{timestamp} {prefix} {message}")
    
    def log_exception(self, message, exception):
        """Log an exception with traceback"""
        self.log(f"{message}: {str(exception)}", error=True)
        with open(self.log_file, 'a') as f:
            f.write(traceback.format_exc() + "\n")

class StressTest(QObject):
    """Main stress test class"""
    
    test_completed = pyqtSignal(bool, str)
    
    def __init__(self, test_db_file="stress_test.db"):
        super().__init__()
        self.logger = StressTestLogger()
        self.test_db_file = test_db_file
        
        # Remove test database if it exists
        if os.path.exists(test_db_file):
            os.remove(test_db_file)
        
        # Initialize database and controllers
        self.db = Database(test_db_file)
        self.employee_controller = EmployeeController(self.db)
        self.payroll_controller = PayrollController(self.db)
        self.auth_controller = AuthController(self.db)
        self.salary_controller = SalaryController(self.db)
        self.report_controller = ReportController(self.db)
        
        # Ensure all required tables are created
        self.ensure_tables_exist()
        
        # Test data
        self.test_employees = []
        self.test_departments = []
        self.test_positions = []
        
        # Test counters
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
    
    def ensure_tables_exist(self):
        """Ensure all required tables exist in the database"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if salaries table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='salaries'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE salaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id INTEGER NOT NULL,
                        base_salary REAL NOT NULL,
                        bonuses REAL DEFAULT 0,
                        deductions REAL DEFAULT 0,
                        overtime_pay REAL DEFAULT 0,
                        total_salary REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (employee_id) REFERENCES employees(id)
                    )
                """)
            
            # Check if salary_payments table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='salary_payments'")
            if not cursor.fetchone():
                cursor.execute("""
                    CREATE TABLE salary_payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id INTEGER NOT NULL,
                        amount_paid REAL NOT NULL,
                        payment_date DATE NOT NULL,
                        payment_mode TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (employee_id) REFERENCES employees(id)
                    )
                """)
            
            # Check if payroll_entries table exists and has required columns
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payroll_entries'")
            if cursor.fetchone():
                # Check if gross_salary column exists
                cursor.execute("PRAGMA table_info(payroll_entries)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'gross_salary' not in columns:
                    cursor.execute("ALTER TABLE payroll_entries ADD COLUMN gross_salary REAL DEFAULT 0")
                    cursor.execute("UPDATE payroll_entries SET gross_salary = basic_salary + total_allowances")
                
                if 'payment_date' not in columns:
                    cursor.execute("ALTER TABLE payroll_entries ADD COLUMN payment_date DATE")
                    cursor.execute("UPDATE payroll_entries SET payment_date = date('now')")
            
            conn.commit()
        except Exception as e:
            self.logger.log_exception("Error ensuring tables exist", e)
        finally:
            conn.close()
    
    def run_all_tests(self):
        """Run all stress tests"""
        try:
            self.logger.log("Starting stress tests...")
            
            # Database tests
            self.test_database_connection()
            self.test_database_concurrent_access()
            
            # Data validation tests
            self.test_employee_validation()
            self.test_salary_validation()
            
            # Employee operations tests
            self.test_employee_crud()
            self.test_bulk_employee_operations()
            
            # Payroll tests
            self.test_payroll_generation()
            self.test_payroll_edge_cases()
            
            # Authentication tests
            self.test_authentication()
            
            # Salary operations tests
            self.test_salary_operations()
            
            # Reporting tests
            self.test_reporting()
            
            # Report test results
            success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
            self.logger.log(f"Stress tests completed. Success rate: {success_rate:.2f}%")
            self.logger.log(f"Tests run: {self.tests_run}, Passed: {self.tests_passed}, Failed: {self.tests_failed}")
            
            self.test_completed.emit(True, f"Stress tests completed. Success rate: {success_rate:.2f}%")
            
        except Exception as e:
            self.logger.log_exception("Error running stress tests", e)
            self.test_completed.emit(False, f"Stress tests failed: {str(e)}")
    
    def assert_test(self, condition, test_name, message=""):
        """Assert a test condition and log the result"""
        self.tests_run += 1
        
        if condition:
            self.tests_passed += 1
            self.logger.log(f"PASSED: {test_name}")
            return True
        else:
            self.tests_failed += 1
            self.logger.log(f"FAILED: {test_name} - {message}", error=True)
            return False
    
    def test_database_connection(self):
        """Test database connection reliability"""
        self.logger.log("Testing database connection reliability...")
        
        # Test connection creation and closing
        for i in range(100):
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()
                
                self.assert_test(result[0] == 1, 
                                f"Database connection test #{i+1}")
            except Exception as e:
                self.assert_test(False, 
                                f"Database connection test #{i+1}", 
                                str(e))
    
    def test_database_concurrent_access(self):
        """Test concurrent database access"""
        self.logger.log("Testing concurrent database access...")
        
        def db_operation(thread_id):
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                
                # Perform a simple query
                cursor.execute("SELECT COUNT(*) FROM departments")
                result = cursor.fetchone()
                
                # Simulate some work
                time.sleep(0.01)
                
                conn.close()
                return True
            except Exception as e:
                self.logger.log_exception(f"Thread {thread_id} error", e)
                return False
        
        # Create and start multiple threads
        threads = []
        results = [False] * 20
        
        for i in range(20):
            thread = threading.Thread(target=lambda idx=i: results.__setitem__(idx, db_operation(idx)))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        self.assert_test(all(results), 
                        "Concurrent database access", 
                        f"{results.count(False)} threads failed")
    
    def test_employee_validation(self):
        """Test employee data validation"""
        self.logger.log("Testing employee data validation...")
        
        # Test valid employee data
        valid_employee = {
            'name': 'John Doe',
            'name_ar': 'جون دو',
            'hire_date': '2023-01-01',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'email': 'john.doe@example.com',
            'phone': '1234567890',
            'national_id': '1234567890',
            'basic_salary': 5000
        }
        
        result, message = ValidationUtils.validate_employee_data(valid_employee)
        self.assert_test(result, 
                        "Valid employee validation", 
                        message if not result else "")
        
        # Test invalid email
        invalid_email = valid_employee.copy()
        invalid_email['email'] = 'invalid-email'
        result, message = ValidationUtils.validate_employee_data(invalid_email)
        self.assert_test(not result, 
                        "Invalid email validation", 
                        "Validation should fail for invalid email")
        
        # Test invalid phone
        invalid_phone = valid_employee.copy()
        invalid_phone['phone'] = 'abc'
        result, message = ValidationUtils.validate_employee_data(invalid_phone)
        self.assert_test(not result, 
                        "Invalid phone validation", 
                        "Validation should fail for invalid phone")
        
        # Test missing required fields
        missing_required = {
            'email': 'john.doe@example.com'
        }
        result, message = ValidationUtils.validate_employee_data(missing_required)
        self.assert_test(not result, 
                        "Missing required fields validation", 
                        "Validation should fail for missing required fields")
        
        # Test Arabic numerals in phone
        arabic_phone = valid_employee.copy()
        arabic_phone['phone'] = '١٢٣٤٥٦٧٨٩٠'
        result, message = ValidationUtils.validate_employee_data(arabic_phone)
        self.assert_test(result, 
                        "Arabic numerals in phone validation", 
                        message if not result else "")
    
    def test_salary_validation(self):
        """Test salary data validation"""
        self.logger.log("Testing salary data validation...")
        
        # Test valid salary
        valid_salary = {
            'employee_id': 1,
            'basic_salary': 5000,
            'payment_date': '2023-01-01',
            'payment_method': 'Bank Transfer',
            'payment_status': 'Paid'
        }
        
        result, message = ValidationUtils.validate_salary_data(valid_salary)
        self.assert_test(result, 
                        "Valid salary validation", 
                        message if not result else "")
        
        # Test negative salary
        negative_salary = valid_salary.copy()
        negative_salary['basic_salary'] = -100
        result, message = ValidationUtils.validate_salary_data(negative_salary)
        self.assert_test(not result, 
                        "Negative salary validation", 
                        "Validation should fail for negative salary")
        
        # Test invalid date
        invalid_date = valid_salary.copy()
        invalid_date['payment_date'] = '2023-13-01'
        result, message = ValidationUtils.validate_salary_data(invalid_date)
        self.assert_test(not result, 
                        "Invalid date validation", 
                        "Validation should fail for invalid date")
    
    def test_employee_crud(self):
        """Test employee CRUD operations"""
        self.logger.log("Testing employee CRUD operations...")
        
        # Test adding an employee
        employee_data = {
            'name': 'Test Employee',
            'name_ar': 'موظف اختبار',
            'hire_date': '2023-01-01',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'email': 'test.employee@example.com',
            'phone': '1234567890',
            'national_id': '1234567890',
            'basic_salary': 5000,
            'department_id': 1,
            'position_id': 1
        }
        
        success, result = self.employee_controller.add_employee(employee_data)
        
        self.assert_test(success, 
                        "Add employee", 
                        str(result) if not success else "")
        
        if success and isinstance(result, dict):
            employee_id = result['id']
            
            # Test getting the employee
            success, employee = self.employee_controller.get_employee(employee_id)
            self.assert_test(success and employee['name'] == 'Test Employee', 
                            "Get employee", 
                            str(employee) if not success else "")
            
            # Test updating the employee
            update_data = {
                'name': 'Updated Employee',
                'basic_salary': 6000
            }
            
            success, result = self.employee_controller.update_employee(employee_id, update_data)
            self.assert_test(success, 
                            "Update employee", 
                            str(result) if not success else "")
            
            # Verify update
            success, employee = self.employee_controller.get_employee(employee_id)
            self.assert_test(success and employee['name'] == 'Updated Employee' and employee['basic_salary'] == 6000, 
                            "Verify employee update", 
                            str(employee) if not success else "")
            
            # Test deleting the employee
            success, result = self.employee_controller.delete_employee(employee_id)
            self.assert_test(success, 
                            "Delete employee", 
                            str(result) if not success else "")
            
            # Verify deletion
            success, employee = self.employee_controller.get_employee(employee_id)
            self.assert_test(not success or (success and employee.get('is_active') == 0), 
                            "Verify employee deletion", 
                            "Employee should be inactive or not found")
    
    def test_bulk_employee_operations(self):
        """Test bulk employee operations"""
        self.logger.log("Testing bulk employee operations...")
        
        # Add multiple employees
        employees_to_add = 50
        added_employees = []
        
        for i in range(employees_to_add):
            employee_data = {
                'name': f'Bulk Employee {i}',
                'name_ar': f'موظف {i}',
                'hire_date': '2023-01-01',
                'birth_date': '1990-01-01',
                'gender': 'male' if i % 2 == 0 else 'female',
                'email': f'bulk.employee{i}@example.com',
                'phone': f'123456{i:04d}',
                'national_id': f'123456{i:04d}',
                'basic_salary': 5000 + (i * 100),
                'department_id': (i % 5) + 1,
                'position_id': (i % 5) + 1
            }
            
            success, result = self.employee_controller.add_employee(employee_data)
            
            if success and isinstance(result, dict):
                added_employees.append(result['id'])
        
        # Test getting all employees
        success, employees = self.employee_controller.get_all_employees()
        
        self.assert_test(success and len(employees) >= employees_to_add, 
                        "Get all employees", 
                        f"Expected at least {employees_to_add} employees, got {len(employees) if success else 0}")
        
        # Test filtering employees by department
        for dept_id in range(1, 6):
            success, dept_employees = self.employee_controller.get_employees_by_department(dept_id)
            
            expected_count = len([e for e in range(employees_to_add) if e % 5 + 1 == dept_id])
            self.assert_test(success, 
                            f"Filter employees by department {dept_id}", 
                            str(dept_employees) if not success else "")
    
    def test_payroll_generation(self):
        """Test payroll generation"""
        self.logger.log("Testing payroll generation...")
        
        # Create a payroll period
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        success, period_id = self.payroll_controller.create_payroll_period(current_year, current_month)
        
        self.assert_test(success, 
                        "Create payroll period", 
                        str(period_id) if not success else "")
        
        if success and isinstance(period_id, int):
            # Generate payroll
            success, entries = self.payroll_controller.generate_payroll(period_id)
            
            self.assert_test(success, 
                            "Generate payroll", 
                            str(entries) if not success else "")
            
            # Test payroll calculations
            if success and isinstance(entries, list):
                for entry in entries:
                    # Basic validation of payroll entry
                    basic_salary = entry.get('basic_salary', 0)
                    total_allowances = entry.get('total_allowances', 0)
                    total_deductions = entry.get('total_deductions', 0)
                    total_adjustments = entry.get('total_adjustments', 0)
                    net_salary = entry.get('net_salary', 0)
                    
                    expected_net = basic_salary + total_allowances - total_deductions + total_adjustments
                    
                    # Allow for small floating point differences
                    self.assert_test(abs(net_salary - expected_net) < 0.01, 
                                    f"Payroll calculation for employee {entry.get('employee_id')}", 
                                    f"Expected net salary {expected_net}, got {net_salary}")
    
    def test_payroll_edge_cases(self):
        """Test payroll edge cases"""
        self.logger.log("Testing payroll edge cases...")
        
        # Test with very large salary values
        employee_data = {
            'name': 'Large Salary Employee',
            'name_ar': 'موظف براتب كبير',
            'hire_date': '2023-01-01',
            'basic_salary': 9999999.99,  # Very large salary
            'department_id': 1,
            'position_id': 1
        }
        
        success, result = self.employee_controller.add_employee(employee_data)
        
        if success and isinstance(result, dict):
            employee_id = result['id']
            
            # Create a payroll period
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            success, period_id = self.payroll_controller.create_payroll_period(current_year, current_month)
            
            if success and isinstance(period_id, int):
                # Generate payroll
                success, entries = self.payroll_controller.generate_payroll(period_id)
                
                if success and isinstance(entries, list):
                    # Find our test employee
                    for entry in entries:
                        if entry.get('employee_id') == employee_id:
                            # Check if the large salary was handled correctly
                            self.assert_test(entry.get('basic_salary') == 9999999.99, 
                                            "Handle large salary values", 
                                            f"Expected 9999999.99, got {entry.get('basic_salary')}")
        
        # Test with zero salary
        employee_data = {
            'name': 'Zero Salary Employee',
            'name_ar': 'موظف بدون راتب',
            'hire_date': '2023-01-01',
            'basic_salary': 0,  # Zero salary
            'department_id': 1,
            'position_id': 1
        }
        
        success, result = self.employee_controller.add_employee(employee_data)
        
        if success and isinstance(result, dict):
            employee_id = result['id']
            
            # Generate payroll again
            success, entries = self.payroll_controller.generate_payroll(period_id)
            
            if success and isinstance(entries, list):
                # Find our test employee
                for entry in entries:
                    if entry.get('employee_id') == employee_id:
                        # Check if zero salary was handled correctly
                        self.assert_test(entry.get('net_salary') == 0, 
                                        "Handle zero salary", 
                                        f"Expected 0, got {entry.get('net_salary')}")
    
    def test_authentication(self):
        """Test user authentication functionality"""
        self.logger.log("Testing authentication system...")
        
        # Test user creation
        test_user = {
            'username': f'test_user_{random.randint(1000, 9999)}',
            'password': 'Test@123456',
            'email': f'test{random.randint(1000, 9999)}@example.com',
            'full_name': 'Test User',
            'role': 'hr'
        }
        
        success, result = self.auth_controller.create_user(
            test_user['username'],
            test_user['password'],
            test_user['email'],
            test_user['full_name'],
            test_user['role']
        )
        
        self.assert_test(success, 
                        "Create user", 
                        str(result) if not success else "")
        
        # Test login with valid credentials
        success, result = self.auth_controller.login(
            test_user['username'],
            test_user['password']
        )
        
        self.assert_test(success, 
                        "Login with valid credentials", 
                        str(result) if not success else "")
        
        # Test login with invalid password
        success, result = self.auth_controller.login(
            test_user['username'],
            'WrongPassword123'
        )
        
        self.assert_test(not success, 
                        "Reject login with invalid password", 
                        "Login should fail with wrong password")
        
        # Test login with non-existent user
        success, result = self.auth_controller.login(
            'nonexistent_user',
            'AnyPassword123'
        )
        
        self.assert_test(not success, 
                        "Reject login with non-existent user", 
                        "Login should fail with non-existent user")
        
        # Test logout
        if self.auth_controller.is_authenticated():
            self.auth_controller.logout()
            self.assert_test(not self.auth_controller.is_authenticated(), 
                            "Logout user", 
                            "User should be logged out")
    
    def test_salary_operations(self):
        """Test salary operations"""
        self.logger.log("Testing salary operations...")
        
        # Create a test employee
        employee_data = {
            'name': 'Salary Test Employee',
            'name_ar': 'موظف اختبار الراتب',
            'hire_date': '2023-01-01',
            'birth_date': '1990-01-01',
            'gender': 'male',
            'email': f'salary.test{random.randint(1000, 9999)}@example.com',
            'phone': f'555{random.randint(1000, 9999)}',
            'national_id': f'123{random.randint(10000, 99999)}',
            'basic_salary': 5000,
            'department_id': 1,
            'position_id': 1,
            'is_active': 1
        }
        
        success, result = self.employee_controller.add_employee(employee_data)
        
        if success and isinstance(result, dict):
            employee_id = result['id']
            
            # Ensure the employee exists in the database before proceeding
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if the employee was actually created
            cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
            if not cursor.fetchone():
                self.logger.log(f"Employee {employee_id} not found in database", error=True)
                conn.close()
                return
                
            # Create an initial salary record for the employee if needed
            cursor.execute("SELECT id FROM salaries WHERE employee_id = ?", (employee_id,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO salaries (
                        employee_id, base_salary, bonuses, deductions, overtime_pay, total_salary
                    ) VALUES (?, ?, 0, 0, 0, ?)
                """, (employee_id, employee_data['basic_salary'], employee_data['basic_salary']))
                conn.commit()
            
            conn.close()
            
            # Test updating salary
            salary_data = {
                'base_salary': 6000,
                'bonuses': 500,
                'deductions': 200,
                'overtime_pay': 300
            }
            
            success, result = self.salary_controller.update_salary(employee_id, salary_data)
            
            self.assert_test(success, 
                            "Update employee salary", 
                            str(result) if not success else "")
            
            # Test getting salary info
            success, salary_info = self.salary_controller.get_salary_info(employee_id)
            
            self.assert_test(success and salary_info.get('base_salary') == 6000, 
                            "Get salary information", 
                            str(salary_info) if not success else "")
            
            # Test processing a payment
            payment_data = {
                'employee_id': employee_id,
                'amount_paid': 6600,  # base + bonuses + overtime - deductions
                'payment_date': datetime.now().strftime('%Y-%m-%d'),
                'payment_mode': 'Bank Transfer'
            }
            
            success, payment_id = self.salary_controller.process_payment(payment_data)
            
            self.assert_test(success, 
                            "Process salary payment", 
                            str(payment_id) if not success else "")
            
            # Test getting payment history
            success, payments = self.salary_controller.get_payment_history(employee_id)
            
            self.assert_test(success and len(payments) > 0, 
                            "Get payment history", 
                            str(payments) if not success else "")
    
    def test_reporting(self):
        """Test reporting functionality"""
        self.logger.log("Testing reporting functionality...")
        
        # Test getting employee count
        success, count = self.report_controller.get_employee_count()
        
        self.assert_test(success, 
                        "Get employee count", 
                        str(count) if not success else "")
        
        # Test getting monthly payroll
        success, total = self.report_controller.get_monthly_payroll()
        
        self.assert_test(success, 
                        "Get monthly payroll total", 
                        str(total) if not success else "")
        
        # Test getting payroll distribution
        success, distribution = self.report_controller.get_payroll_distribution()
        
        self.assert_test(success, 
                        "Get payroll distribution", 
                        str(distribution) if not success else "")
        
        # Test generating payroll report
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        success, report = self.report_controller.generate_payroll_report(start_date, end_date)
        
        self.assert_test(success, 
                        "Generate payroll report", 
                        str(report) if not success else "")

def run_stress_tests():
    """Run the stress tests"""
    app = QApplication(sys.argv)
    
    # Create and run stress test
    stress_test = StressTest()
    
    # Connect signals
    stress_test.test_completed.connect(lambda success, message: app.quit())
    
    # Start tests after a short delay
    QTimer.singleShot(100, stress_test.run_all_tests)
    
    # Run the application event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_stress_tests()
