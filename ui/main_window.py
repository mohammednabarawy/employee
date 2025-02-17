import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QStackedWidget, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from database import Database
from controllers.employee_controller import EmployeeController
from controllers.salary_controller import SalaryController
from ui.employee_form import EmployeeForm
from ui.salary_form import SalaryForm
from ui.dashboard import Dashboard
from ui.employee_list import EmployeeList
from ui.reports_form import ReportsForm

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

        # Create pages
        self.dashboard = Dashboard(self.employee_controller, self.salary_controller)
        self.employee_list = EmployeeList(self.employee_controller)
        self.employee_form = EmployeeForm(self.employee_controller)
        self.salary_form = SalaryForm(self.salary_controller)
        self.reports_form = ReportsForm(self.employee_controller, self.salary_controller)

        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.dashboard)  # index 0
        self.stacked_widget.addWidget(self.employee_list)  # index 1
        self.stacked_widget.addWidget(self.employee_form)  # index 2
        self.stacked_widget.addWidget(self.salary_form)  # index 3
        self.stacked_widget.addWidget(self.reports_form)  # index 4

        # Connect signals
        self.employee_list.employee_selected.connect(self.employee_form.load_employee)
        self.employee_form.employee_saved.connect(self.employee_list.refresh_list)
        self.employee_form.employee_saved.connect(self.dashboard.refresh_data)

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
        self.dashboard_btn = QPushButton("لوحة المعلومات")
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(True)
        self.dashboard_btn.clicked.connect(lambda: self.switch_page(0))

        self.emp_list_btn = QPushButton("قائمة الموظفين")
        self.emp_list_btn.setCheckable(True)
        self.emp_list_btn.clicked.connect(lambda: self.switch_page(1))

        self.emp_add_btn = QPushButton("إضافة موظف")
        self.emp_add_btn.setCheckable(True)
        self.emp_add_btn.clicked.connect(lambda: self.switch_page(2))

        self.salary_btn = QPushButton("إدارة الرواتب")
        self.salary_btn.setCheckable(True)
        self.salary_btn.clicked.connect(lambda: self.switch_page(3))

        self.reports_btn = QPushButton("التقارير")
        self.reports_btn.setCheckable(True)
        self.reports_btn.clicked.connect(lambda: self.switch_page(4))

        # Add buttons to layout
        layout.addWidget(self.dashboard_btn)
        layout.addWidget(self.emp_list_btn)
        layout.addWidget(self.emp_add_btn)
        layout.addWidget(self.salary_btn)
        layout.addWidget(self.reports_btn)
        layout.addStretch()

        return sidebar

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        
        # Update button states
        buttons = [
            self.dashboard_btn,
            self.emp_list_btn,
            self.emp_add_btn,
            self.salary_btn,
            self.reports_btn
        ]
        
        for i, btn in enumerate(buttons):
            btn.setChecked(i == index)
