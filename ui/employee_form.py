from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QTabWidget, QWidget,
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
                             QTextEdit, QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QPixmap
import os
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
        self.filtered_employees = []
        self.init_ui()
        self.load_employees()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Search and Filter Group
        search_group = QGroupBox("بحث وتصفية")
        search_layout = QVBoxLayout()
        
        # Search bar
        search_bar_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث عن موظف...")
        self.search_edit.textChanged.connect(self.apply_filters)
        search_bar_layout.addWidget(self.search_edit)
        
        # Filter options
        filter_layout = QHBoxLayout()
        
        # Department filter
        self.filter_dept_combo = QComboBox()
        self.filter_dept_combo.addItem("كل الأقسام")
        self.filter_dept_combo.addItems([
            "الموارد البشرية", "المالية", "تقنية المعلومات", "المبيعات",
            "التسويق", "خدمة العملاء", "الإدارة", "المشتريات", "المستودعات"
        ])
        self.filter_dept_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("القسم:"))
        filter_layout.addWidget(self.filter_dept_combo)
        
        # Status filter
        self.filter_status_combo = QComboBox()
        self.filter_status_combo.addItems(["الكل", "نشط", "غير نشط"])
        self.filter_status_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("الحالة:"))
        filter_layout.addWidget(self.filter_status_combo)
        
        # Salary range filter
        self.filter_salary_combo = QComboBox()
        self.filter_salary_combo.addItems([
            "كل الرواتب",
            "أقل من 5,000",
            "5,000 - 10,000",
            "10,000 - 15,000",
            "15,000 - 20,000",
            "أكثر من 20,000"
        ])
        self.filter_salary_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("نطاق الراتب:"))
        filter_layout.addWidget(self.filter_salary_combo)
        
        search_layout.addLayout(search_bar_layout)
        search_layout.addLayout(filter_layout)
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Navigation buttons at the top
        nav_layout, action_layout = self.setup_navigation_buttons()
        
        layout.addLayout(nav_layout)
        
        # Header with photo
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        
        # Photo section
        photo_layout = QVBoxLayout()
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet("border: 1px solid #ccc;")
        photo_layout.addWidget(self.photo_label)
        
        upload_btn = QPushButton("تحميل صورة")
        upload_btn.clicked.connect(self.select_photo)
        photo_layout.addWidget(upload_btn)
        
        header_layout.addLayout(photo_layout)
        header_layout.addStretch()
        
        layout.addWidget(header_widget)
        
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
        self.name_edit.setPlaceholderText("الاسم الكامل")
        self.name_edit.setToolTip("أدخل الاسم الكامل باللغة العربية أو الإنجليزية")
        layout.addRow("الاسم:", self.name_edit)
        
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("الاسم باللغة العربية")
        self.name_ar_edit.setToolTip("أدخل الاسم الكامل باللغة العربية")
        layout.addRow("الاسم بالعربية:", self.name_ar_edit)
        
        # Date of Birth
        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        self.dob_edit.setToolTip("اختر تاريخ الميلاد من التقويم")
        layout.addRow("تاريخ الميلاد:", self.dob_edit)
        
        # Gender
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(['male', 'female'])  # Database values
        self.gender_display = {
            'male': 'ذكر',
            'female': 'أنثى'
        }
        # Set display text while keeping the data role as the database value
        for i in range(self.gender_combo.count()):
            db_value = self.gender_combo.itemText(i)
            self.gender_combo.setItemText(i, self.gender_display[db_value])
            self.gender_combo.setItemData(i, db_value)  # Store DB value
        self.gender_combo.setToolTip("اختر الجنس")
        layout.addRow("الجنس:", self.gender_combo)
        
        # Marital Status
        self.marital_status_combo = QComboBox()
        self.marital_status_combo.addItems(["أعزب", "متزوج", "مطلق", "أرمل"])
        self.marital_status_combo.setToolTip("اختر الحالة الاجتماعية")
        layout.addRow("الحالة الاجتماعية:", self.marital_status_combo)
        
        # Nationality
        self.nationality_edit = QComboBox()
        self.nationality_edit.setEditable(True)
        self.nationality_edit.addItems([
            "سعودي", "إماراتي", "كويتي", "بحريني", "عماني", "قطري", "مصري",
            "أردني", "لبناني", "سوري", "عراقي", "يمني", "سوداني", "فلسطيني"
        ])
        self.nationality_edit.setToolTip("اختر الجنسية أو أدخل جنسية جديدة")
        layout.addRow("الجنسية:", self.nationality_edit)
        
        # ID Numbers
        self.national_id_edit = QLineEdit()
        self.national_id_edit.setPlaceholderText("10-14 رقم")
        self.national_id_edit.setToolTip("أدخل رقم الهوية (10-14 رقم)")
        layout.addRow("رقم الهوية:", self.national_id_edit)
        
        self.passport_edit = QLineEdit()
        self.passport_edit.setPlaceholderText("مثال: A1234567")
        self.passport_edit.setToolTip("أدخل رقم جواز السفر (6-9 أحرف وأرقام)")
        layout.addRow("رقم جواز السفر:", self.passport_edit)
        
        tab.setLayout(layout)
        return tab

    def setup_contact_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        
        # Phone numbers
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("05xxxxxxxx")
        self.phone_edit.setToolTip("أدخل رقم الهاتف (8-15 رقم)")
        layout.addRow("رقم الهاتف:", self.phone_edit)
        
        self.phone2_edit = QLineEdit()
        self.phone2_edit.setPlaceholderText("05xxxxxxxx (اختياري)")
        self.phone2_edit.setToolTip("أدخل رقم الهاتف البديل (8-15 رقم)")
        layout.addRow("رقم الهاتف البديل:", self.phone2_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("example@domain.com")
        self.email_edit.setToolTip("أدخل البريد الإلكتروني بالصيغة الصحيحة")
        layout.addRow("البريد الإلكتروني:", self.email_edit)
        
        # Address
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(100)
        self.address_edit.setPlaceholderText("أدخل العنوان التفصيلي")
        self.address_edit.setToolTip("أدخل العنوان التفصيلي متضمناً المدينة والحي والشارع")
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
        self.department_combo.setToolTip("اختر القسم أو أدخل قسم جديد")
        layout.addRow("القسم:", self.department_combo)
        
        # Position
        self.position_combo = QComboBox()
        self.position_combo.setEditable(True)
        self.position_combo.addItems([
            "مدير", "مشرف", "موظف", "محاسب", "مهندس", "فني",
            "مندوب مبيعات", "سكرتير", "مدخل بيانات"
        ])
        self.position_combo.setToolTip("اختر المنصب أو أدخل منصب جديد")
        layout.addRow("المنصب:", self.position_combo)
        
        # Hire Date
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        self.hire_date_edit.setToolTip("اختر تاريخ التعيين من التقويم")
        layout.addRow("تاريخ التعيين:", self.hire_date_edit)
        
        # Contract Type
        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems([
            "دوام كامل", "دوام جزئي", "عقد", "مؤقت",
            "موسمي", "تجريبي", "عن بعد"
        ])
        self.contract_type_combo.setToolTip("اختر نوع العقد")
        layout.addRow("نوع العقد:", self.contract_type_combo)
        
        # Bank Account
        self.bank_account_edit = QLineEdit()
        self.bank_account_edit.setPlaceholderText("SA1234567890123456789012")
        self.bank_account_edit.setToolTip("أدخل رقم الآيبان (IBAN) المكون من 24 رقم")
        layout.addRow("رقم الحساب البنكي:", self.bank_account_edit)
        
        # Salary Type
        self.salary_type_combo = QComboBox()
        self.salary_type_combo.addItems([
            "شهري", "أسبوعي", "يومي", "بالساعة",
            "بالمشروع", "بالعمولة"
        ])
        self.salary_type_combo.setToolTip("اختر نوع الراتب")
        layout.addRow("نوع الراتب:", self.salary_type_combo)
        
        # Basic Salary
        self.basic_salary_edit = QLineEdit()
        self.basic_salary_edit.setPlaceholderText("0.00")
        self.basic_salary_edit.setToolTip("أدخل قيمة الراتب الأساسي")
        layout.addRow("الراتب الأساسي:", self.basic_salary_edit)
        
        # Currency
        self.currency_combo = QComboBox()
        self.currency_combo.addItems([
            "ريال سعودي", "درهم إماراتي", "دينار كويتي", "دينار بحريني",
            "ريال عماني", "ريال قطري", "جنيه مصري", "دولار أمريكي", "يورو"
        ])
        self.currency_combo.setToolTip("اختر عملة الراتب")
        layout.addRow("العملة:", self.currency_combo)
        
        # Working Hours
        self.working_hours_edit = QLineEdit()
        self.working_hours_edit.setPlaceholderText("40")
        self.working_hours_edit.setToolTip("أدخل عدد ساعات العمل الأسبوعية")
        layout.addRow("ساعات العمل الأسبوعية:", self.working_hours_edit)
        
        # Bank Name
        self.bank_name_edit = QLineEdit()
        self.bank_name_edit.setPlaceholderText("اسم البنك")
        self.bank_name_edit.setToolTip("أدخل اسم البنك")
        layout.addRow("اسم البنك:", self.bank_name_edit)
        
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
        """Update the state of navigation buttons based on current position"""
        has_employees = len(self.filtered_employees) > 0
        current_index = self.current_employee_index
        
        self.first_btn.setEnabled(has_employees and current_index > 0)
        self.prev_btn.setEnabled(has_employees and current_index > 0)
        self.next_btn.setEnabled(has_employees and current_index < len(self.filtered_employees) - 1)
        self.last_btn.setEnabled(has_employees and current_index < len(self.filtered_employees) - 1)
        self.delete_btn.setEnabled(has_employees and self.employee_id is not None)
        
        if has_employees and current_index >= 0:
            self.employee_count_label.setText(
                f"موظف {current_index + 1} من {len(self.filtered_employees)} (الإجمالي: {len(self.employees)})"
            )
        else:
            self.employee_count_label.setText("لا يوجد موظفين")

    def go_to_first(self):
        if self.filtered_employees:
            self.current_employee_index = 0
            self.load_current_employee()

    def go_to_previous(self):
        if self.current_employee_index > 0:
            self.current_employee_index -= 1
            self.load_current_employee()

    def go_to_next(self):
        if self.current_employee_index < len(self.filtered_employees) - 1:
            self.current_employee_index += 1
            self.load_current_employee()

    def go_to_last(self):
        if self.filtered_employees:
            self.current_employee_index = len(self.filtered_employees) - 1
            self.load_current_employee()

    def load_current_employee(self):
        """Load the currently selected employee into the form"""
        if 0 <= self.current_employee_index < len(self.filtered_employees):
            employee = self.filtered_employees[self.current_employee_index]
            self.employee_id = employee.get('id')  # Set employee_id here
            self.load_employee(employee)
        else:
            self.employee_id = None
            self.clear_form()
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
        self.marital_status_combo.setCurrentIndex(0)
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
        self.basic_salary_edit.clear()
        self.currency_combo.setCurrentIndex(0)
        self.working_hours_edit.clear()
        self.bank_name_edit.clear()
        self.photo_label.clear()
        self.photo_path = None

    def delete_employee(self):
        if not self.employee_id:
            QMessageBox.warning(self, "خطأ", "لم يتم تحديد موظف للحذف")
            return
            
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الموظف؟\nسيتم حذف جميع البيانات المتعلقة به مثل الرواتب والحضور والإجازات.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, error = self.employee_controller.delete_employee(self.employee_id)
            if success:
                QMessageBox.information(self, "نجاح", "تم حذف الموظف وجميع البيانات المتعلقة به بنجاح")
                # Remove the deleted employee from the list
                self.employees = [emp for emp in self.employees if emp['id'] != self.employee_id]
                self.filtered_employees = [emp for emp in self.filtered_employees if emp['id'] != self.employee_id]
                self.employee_id = None
                
                # Update navigation
                if self.filtered_employees:
                    if self.current_employee_index >= len(self.filtered_employees):
                        self.current_employee_index = len(self.filtered_employees) - 1
                    self.load_current_employee()
                else:
                    self.current_employee_index = -1
                    self.clear_form()
                self.update_navigation_buttons()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في حذف الموظف: {error}")

    def load_employees(self):
        """Load all employees and initialize the form"""
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.employees = employees
            self.filtered_employees = employees.copy()
            
            # Only reset current_employee_index if there are no employees
            # or if it's the first load (current_employee_index == -1)
            if not employees:
                self.current_employee_index = -1
                self.employee_id = None
                self.clear_form()
            elif self.current_employee_index == -1 and employees:
                self.current_employee_index = 0
                self.load_current_employee()
                
            self.update_navigation_buttons()
        else:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل بيانات الموظفين: {employees}")
            self.employees = []
            self.filtered_employees = []
            self.current_employee_index = -1
            self.employee_id = None
            self.clear_form()
            self.update_navigation_buttons()

    def select_photo(self):
        """Open file dialog to select employee photo"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "اختر صورة",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            # Store the photo path for later use
            self.photo_path = file_name
            # Display the selected photo
            pixmap = QPixmap(file_name)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.photo_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.photo_label.setPixmap(scaled_pixmap)

    def get_form_data(self):
        """Get all form data as a dictionary"""
        data = {
            'name': self.name_edit.text(),
            'name_ar': self.name_ar_edit.text(),
            'department_id': self.department_combo.currentData(),
            'position_id': self.position_combo.currentData(),
            'basic_salary': float(self.basic_salary_edit.text() or 0),
            'hire_date': self.hire_date_edit.date().toString('yyyy-MM-dd'),
            'birth_date': self.dob_edit.date().toString('yyyy-MM-dd'),
            'gender': self.gender_combo.currentData(),
            'marital_status': self.marital_status_combo.currentText(),
            'national_id': self.national_id_edit.text(),
            'phone': self.phone_edit.text(),
            'email': self.email_edit.text(),
            'address': self.address_edit.toPlainText(),
            'bank_account': self.bank_account_edit.text(),
            'bank_name': self.bank_name_edit.text(),
            'is_active': 1
        }
        
        # Add photo path if a new photo was selected
        if hasattr(self, 'photo_path'):
            data['photo_path'] = self.photo_path
            
        return data

    def load_employee(self, employee_data):
        """Load employee data into the form"""
        if not employee_data:
            return

        # Basic Information
        self.name_edit.setText(employee_data.get('name', ''))
        self.name_ar_edit.setText(employee_data.get('name_ar', ''))
        self.email_edit.setText(employee_data.get('email', ''))
        self.phone_edit.setText(employee_data.get('phone', ''))
        self.national_id_edit.setText(employee_data.get('national_id', ''))
        self.address_edit.setPlainText(employee_data.get('address', ''))
        
        # Display photo if available
        if 'photo_pixmap' in employee_data and employee_data['photo_pixmap']:
            scaled_pixmap = employee_data['photo_pixmap'].scaled(
                self.photo_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.photo_label.setPixmap(scaled_pixmap)
        else:
            self.photo_label.clear()
            
        # Clear the stored photo path when loading new employee
        if hasattr(self, 'photo_path'):
            del self.photo_path
            
        # Dates
        if employee_data.get('birth_date'):
            self.dob_edit.setDate(QDate.fromString(employee_data['birth_date'], 'yyyy-MM-dd'))
        else:
            self.dob_edit.setDate(QDate.currentDate())
            
        if employee_data.get('hire_date'):
            self.hire_date_edit.setDate(QDate.fromString(employee_data['hire_date'], 'yyyy-MM-dd'))
        else:
            self.hire_date_edit.setDate(QDate.currentDate())
            
        # Gender - find by database value
        gender = employee_data.get('gender', 'male')
        index = self.gender_combo.findData(gender)
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)
            
        # Marital Status
        marital_status = employee_data.get('marital_status', 'أعزب')
        index = self.marital_status_combo.findText(marital_status)
        if index >= 0:
            self.marital_status_combo.setCurrentIndex(index)
            
        # Department
        department_id = employee_data.get('department_id')
        if department_id:
            index = self.department_combo.findData(department_id)
            if index >= 0:
                self.department_combo.setCurrentIndex(index)
                
        # Position
        position_id = employee_data.get('position_id')
        if position_id:
            index = self.position_combo.findData(position_id)
            if index >= 0:
                self.position_combo.setCurrentIndex(index)
            
        # Bank Account and Salary
        self.bank_account_edit.setText(employee_data.get('bank_account', ''))
        self.bank_name_edit.setText(employee_data.get('bank_name', ''))
        self.basic_salary_edit.setText(str(employee_data.get('basic_salary', 0) or 0))
        
    def save_employee(self):
        data = self.get_form_data()
        
        # Validate data
        valid, error = ValidationUtils.validate_employee_data(data)
        if not valid:
            QMessageBox.warning(
                self,
                "خطأ في التحقق",
                f"{error}\n\nملاحظات:\n" +
                "• الاسم وتاريخ التعيين فقط مطلوبين\n" +
                "• رقم الهاتف يجب أن يكون 8-15 رقم\n" +
                "• البريد الإلكتروني يجب أن يكون بالصيغة الصحيحة\n" +
                "• رقم الهوية يجب أن يكون 10-14 رقم\n" +
                "• رقم جواز السفر يجب أن يكون 6-9 أحرف وأرقام"
            )
            return
        
        current_id = self.employee_id
        if current_id:  # Update existing employee
            success, error = self.employee_controller.update_employee(current_id, data)
            if success:
                QMessageBox.information(self, "نجاح", "تم تحديث بيانات الموظف بنجاح")
                # Reload employees while maintaining current position
                self.load_employees()
                # Find and select the updated employee
                for i, emp in enumerate(self.filtered_employees):
                    if emp['id'] == current_id:
                        self.current_employee_index = i
                        self.load_current_employee()
                        break
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في تحديث بيانات الموظف: {error}")
        else:  # Add new employee
            success, error = self.employee_controller.add_employee(data)
            if success:
                QMessageBox.information(self, "نجاح", "تم إضافة الموظف بنجاح")
                # Reload employees and select the new employee (which will be first in the list)
                self.load_employees()
                if self.filtered_employees:
                    self.current_employee_index = 0
                    self.load_current_employee()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في إضافة الموظف: {error}")

    def apply_filters(self):
        """Apply search and filter criteria to employees list"""
        search_text = self.search_edit.text().lower()
        department = self.filter_dept_combo.currentText()
        status = self.filter_status_combo.currentText()
        salary_range = self.filter_salary_combo.currentText()
        
        self.filtered_employees = []
        
        for emp in self.employees:
            # Check search text
            if search_text and not any(search_text in str(value).lower() 
                                     for value in emp.values()):
                continue
            
            # Check department
            if department != "كل الأقسام" and emp.get('department_name') != department:
                continue
            
            # Check status
            if status != "الكل" and emp.get('employee_status') != status:
                continue
            
            # Check salary range
            salary = float(emp.get('basic_salary', 0) or 0)
            if salary_range != "كل الرواتب":
                if salary_range == "أقل من 5,000" and salary >= 5000:
                    continue
                elif salary_range == "5,000 - 10,000" and (salary < 5000 or salary >= 10000):
                    continue
                elif salary_range == "10,000 - 15,000" and (salary < 10000 or salary >= 15000):
                    continue
                elif salary_range == "15,000 - 20,000" and (salary < 15000 or salary >= 20000):
                    continue
                elif salary_range == "أكثر من 20,000" and salary < 20000:
                    continue
            
            self.filtered_employees.append(emp)
        
        # Reset navigation
        self.current_employee_index = -1 if not self.filtered_employees else 0
        self.load_current_employee()
        self.update_navigation_buttons()
