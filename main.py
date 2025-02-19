import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QStackedWidget, QLabel)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from database import Database
from controllers.employee_controller import EmployeeController
from controllers.payroll_controller import PayrollController
from ui.employee_form import EmployeeForm
from ui.payroll_form import PayrollForm
from ui.reports_form import ReportsForm

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.employee_controller = EmployeeController(self.db)
        self.payroll_controller = PayrollController(self.db)
        
        # Fix any incorrect employee statuses
        self.employee_controller.fix_employee_statuses()
        
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle('نظام إدارة الموظفين')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout()
        main_widget.setLayout(layout)
        
        # Create sidebar
        sidebar = self.create_sidebar()
        layout.addWidget(sidebar)
        
        # Create stacked widget for main content
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Set layout ratio (1:4)
        layout.setStretch(0, 1)  # Sidebar
        layout.setStretch(1, 4)  # Main content
        
        # Create forms
        self.employee_form = EmployeeForm(self.employee_controller)
        self.payroll_form = PayrollForm(self.payroll_controller, self.employee_controller)
        self.reports_form = ReportsForm(self.employee_controller, self.payroll_controller)
        
        # Add forms to stacked widget
        self.stacked_widget.addWidget(self.employee_form)
        self.stacked_widget.addWidget(self.payroll_form)
        self.stacked_widget.addWidget(self.reports_form)

    def create_sidebar(self):
        """Create the sidebar with navigation buttons"""
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar.setLayout(sidebar_layout)
        
        # Add logo or title
        title = QLabel('القائمة')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 12, QFont.Bold))
        sidebar_layout.addWidget(title)
        
        # Create navigation buttons
        self.employee_btn = QPushButton("الموظفين")
        self.employee_btn.setCheckable(True)
        self.employee_btn.clicked.connect(lambda: self.switch_page(0))
        
        self.payroll_btn = QPushButton("الرواتب")
        self.payroll_btn.setCheckable(True)
        self.payroll_btn.clicked.connect(lambda: self.switch_page(1))
        
        self.reports_btn = QPushButton("التقارير")
        self.reports_btn.setCheckable(True)
        self.reports_btn.clicked.connect(lambda: self.switch_page(2))
        
        # Add buttons to button group
        self.nav_buttons = [self.employee_btn, self.payroll_btn, self.reports_btn]
        
        # Add buttons to sidebar
        sidebar_layout.addWidget(self.employee_btn)
        sidebar_layout.addWidget(self.payroll_btn)
        sidebar_layout.addWidget(self.reports_btn)
        sidebar_layout.addStretch()
        
        return sidebar

    def switch_page(self, index):
        """Switch to the selected page and update button states"""
        self.stacked_widget.setCurrentIndex(index)
        
        # Update button states
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

def main():
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application-wide RTL layout
    app.setLayoutDirection(Qt.RightToLeft)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
