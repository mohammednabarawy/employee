from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QListWidget, QStackedWidget, QLabel,
                             QFrame, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from .employee_form import EmployeeForm
from .salary_form import SalaryForm
from .attendance_form import AttendanceForm
from .reports_form import ReportsForm

class MainWindow(QMainWindow):
    def __init__(self, employee_controller=None, salary_controller=None, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.salary_controller = salary_controller
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Employee Management System')
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # Create and setup sidebar
        self.setup_sidebar(layout)
        
        # Create and setup main content area
        self.setup_main_content(layout)
        
        # Initialize pages
        self.init_pages()
        
        # Show default page
        self.show_page("employees")
        
        # Apply stylesheet
        self.apply_stylesheet()
    
    def setup_sidebar(self, layout):
        # Create sidebar frame
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        sidebar_frame.setFixedWidth(200)
        
        # Create sidebar layout
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Add logo/title
        title_label = QLabel("EMS")
        title_label.setObjectName("sidebarTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Bold))
        sidebar_layout.addWidget(title_label)
        
        # Create navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("employees", "Employees", ""),
            ("salary", "Salary", ""),
            ("attendance", "Attendance", ""),
            ("reports", "Reports", "")
        ]
        
        for item_id, text, icon in nav_items:
            btn = QPushButton(f"{icon} {text}")
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, x=item_id: self.show_page(x))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[item_id] = btn
        
        # Add stretch to push buttons to the top
        sidebar_layout.addStretch()
        
        # Add sidebar to main layout
        layout.addWidget(sidebar_frame)
    
    def setup_main_content(self, layout):
        # Create main content widget
        main_content = QWidget()
        main_content.setObjectName("mainContent")
        main_layout = QVBoxLayout(main_content)
        
        # Create stacked widget for different pages
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # Add main content to layout
        layout.addWidget(main_content)
    
    def init_pages(self):
        # Create pages
        self.employee_form = EmployeeForm(self.employee_controller)
        self.salary_form = SalaryForm(self.salary_controller, self.employee_controller)
        self.attendance_form = AttendanceForm(self.employee_controller)
        self.reports_form = ReportsForm(self.employee_controller, self.salary_controller)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.employee_form)  # Index 0
        self.stacked_widget.addWidget(self.salary_form)    # Index 1
        self.stacked_widget.addWidget(self.attendance_form)  # Index 2
        self.stacked_widget.addWidget(self.reports_form)     # Index 3
    
    def show_page(self, page_name):
        # Update button states
        for btn in self.nav_buttons.values():
            btn.setChecked(False)
        self.nav_buttons[page_name].setChecked(True)
        
        # Show corresponding page
        page_index = {
            "employees": 0,
            "salary": 1,
            "attendance": 2,
            "reports": 3
        }
        self.stacked_widget.setCurrentIndex(page_index[page_name])
    
    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            #sidebar {
                background-color: #2c3e50;
                border: none;
            }
            #sidebarTitle {
                color: white;
                padding: 20px;
                background-color: #34495e;
            }
            #sidebarButton {
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
                color: white;
                background-color: transparent;
            }
            #sidebarButton:hover {
                background-color: #34495e;
            }
            #sidebarButton:checked {
                background-color: #3498db;
            }
            #mainContent {
                background-color: white;
                border-radius: 10px;
                margin: 10px;
            }
        """)
