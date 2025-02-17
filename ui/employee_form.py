from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QTabWidget, QWidget,
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
                             QTextEdit, QFormLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QPixmap
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
        layout = QVBoxLayout(self)
        
        # Navigation buttons at the top
        nav_layout, action_layout = self.setup_navigation_buttons()
        
        layout.addLayout(nav_layout)
        
        # Header with photo
        header_layout = QHBoxLayout()
        
        # Photo section
        photo_layout = QVBoxLayout()
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet("border: 1px solid #ccc;")
        photo_layout.addWidget(self.photo_label)
        
        upload_btn = QPushButton("تحميل صورة")
        upload_btn.clicked.connect(self.upload_photo)
        photo_layout.addWidget(upload_btn)
        
        header_layout.addLayout(photo_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.addTab(self.setup_personal_tab(), "المعلومات الشخصية")
        tab_widget.addTab(self.setup_contact_tab(), "معلومات الاتصال")
        tab_widget.addTab(self.setup_employment_tab(), "تفاصيل التوظيف")
        
        layout.addWidget(tab_widget)
        
        # Action buttons
        layout.addLayout(action_layout)

    def setup_personal_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        
        # Name fields
        self.name_edit = QLineEdit()
        layout.addRow("الاسم:", self.name_edit)
        
        self.name_ar_edit = QLineEdit()
        layout.addRow("الاسم بالعربية:", self.name_ar_edit)
        
        # Date of Birth
        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        layout.addRow("تاريخ الميلاد:", self.dob_edit)
        
        # Gender
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["ذكر", "أنثى"])
        layout.addRow("الجنس:", self.gender_combo)
        
        # Nationality
        self.nationality_edit = QComboBox()
        self.nationality_edit.setEditable(True)
        self.nationality_edit.addItems([
            "سعودي", "إماراتي", "كويتي", "بحريني", "عماني", "قطري", "مصري",
            "أردني", "لبناني", "سوري", "عراقي", "يمني", "سوداني", "فلسطيني"
        ])
        layout.addRow("الجنسية:", self.nationality_edit)
        
        # ID Numbers
        self.national_id_edit = QLineEdit()
        layout.addRow("رقم الهوية:", self.national_id_edit)
        
        self.passport_edit = QLineEdit()
        layout.addRow("رقم جواز السفر:", self.passport_edit)
        
        tab.setLayout(layout)
        return tab

    def setup_contact_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        
        # Phone numbers
        self.phone_edit = QLineEdit()
        layout.addRow("رقم الهاتف:", self.phone_edit)
        
        self.phone2_edit = QLineEdit()
        layout.addRow("رقم الهاتف البديل:", self.phone2_edit)
        
        # Email
        self.email_edit = QLineEdit()
        layout.addRow("البريد الإلكتروني:", self.email_edit)
        
        # Address
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(100)
        layout.addRow("العنوان:", self.address_edit)
        
        tab.setLayout(layout)
        return tab

    def setup_employment_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        
        # Department
        self.department_combo = QComboBox()
        self.department_combo.setEditable(True)
        self.department_combo.addItems([
            "الموارد البشرية", "المالية", "تقنية المعلومات", "المبيعات",
            "التسويق", "خدمة العملاء", "الإدارة", "المشتريات", "المستودعات"
        ])
        layout.addRow("القسم:", self.department_combo)
        
        # Position
        self.position_combo = QComboBox()
        self.position_combo.setEditable(True)
        self.position_combo.addItems([
            "مدير", "مشرف", "موظف", "محاسب", "مهندس", "فني",
            "مندوب مبيعات", "سكرتير", "مدخل بيانات"
        ])
        layout.addRow("المنصب:", self.position_combo)
        
        # Hire Date
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        layout.addRow("تاريخ التعيين:", self.hire_date_edit)
        
        # Contract Type
        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems([
            "دوام كامل", "دوام جزئي", "عقد", "مؤقت",
            "موسمي", "تجريبي", "عن بعد"
        ])
        layout.addRow("نوع العقد:", self.contract_type_combo)
        
        # Bank Account
        self.bank_account_edit = QLineEdit()
        layout.addRow("رقم الحساب البنكي:", self.bank_account_edit)
        
        # Salary Type
        self.salary_type_combo = QComboBox()
        self.salary_type_combo.addItems([
            "شهري", "أسبوعي", "يومي", "بالساعة",
            "بالمشروع", "بالعمولة"
        ])
        layout.addRow("نوع الراتب:", self.salary_type_combo)
        
        # Basic Salary
        self.basic_salary_spin = QDoubleSpinBox()
        self.basic_salary_spin.setRange(0, 1000000)
        self.basic_salary_spin.setDecimals(2)
        self.basic_salary_spin.setSingleStep(100)
        layout.addRow("الراتب الأساسي:", self.basic_salary_spin)
        
        # Currency
        self.currency_combo = QComboBox()
        self.currency_combo.addItems([
            "ريال سعودي", "درهم إماراتي", "دينار كويتي", "دينار بحريني",
            "ريال عماني", "ريال قطري", "جنيه مصري", "دولار أمريكي", "يورو"
        ])
        layout.addRow("العملة:", self.currency_combo)
        
        tab.setLayout(layout)
        return tab

    def setup_navigation_buttons(self):
        """Setup navigation buttons."""
        nav_layout = QHBoxLayout()
        action_layout = QHBoxLayout()
        
        # Employee counter label
        self.employee_count_label = QLabel()
        nav_layout.addWidget(self.employee_count_label)
        
        # Navigation buttons
        self.first_btn = QPushButton("الأول")
        self.prev_btn = QPushButton("السابق")
        self.next_btn = QPushButton("التالي")
        self.last_btn = QPushButton("الأخير")
        
        self.first_btn.clicked.connect(self.go_to_first)
        self.prev_btn.clicked.connect(self.go_to_previous)
        self.next_btn.clicked.connect(self.go_to_next)
        self.last_btn.clicked.connect(self.go_to_last)
        
        nav_layout.addWidget(self.first_btn)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.last_btn)
        
        # Action buttons
        self.new_btn = QPushButton("موظف جديد")
        self.save_btn = QPushButton("حفظ")
        self.delete_btn = QPushButton("حذف")
        
        self.new_btn.clicked.connect(self.new_employee)
        self.save_btn.clicked.connect(self.save_employee)
        self.delete_btn.clicked.connect(self.delete_employee)
        
        action_layout.addWidget(self.new_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.delete_btn)
        
        return nav_layout, action_layout

    def update_navigation_buttons(self):
        has_employees = len(self.employees) > 0
        current_index = self.current_employee_index
        
        self.first_btn.setEnabled(has_employees and current_index > 0)
        self.prev_btn.setEnabled(has_employees and current_index > 0)
        self.next_btn.setEnabled(has_employees and current_index < len(self.employees) - 1)
        self.last_btn.setEnabled(has_employees and current_index < len(self.employees) - 1)
        
        if has_employees:
            self.employee_count_label.setText(
                f"موظف {current_index + 1} من {len(self.employees)}"
            )
        else:
            self.employee_count_label.setText("لا يوجد موظفين")
        
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
            employee = self.employees[self.current_employee_index]
            self.load_employee(employee)
            self.update_navigation_buttons()

    def new_employee(self):
        self.employee_id = None
        self.clear_form()
        self.current_employee_index = -1
        self.update_navigation_buttons()

    def clear_form(self):
        self.name_edit.clear()
        self.name_ar_edit.clear()
        self.dob_edit.setDate(QDate.currentDate())
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
        self.photo_label.clear()
        self.photo_path = None

    def delete_employee(self):
        if not self.employee_id:
            return
            
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الموظف؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.employee_controller.delete_employee(self.employee_id)
            if success:
                QMessageBox.information(self, "نجاح", "تم حذف الموظف بنجاح")
                self.load_employees()
                if self.employees:
                    self.current_employee_index = 0
                    self.load_current_employee()
                else:
                    self.clear_form()
                    self.update_navigation_buttons()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في حذف الموظف: {error}")

    def load_employees(self):
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.employees = employees
            if self.employees:
                self.current_employee_index = 0
                self.load_current_employee()
            self.update_navigation_buttons()

    def upload_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "اختر صورة",
            "",
            "Image files (*.jpg *.jpeg *.png *.bmp)"
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
        valid, error = ValidationUtils.validate_employee_data(data)
        if not valid:
            QMessageBox.warning(self, "خطأ في التحقق", error)
            return
        
        if self.employee_id:  # Update existing employee
            success, error = self.employee_controller.update_employee(self.employee_id, data)
            if success:
                QMessageBox.information(self, "نجاح", "تم تحديث بيانات الموظف بنجاح")
                self.load_employees()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في تحديث بيانات الموظف: {error}")
        else:  # Add new employee
            success, error = self.employee_controller.add_employee(data)
            if success:
                QMessageBox.information(self, "نجاح", "تم إضافة الموظف بنجاح")
                self.load_employees()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في إضافة الموظف: {error}")

    def get_form_data(self):
        """Get all form data as a dictionary."""
        return {
            'name': self.name_edit.text().strip(),
            'name_ar': self.name_ar_edit.text().strip(),
            'dob': self.dob_edit.date().toString('yyyy-MM-dd'),
            'gender': self.gender_combo.currentText().strip(),
            'nationality': self.nationality_edit.currentText().strip(),
            'national_id': self.national_id_edit.text().strip(),
            'passport': self.passport_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'phone2': self.phone2_edit.text().strip(),
            'email': self.email_edit.text().strip(),
            'address': self.address_edit.toPlainText().strip(),
            'department': self.department_combo.currentText().strip(),
            'position': self.position_combo.currentText().strip(),
            'hire_date': self.hire_date_edit.date().toString('yyyy-MM-dd'),
            'contract_type': self.contract_type_combo.currentText().strip(),
            'bank_account': self.bank_account_edit.text().strip(),
            'salary_type': self.salary_type_combo.currentText().strip(),
            'basic_salary': self.basic_salary_spin.value(),
            'currency': self.currency_combo.currentText().strip()
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
        self.address_edit.setText(employee_data.get('address', ''))
        
        # Employment Details
        self.department_combo.setCurrentText(employee_data.get('department', ''))
        self.position_combo.setCurrentText(employee_data.get('position', ''))
        self.hire_date_edit.setDate(ValidationUtils.parse_date(employee_data.get('hire_date')))
        self.contract_type_combo.setCurrentText(employee_data.get('contract_type', ''))
        self.bank_account_edit.setText(employee_data.get('bank_account', ''))
        self.salary_type_combo.setCurrentText(employee_data.get('salary_type', ''))
        self.basic_salary_spin.setValue(float(employee_data.get('basic_salary', 0)))
        self.currency_combo.setCurrentText(employee_data.get('currency', ''))
