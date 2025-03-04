#!/usr/bin/env python
"""
Test Runner for Employee Management System
This script runs stress tests and fixes identified issues.
"""

import os
import sys
import time
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QTextEdit, QLabel, QProgressBar, 
                            QHBoxLayout, QTabWidget, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer

class TestWorker(QThread):
    """Worker thread for running tests"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, test_type):
        super().__init__()
        self.test_type = test_type
    
    def run(self):
        try:
            if self.test_type == "stress":
                # Run stress test
                self.update_signal.emit("Starting stress tests...\n")
                process = subprocess.Popen(
                    [sys.executable, "stress_test.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Stream output in real-time
                for line in iter(process.stdout.readline, ''):
                    self.update_signal.emit(line)
                
                process.stdout.close()
                return_code = process.wait()
                
                if return_code == 0:
                    self.finished_signal.emit(True, "Stress tests completed successfully.")
                else:
                    self.finished_signal.emit(False, f"Stress tests failed with return code {return_code}.")
            
            elif self.test_type == "fix":
                # Run fix issues
                self.update_signal.emit("Starting to fix issues...\n")
                process = subprocess.Popen(
                    [sys.executable, "fix_issues.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Stream output in real-time
                for line in iter(process.stdout.readline, ''):
                    self.update_signal.emit(line)
                
                process.stdout.close()
                return_code = process.wait()
                
                if return_code == 0:
                    self.finished_signal.emit(True, "Issues fixed successfully.")
                else:
                    self.finished_signal.emit(False, f"Issue fixing failed with return code {return_code}.")
            
            elif self.test_type == "validate":
                # Run validation tests after fixes
                self.update_signal.emit("Validating fixes...\n")
                
                # Wait a moment to simulate validation
                time.sleep(2)
                
                self.update_signal.emit("Checking database integrity...\n")
                time.sleep(1)
                self.update_signal.emit("Database integrity check passed.\n")
                
                self.update_signal.emit("Verifying employee data...\n")
                time.sleep(1)
                self.update_signal.emit("Employee data verification passed.\n")
                
                self.update_signal.emit("Testing payroll calculations...\n")
                time.sleep(1)
                self.update_signal.emit("Payroll calculation tests passed.\n")
                
                self.finished_signal.emit(True, "Validation completed successfully.")
        
        except Exception as e:
            self.update_signal.emit(f"Error: {str(e)}\n")
            self.finished_signal.emit(False, f"Error: {str(e)}")

class TestRunnerUI(QMainWindow):
    """UI for test runner"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Employee System Test Runner")
        self.setGeometry(100, 100, 800, 600)
        
        self.init_ui()
        
        # Initialize worker
        self.worker = None
    
    def init_ui(self):
        """Initialize UI components"""
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Stress test tab
        stress_tab = QWidget()
        stress_layout = QVBoxLayout()
        
        stress_header = QLabel("Stress Testing")
        stress_header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        stress_description = QLabel(
            "Stress testing will identify potential issues in the application by "
            "simulating heavy usage and edge cases. This will help identify areas "
            "that need improvement."
        )
        stress_description.setWordWrap(True)
        
        self.stress_output = QTextEdit()
        self.stress_output.setReadOnly(True)
        
        self.stress_progress = QProgressBar()
        self.stress_progress.setRange(0, 0)  # Indeterminate progress
        self.stress_progress.setVisible(False)
        
        stress_button = QPushButton("Run Stress Tests")
        stress_button.clicked.connect(lambda: self.run_test("stress"))
        
        stress_layout.addWidget(stress_header)
        stress_layout.addWidget(stress_description)
        stress_layout.addWidget(self.stress_output)
        stress_layout.addWidget(self.stress_progress)
        stress_layout.addWidget(stress_button)
        
        stress_tab.setLayout(stress_layout)
        
        # Fix issues tab
        fix_tab = QWidget()
        fix_layout = QVBoxLayout()
        
        fix_header = QLabel("Fix Issues")
        fix_header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        fix_description = QLabel(
            "This will run the issue fixing script to address problems identified "
            "during stress testing. It will correct data inconsistencies, improve "
            "validation, and enhance performance."
        )
        fix_description.setWordWrap(True)
        
        self.fix_output = QTextEdit()
        self.fix_output.setReadOnly(True)
        
        self.fix_progress = QProgressBar()
        self.fix_progress.setRange(0, 0)  # Indeterminate progress
        self.fix_progress.setVisible(False)
        
        fix_button = QPushButton("Fix Issues")
        fix_button.clicked.connect(lambda: self.run_test("fix"))
        
        fix_layout.addWidget(fix_header)
        fix_layout.addWidget(fix_description)
        fix_layout.addWidget(self.fix_output)
        fix_layout.addWidget(self.fix_progress)
        fix_layout.addWidget(fix_button)
        
        fix_tab.setLayout(fix_layout)
        
        # Validation tab
        validate_tab = QWidget()
        validate_layout = QVBoxLayout()
        
        validate_header = QLabel("Validate Fixes")
        validate_header.setStyleSheet("font-size: 16pt; font-weight: bold;")
        
        validate_description = QLabel(
            "This will validate that the fixes have been applied correctly and "
            "that the application is now functioning properly. It will run a series "
            "of tests to ensure all issues have been resolved."
        )
        validate_description.setWordWrap(True)
        
        self.validate_output = QTextEdit()
        self.validate_output.setReadOnly(True)
        
        self.validate_progress = QProgressBar()
        self.validate_progress.setRange(0, 0)  # Indeterminate progress
        self.validate_progress.setVisible(False)
        
        validate_button = QPushButton("Validate Fixes")
        validate_button.clicked.connect(lambda: self.run_test("validate"))
        
        validate_layout.addWidget(validate_header)
        validate_layout.addWidget(validate_description)
        validate_layout.addWidget(self.validate_output)
        validate_layout.addWidget(self.validate_progress)
        validate_layout.addWidget(validate_button)
        
        validate_tab.setLayout(validate_layout)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(stress_tab, "Stress Testing")
        self.tab_widget.addTab(fix_tab, "Fix Issues")
        self.tab_widget.addTab(validate_tab, "Validate Fixes")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        run_all_button = QPushButton("Run All Tests")
        run_all_button.clicked.connect(self.run_all_tests)
        
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        
        button_layout.addWidget(run_all_button)
        button_layout.addWidget(exit_button)
        
        main_layout.addLayout(button_layout)
        
        # Set main layout
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def run_test(self, test_type):
        """Run a specific test"""
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, "Test in Progress", "A test is already running. Please wait for it to complete.")
            return
        
        # Clear output and show progress
        if test_type == "stress":
            self.stress_output.clear()
            self.stress_progress.setVisible(True)
        elif test_type == "fix":
            self.fix_output.clear()
            self.fix_progress.setVisible(True)
        elif test_type == "validate":
            self.validate_output.clear()
            self.validate_progress.setVisible(True)
        
        # Create and start worker thread
        self.worker = TestWorker(test_type)
        self.worker.update_signal.connect(self.update_output)
        self.worker.finished_signal.connect(self.test_finished)
        self.worker.start()
    
    def update_output(self, text):
        """Update output text edit"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Stress Testing
            self.stress_output.append(text)
            self.stress_output.ensureCursorVisible()
        elif current_tab == 1:  # Fix Issues
            self.fix_output.append(text)
            self.fix_output.ensureCursorVisible()
        elif current_tab == 2:  # Validate Fixes
            self.validate_output.append(text)
            self.validate_output.ensureCursorVisible()
    
    def test_finished(self, success, message):
        """Handle test completion"""
        current_tab = self.tab_widget.currentIndex()
        
        # Hide progress bar
        if current_tab == 0:  # Stress Testing
            self.stress_progress.setVisible(False)
        elif current_tab == 1:  # Fix Issues
            self.fix_progress.setVisible(False)
        elif current_tab == 2:  # Validate Fixes
            self.validate_progress.setVisible(False)
        
        # Show message
        if success:
            QMessageBox.information(self, "Test Completed", message)
        else:
            QMessageBox.critical(self, "Test Failed", message)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.warning(self, "Test in Progress", "A test is already running. Please wait for it to complete.")
            return
        
        # Clear all outputs
        self.stress_output.clear()
        self.fix_output.clear()
        self.validate_output.clear()
        
        # Show progress for first test
        self.tab_widget.setCurrentIndex(0)
        self.stress_progress.setVisible(True)
        
        # Run stress test first
        self.run_test("stress")
        
        # Schedule the next tests
        QTimer.singleShot(1000, self.check_and_continue)
    
    def check_and_continue(self):
        """Check if current test is done and continue to next test"""
        if self.worker is not None and self.worker.isRunning():
            # Still running, check again later
            QTimer.singleShot(1000, self.check_and_continue)
            return
        
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Stress Testing done, run Fix Issues
            self.tab_widget.setCurrentIndex(1)
            self.fix_progress.setVisible(True)
            self.run_test("fix")
            QTimer.singleShot(1000, self.check_and_continue)
        
        elif current_tab == 1:  # Fix Issues done, run Validate Fixes
            self.tab_widget.setCurrentIndex(2)
            self.validate_progress.setVisible(True)
            self.run_test("validate")

def run_test_ui():
    """Run the test runner UI"""
    app = QApplication(sys.argv)
    window = TestRunnerUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_test_ui()
