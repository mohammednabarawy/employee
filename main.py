import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QStackedWidget, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import Database
from controllers.employee_controller import EmployeeController
from controllers.salary_controller import SalaryController
from ui.employee_form import EmployeeForm
from ui.salary_form import SalaryForm

class MainWindow(QMainWindow):
    def __init__(self, employee_controller, salary_controller):
        super().__init__()
        self.employee_controller = employee_controller
        self.salary_controller = salary_controller
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("نظام إدارة الموظفين")
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.RightToLeft)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create and setup sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # Create and setup stacked widget for main content
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Set layout proportions
        main_layout.setStretch(0, 1)  # Sidebar takes 1 part
        main_layout.setStretch(1, 4)  # Main content takes 4 parts

        # Create forms
        self.employee_form = EmployeeForm(self.employee_controller)
        self.salary_form = SalaryForm(self.salary_controller)

        # Add forms to stacked widget
        self.stacked_widget.addWidget(self.employee_form)
        self.stacked_widget.addWidget(self.salary_form)

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            QWidget#sidebar {
                background-color: #2c3e50;
                min-width: 200px;
                max-width: 200px;
            }
            QPushButton {
                color: white;
                border: none;
                text-align: right;
                padding: 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #3498db;
            }
            QLabel {
                color: white;
                padding: 20px;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add title
        title = QLabel("القائمة الرئيسية")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Create navigation buttons
        self.emp_btn = QPushButton("إدارة الموظفين")
        self.emp_btn.setCheckable(True)
        self.emp_btn.setChecked(True)
        self.emp_btn.clicked.connect(lambda: self.switch_page(0))

        self.salary_btn = QPushButton("إدارة الرواتب")
        self.salary_btn.setCheckable(True)
        self.salary_btn.clicked.connect(lambda: self.switch_page(1))

        # Add buttons to layout
        layout.addWidget(self.emp_btn)
        layout.addWidget(self.salary_btn)
        layout.addStretch()

        return sidebar

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
        # Update button states
        self.emp_btn.setChecked(index == 0)
        self.salary_btn.setChecked(index == 1)

def main():
    # Create database instance
    db = Database()
    
    # Create controllers
    employee_controller = EmployeeController(db)
    salary_controller = SalaryController(db)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application-wide settings
    app.setLayoutDirection(Qt.RightToLeft)
    
    # Create and show main window
    window = MainWindow(employee_controller, salary_controller)
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
