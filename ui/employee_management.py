from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QPushButton, QFrame, QLabel, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QMessageBox, QMenu, QAction,
                             QFileDialog, QScrollArea, QFormLayout, QDateEdit,
                             QSpinBox, QDoubleSpinBox, QTextEdit, QGroupBox)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
import os
from datetime import datetime
from .styles import Styles

class EmployeeCard(QFrame):
    clicked = pyqtSignal(dict)
    
    def __init__(self, employee_data):
        super().__init__()
        self.employee_data = employee_data
        self.setObjectName("card")
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Employee photo
        photo_label = QLabel()
        photo_label.setFixedSize(80, 80)
        if self.employee_data.get('photo_path') and os.path.exists(self.employee_data['photo_path']):
            pixmap = QPixmap(self.employee_data['photo_path'])
        else:
            pixmap = QPixmap("resources/default_avatar.png")
        photo_label.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(photo_label)
        
        # Employee info
        info_layout = QVBoxLayout()
        
        name_label = QLabel(self.employee_data['name'])
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        position_label = QLabel(f"{self.employee_data['position']} - {self.employee_data['department']}")
        position_label.setStyleSheet("color: #7f8c8d;")
        
        contact_label = QLabel(f"{self.employee_data['email']} | {self.employee_data['phone']}")
        contact_label.setStyleSheet("color: #7f8c8d;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(position_label)
        info_layout.addWidget(contact_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # Status indicator
        status_layout = QVBoxLayout()
        status_label = QLabel(self.employee_data.get('status', 'Active'))
        status_color = "#2ecc71" if self.employee_data.get('status') == 'Active' else "#e74c3c"
        status_label.setStyleSheet(f"""
            color: {status_color};
            font-weight: bold;
            padding: 5px 10px;
            border: 2px solid {status_color};
            border-radius: 10px;
        """)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.employee_data)

class EmployeeManagement(QWidget):
    def __init__(self, employee_controller):
        super().__init__()
        self.employee_controller = employee_controller
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Search and filter bar
        search_frame = QFrame()
        search_frame.setObjectName("card")
        search_layout = QHBoxLayout(search_frame)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchBox")
        self.search_input.setPlaceholderText("Search employees...")
        self.search_input.textChanged.connect(self.filter_employees)
        
        # Department filter
        self.dept_filter = QComboBox()
        self.dept_filter.addItems(["All Departments", "IT", "HR", "Finance", "Sales"])
        self.dept_filter.currentTextChanged.connect(self.filter_employees)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Status", "Active", "On Leave", "Resigned"])
        self.status_filter.currentTextChanged.connect(self.filter_employees)
        
        # Add employee button
        add_btn = QPushButton("Add Employee")
        add_btn.clicked.connect(self.add_employee)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.dept_filter)
        search_layout.addWidget(self.status_filter)
        search_layout.addWidget(add_btn)
        
        layout.addWidget(search_frame)
        
        # Employees list
        self.employees_scroll = QScrollArea()
        self.employees_scroll.setWidgetResizable(True)
        self.employees_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.employees_container = QWidget()
        self.employees_layout = QVBoxLayout(self.employees_container)
        self.employees_layout.setSpacing(10)
        self.employees_layout.addStretch()
        
        self.employees_scroll.setWidget(self.employees_container)
        layout.addWidget(self.employees_scroll)
    
    def load_employees(self):
        # Clear existing cards
        while self.employees_layout.count() > 1:
            item = self.employees_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add employee cards
        success, employees = self.employee_controller.get_all_employees()
        if success:
            for employee in employees:
                card = EmployeeCard(employee)
                card.clicked.connect(self.edit_employee)
                self.employees_layout.insertWidget(self.employees_layout.count() - 1, card)
    
    def filter_employees(self):
        search_text = self.search_input.text().lower()
        department = self.dept_filter.currentText()
        status = self.status_filter.currentText()
        
        # Show/hide cards based on filters
        for i in range(self.employees_layout.count() - 1):
            widget = self.employees_layout.itemAt(i).widget()
            if isinstance(widget, EmployeeCard):
                employee = widget.employee_data
                name_match = search_text in employee['name'].lower()
                dept_match = department == "All Departments" or department == employee['department']
                status_match = status == "All Status" or status == employee.get('status', 'Active')
                
                widget.setVisible(name_match and dept_match and status_match)
    
    def add_employee(self):
        # Show employee form dialog
        from .employee_form import EmployeeForm
        form = EmployeeForm(self.employee_controller)
        form.employee_saved.connect(self.load_employees)
        form.show()
    
    def edit_employee(self, employee_data):
        # Show employee form dialog with data
        from .employee_form import EmployeeForm
        form = EmployeeForm(self.employee_controller)
        form.load_employee(employee_data)
        form.employee_saved.connect(self.load_employees)
        form.show()

