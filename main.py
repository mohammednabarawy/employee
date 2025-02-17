import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QStackedWidget,
                           QFrame, QSizePolicy, QTableWidget, QTableWidgetItem,
                           QHeaderView, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont
from database import Database
from controllers.employee_controller import EmployeeController
from controllers.salary_controller import SalaryController
from ui.employee_form import EmployeeForm
from ui.salary_form import SalaryForm
from utils.export_utils import ExportUtils
from ui.styles import Styles
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.employee_controller = EmployeeController(self.db)
        self.salary_controller = SalaryController(self.db)
        self.export_utils = ExportUtils()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Employee Management System')
        self.setMinimumSize(1200, 800)
        
        # Apply stylesheet
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Create sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Create stacked widget for main content
        self.stacked_widget = QStackedWidget()
        self.init_pages()
        main_layout.addWidget(self.stacked_widget)
        
        # Set layout ratio between sidebar and main content
        main_layout.setStretch(0, 1)  # Sidebar
        main_layout.setStretch(1, 4)  # Main content

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(250)
        layout = QVBoxLayout(sidebar)
        
        # Add logo/title
        title = QLabel("EMS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 24px; padding: 20px;")
        layout.addWidget(title)
        
        # Add navigation buttons
        self.nav_buttons = {}
        
        # Dashboard button
        dashboard_btn = QPushButton("Dashboard")
        dashboard_btn.setCheckable(True)
        dashboard_btn.clicked.connect(lambda: self.show_page("dashboard"))
        layout.addWidget(dashboard_btn)
        self.nav_buttons["dashboard"] = dashboard_btn
        
        # Employees button
        employees_btn = QPushButton("Employees")
        employees_btn.setCheckable(True)
        employees_btn.clicked.connect(lambda: self.show_page("employees"))
        layout.addWidget(employees_btn)
        self.nav_buttons["employees"] = employees_btn
        
        # Salaries button
        salaries_btn = QPushButton("Salaries")
        salaries_btn.setCheckable(True)
        salaries_btn.clicked.connect(lambda: self.show_page("salaries"))
        layout.addWidget(salaries_btn)
        self.nav_buttons["salaries"] = salaries_btn
        
        # Reports button
        reports_btn = QPushButton("Reports")
        reports_btn.setCheckable(True)
        reports_btn.clicked.connect(lambda: self.show_page("reports"))
        layout.addWidget(reports_btn)
        self.nav_buttons["reports"] = reports_btn
        
        layout.addStretch()
        return sidebar

    def init_pages(self):
        # Create pages
        self.employee_form = EmployeeForm(self.employee_controller)
        self.salary_form = SalaryForm(self.salary_controller, self.employee_controller)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.employee_form)  # Index 0
        self.stacked_widget.addWidget(self.salary_form)    # Index 1
        
        # Show employees page by default
        self.show_page("employees")

    def show_page(self, page_name):
        # Update button states
        for btn_id, btn in self.nav_buttons.items():
            btn.setChecked(btn_id == page_name)
        
        # Show the selected page
        if page_name == "employees":
            self.stacked_widget.setCurrentIndex(0)
        elif page_name == "salaries":
            self.stacked_widget.setCurrentIndex(1)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
