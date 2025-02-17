from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QTabWidget, QWidget,
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
                             QTextEdit, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QPixmap
from .employee_management import EmployeeFormTabs
from utils.validation import ValidationUtils

class EmployeeForm(QDialog):
    employee_saved = pyqtSignal(dict)
    
    def __init__(self, employee_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.photo_path = None
        self.employee_id = None
        self.current_employee_index = -1
        self.employees = []
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        self.setWindowTitle("Employee Details")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Navigation buttons at the top
        nav_layout = QHBoxLayout()
        
        self.first_btn = QPushButton("⏮ First")
        self.prev_btn = QPushButton("◀ Previous")
        self.employee_count_label = QLabel()
        self.next_btn = QPushButton("Next ▶")
        self.last_btn = QPushButton("Last ⏭")
        
        # Connect navigation buttons
        self.first_btn.clicked.connect(self.go_to_first)
        self.prev_btn.clicked.connect(self.go_to_previous)
        self.next_btn.clicked.connect(self.go_to_next)
        self.last_btn.clicked.connect(self.go_to_last)
        
        nav_layout.addWidget(self.first_btn)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.employee_count_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.last_btn)
        
        layout.addLayout(nav_layout)
        
        # Header with photo
        header_layout = QHBoxLayout()
        
        # Photo section
        photo_layout = QVBoxLayout()
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet("border: 2px dashed #bdc3c7; border-radius: 75px;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        
        self.upload_photo_btn = QPushButton("Change Photo")
        self.upload_photo_btn.clicked.connect(self.upload_photo)
        
        photo_layout.addWidget(self.photo_label)
        photo_layout.addWidget(self.upload_photo_btn)
        photo_layout.addStretch()
        
        # Form tabs
        self.form_tabs = QTabWidget()
        self.personal_info_tab = QWidget()
        self.contact_info_tab = QWidget()
        self.employment_details_tab = QWidget()
        
        self.form_tabs.addTab(self.personal_info_tab, "Personal Information")
        self.form_tabs.addTab(self.contact_info_tab, "Contact Information")
        self.form_tabs.addTab(self.employment_details_tab, "Employment Details")
        
        self.init_personal_info_tab()
        self.init_contact_info_tab()
        self.init_employment_details_tab()
        
        header_layout.addLayout(photo_layout)
        header_layout.addWidget(self.form_tabs)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("New Employee")
        self.new_btn.clicked.connect(self.new_employee)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_employee)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setObjectName("deleteButton")
        self.delete_btn.clicked.connect(self.delete_employee)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.new_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # Add layouts to main layout
        layout.addLayout(header_layout)
        layout.addLayout(button_layout)
        
        # Initialize navigation buttons state
        self.update_navigation_buttons()
    
    def load_employees(self):
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.employees = employees
            if self.employees:
                self.current_employee_index = 0
                self.load_current_employee()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        has_employees = len(self.employees) > 0
        current_index = self.current_employee_index
        
        self.first_btn.setEnabled(has_employees and current_index > 0)
        self.prev_btn.setEnabled(has_employees and current_index > 0)
        self.next_btn.setEnabled(has_employees and current_index < len(self.employees) - 1)
        self.last_btn.setEnabled(has_employees and current_index < len(self.employees) - 1)
        
        if has_employees:
            self.employee_count_label.setText(
                f"Employee {current_index + 1} of {len(self.employees)}"
            )
        else:
            self.employee_count_label.setText("No Employees")
        
        # Enable/disable delete button
        self.delete_btn.setEnabled(has_employees)
    
    def go_to_first(self):
        if self.employees:
            self.current_employee_index = 0
            self.load_current_employee()
    
    def go_to_previous(self):
        if self.current_employee_index > 0:
            self.current_employee_index -= 1
            self.load_current_employee()
    
    def go_to_next(self):
        if self.current_employee_index < len(self.employees) - 1:
            self.current_employee_index += 1
            self.load_current_employee()
    
    def go_to_last(self):
        if self.employees:
            self.current_employee_index = len(self.employees) - 1
            self.load_current_employee()
    
    def load_current_employee(self):
        if 0 <= self.current_employee_index < len(self.employees):
            self.load_employee(self.employees[self.current_employee_index])
            self.update_navigation_buttons()
    
    def new_employee(self):
        self.clear_form()
        self.current_employee_index = -1
        self.update_navigation_buttons()
    
    def clear_form(self):
        self.employee_id = None
        self.photo_path = None
        self.photo_label.clear()
        self.photo_label.setStyleSheet("border: 2px dashed #bdc3c7; border-radius: 75px;")
        
        # Clear all form fields
        self.name_edit.clear()
        self.name_ar_edit.clear()
        self.dob_edit.setDate(QDate.currentDate().addYears(-18))
        self.gender_combo.setCurrentIndex(0)
        self.nationality_edit.setCurrentIndex(0)
        self.national_id_edit.clear()
        self.passport_edit.clear()
        
        self.phone_edit.clear()
        self.phone2_edit.clear()
        self.email_edit.clear()
        self.address_edit.clear()
        
        self.department_combo.setCurrentIndex(0)
        self.position_combo.setCurrentIndex(0)
        self.hire_date_edit.setDate(QDate.currentDate())
        self.contract_type_combo.setCurrentIndex(0)
        self.bank_account_edit.clear()
        self.salary_type_combo.setCurrentIndex(0)
        self.basic_salary_spin.setValue(0)
        self.currency_combo.setCurrentIndex(0)
    
    def delete_employee(self):
        if not self.employee_id:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this employee?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.employee_controller.delete_employee(self.employee_id)
            if success:
                QMessageBox.information(self, "Success", "Employee deleted successfully!")
                self.load_employees()
                if self.current_employee_index >= len(self.employees):
                    self.current_employee_index = len(self.employees) - 1
                if self.current_employee_index >= 0:
                    self.load_current_employee()
                else:
                    self.clear_form()
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete employee: {error}")
    
    def setup_editable_combo(self, combo, items, default=''):
        """Setup a combobox to be editable with default items."""
        combo.setEditable(True)
        combo.addItems(items)
        combo.setInsertPolicy(QComboBox.InsertAlphabetically)
        if default and default not in items:
            combo.addItem(default)
        combo.setCurrentText(default if default else items[0])

    def init_personal_info_tab(self):
        layout = QVBoxLayout(self.personal_info_tab)
        form_layout = QFormLayout()
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Arabic Name
        self.name_ar_edit = QLineEdit()
        form_layout.addRow("Name (Arabic):", self.name_ar_edit)
        
        # Date of Birth
        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate().addYears(-18))
        form_layout.addRow("Date of Birth:", self.dob_edit)
        
        # Gender
        self.gender_combo = QComboBox()
        self.setup_editable_combo(self.gender_combo, ['Male', 'Female', 'Other'])
        form_layout.addRow("Gender:", self.gender_combo)
        
        # Nationality
        self.nationality_edit = QComboBox()
        nationalities = ['American', 'British', 'Canadian', 'Egyptian', 'French', 'German', 
                        'Indian', 'Italian', 'Japanese', 'Saudi', 'UAE', 'Other']
        self.setup_editable_combo(self.nationality_edit, nationalities)
        form_layout.addRow("Nationality:", self.nationality_edit)
        
        # National ID
        self.national_id_edit = QLineEdit()
        form_layout.addRow("National ID:", self.national_id_edit)
        
        # Passport
        self.passport_edit = QLineEdit()
        form_layout.addRow("Passport Number:", self.passport_edit)
        
        layout.addLayout(form_layout)
        layout.addStretch()
    
    def init_contact_info_tab(self):
        layout = QVBoxLayout(self.contact_info_tab)
        
        # Contact Information
        self.phone_edit = QLineEdit()
        self.phone2_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.address_edit = QTextEdit()
        
        layout.addWidget(QLabel("Phone:"))
        layout.addWidget(self.phone_edit)
        layout.addWidget(QLabel("Phone (Secondary):"))
        layout.addWidget(self.phone2_edit)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_edit)
        layout.addWidget(QLabel("Address:"))
        layout.addWidget(self.address_edit)
        
    def init_employment_details_tab(self):
        layout = QVBoxLayout(self.employment_details_tab)
        form_layout = QFormLayout()
        
        # Department
        self.department_combo = QComboBox()
        departments = ['IT', 'HR', 'Finance', 'Sales', 'Marketing', 'Operations', 
                      'Legal', 'Customer Service', 'Research & Development']
        self.setup_editable_combo(self.department_combo, departments)
        form_layout.addRow("Department:", self.department_combo)
        
        # Position
        self.position_combo = QComboBox()
        positions = ['CEO', 'Manager', 'Team Lead', 'Senior', 'Junior', 'Intern', 
                    'Specialist', 'Coordinator', 'Supervisor']
        self.setup_editable_combo(self.position_combo, positions)
        form_layout.addRow("Position:", self.position_combo)
        
        # Hire Date
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Hire Date:", self.hire_date_edit)
        
        # Contract Type
        self.contract_type_combo = QComboBox()
        contract_types = ['Full Time', 'Part Time', 'Contract', 'Temporary', 
                         'Seasonal', 'Probation', 'Remote']
        self.setup_editable_combo(self.contract_type_combo, contract_types, 'Full Time')
        form_layout.addRow("Contract Type:", self.contract_type_combo)
        
        # Bank Account
        self.bank_account_edit = QLineEdit()
        self.bank_account_edit.setPlaceholderText("Enter bank account number")
        form_layout.addRow("Bank Account:", self.bank_account_edit)
        
        # Salary Type
        self.salary_type_combo = QComboBox()
        salary_types = ['Monthly', 'Weekly', 'Daily', 'Hourly', 
                       'Project-based', 'Commission-based']
        self.setup_editable_combo(self.salary_type_combo, salary_types, 'Monthly')
        form_layout.addRow("Salary Type:", self.salary_type_combo)
        
        # Basic Salary
        self.basic_salary_spin = QDoubleSpinBox()
        self.basic_salary_spin.setRange(0, 1000000)
        self.basic_salary_spin.setDecimals(2)
        self.basic_salary_spin.setSingleStep(100)
        form_layout.addRow("Basic Salary:", self.basic_salary_spin)
        
        # Currency
        self.currency_combo = QComboBox()
        currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AED', 'SAR', 'KWD', 'BHD', 
                     'OMR', 'QAR', 'EGP']
        self.setup_editable_combo(self.currency_combo, currencies, 'USD')
        form_layout.addRow("Currency:", self.currency_combo)
        
        layout.addLayout(form_layout)
        layout.addStretch()

    def get_form_data(self):
        """Get all form data as a dictionary."""
        return {
            'name': self.name_edit.text(),
            'name_ar': self.name_ar_edit.text(),
            'dob': self.dob_edit.date().toString('yyyy-MM-dd'),
            'gender': self.gender_combo.currentText(),
            'nationality': self.nationality_edit.currentText(),
            'national_id': self.national_id_edit.text(),
            'passport': self.passport_edit.text(),
            'phone': self.phone_edit.text(),
            'phone2': self.phone2_edit.text(),
            'email': self.email_edit.text(),
            'address': self.address_edit.toPlainText(),
            'department': self.department_combo.currentText(),
            'position': self.position_combo.currentText(),
            'hire_date': self.hire_date_edit.date().toString('yyyy-MM-dd'),
            'contract_type': self.contract_type_combo.currentText(),
            'bank_account': self.bank_account_edit.text(),
            'salary_type': ValidationUtils.normalize_salary_type(self.salary_type_combo.currentText()),
            'basic_salary': self.basic_salary_spin.value(),
            'currency': self.currency_combo.currentText(),
            'photo_path': self.photo_path
        }

    def load_employee(self, employee_data):
        """Load employee data into the form."""
        self.employee_id = employee_data.get('id')
        
        # Personal Information
        self.name_edit.setText(employee_data.get('name', ''))
        self.name_ar_edit.setText(employee_data.get('name_ar', ''))
        self.dob_edit.setDate(ValidationUtils.parse_date(employee_data.get('dob')))
        self.gender_combo.setCurrentText(employee_data.get('gender', ''))
        self.nationality_edit.setCurrentText(employee_data.get('nationality', ''))
        self.national_id_edit.setText(employee_data.get('national_id', ''))
        self.passport_edit.setText(employee_data.get('passport', ''))
        
        # Contact Information
        self.phone_edit.setText(employee_data.get('phone', ''))
        self.phone2_edit.setText(employee_data.get('phone2', ''))
        self.email_edit.setText(employee_data.get('email', ''))
        self.address_edit.setPlainText(employee_data.get('address', ''))
        
        # Employment Details
        self.department_combo.setCurrentText(employee_data.get('department', ''))
        self.position_combo.setCurrentText(employee_data.get('position', ''))
        self.hire_date_edit.setDate(ValidationUtils.parse_date(employee_data.get('hire_date')))
        self.contract_type_combo.setCurrentText(employee_data.get('contract_type', ''))
        self.bank_account_edit.setText(employee_data.get('bank_account', ''))
        
        # Convert database salary type to display format
        salary_type = employee_data.get('salary_type', 'monthly')
        if salary_type == 'project':
            display_type = 'Project-based'
        elif salary_type == 'commission':
            display_type = 'Commission-based'
        else:
            display_type = salary_type.capitalize()
        self.salary_type_combo.setCurrentText(display_type)
        
        self.basic_salary_spin.setValue(float(employee_data.get('basic_salary', 0)))
        self.currency_combo.setCurrentText(employee_data.get('currency', 'USD'))
        
        # Photo
        self.photo_path = employee_data.get('photo_path')
        if self.photo_path:
            pixmap = QPixmap(self.photo_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.photo_label.setPixmap(pixmap)
            else:
                self.photo_label.clear()
                self.photo_label.setStyleSheet("border: 2px dashed #bdc3c7; border-radius: 75px;")
        else:
            self.photo_label.clear()
            self.photo_label.setStyleSheet("border: 2px dashed #bdc3c7; border-radius: 75px;")
    
    def upload_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Photo",
            "",
            "Image Files (*.png *.jpg *.jpeg)"
        )
        
        if file_name:
            self.photo_path = file_name
            pixmap = QPixmap(file_name)
            self.photo_label.setPixmap(
                pixmap.scaled(
                    self.photo_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
    
    def save_employee(self):
        data = self.get_form_data()
        
        # Validate data
        valid, msg = ValidationUtils.validate_employee_data(data)
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return
        
        if self.employee_id:  # Update existing employee
            success, error = self.employee_controller.update_employee(self.employee_id, data)
        else:  # Add new employee
            success, error = self.employee_controller.add_employee(data)
        
        if success:
            self.employee_saved.emit(data)
            QMessageBox.information(self, "Success", "Employee saved successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to save employee: {error}")