class EmployeeFormTabs(QTabWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        # Personal Information Tab
        personal_tab = QWidget()
        personal_layout = QFormLayout(personal_tab)
        
        # Add personal info fields
        self.name_edit = QLineEdit()
        self.name_ar_edit = QLineEdit()
        self.dob_edit = QDateEdit()
        self.gender_combo = QComboBox()
        self.nationality_edit = QLineEdit()
        self.national_id_edit = QLineEdit()
        self.passport_edit = QLineEdit()
        
        personal_layout.addRow("Name (English):", self.name_edit)
        personal_layout.addRow("Name (Arabic):", self.name_ar_edit)
        personal_layout.addRow("Date of Birth:", self.dob_edit)
        personal_layout.addRow("Gender:", self.gender_combo)
        personal_layout.addRow("Nationality:", self.nationality_edit)
        personal_layout.addRow("National ID:", self.national_id_edit)
        personal_layout.addRow("Passport Number:", self.passport_edit)
        
        self.addTab(personal_tab, "Personal Information")
        
        # Contact Information Tab
        contact_tab = QWidget()
        contact_layout = QFormLayout(contact_tab)
        
        # Add contact info fields
        self.phone_edit = QLineEdit()
        self.phone2_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QTextEdit()
        
        contact_layout.addRow("Primary Phone:", self.phone_edit)
        contact_layout.addRow("Secondary Phone:", self.phone2_edit)
        contact_layout.addRow("Email:", self.email_edit)
        contact_layout.addRow("Address:", self.address_edit)
        
        self.addTab(contact_tab, "Contact Information")
        
        # Employment Details Tab
        employment_tab = QWidget()
        employment_layout = QFormLayout(employment_tab)
        
        # Add employment fields
        self.department_combo = QComboBox()
        self.position_combo = QComboBox()
        self.hire_date_edit = QDateEdit()
        self.contract_type_combo = QComboBox()
        self.basic_salary_spin = QDoubleSpinBox()
        self.currency_combo = QComboBox()
        
        employment_layout.addRow("Department:", self.department_combo)
        employment_layout.addRow("Position:", self.position_combo)
        employment_layout.addRow("Hire Date:", self.hire_date_edit)
        employment_layout.addRow("Contract Type:", self.contract_type_combo)
        employment_layout.addRow("Basic Salary:", self.basic_salary_spin)
        employment_layout.addRow("Currency:", self.currency_combo)
        
        self.addTab(employment_tab, "Employment Details")
        
        # Documents Tab
        documents_tab = QWidget()
        documents_layout = QVBoxLayout(documents_tab)
        
        # Add document upload section
        upload_group = QGroupBox("Upload Documents")
        upload_layout = QVBoxLayout(upload_group)
        
        # Add document list and upload button
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(4)
        self.documents_table.setHorizontalHeaderLabels(["Type", "Title", "Upload Date", "Actions"])
        
        upload_btn = QPushButton("Upload New Document")
        
        upload_layout.addWidget(self.documents_table)
        upload_layout.addWidget(upload_btn)
        
        documents_layout.addWidget(upload_group)
        
        self.addTab(documents_tab, "Documents")
