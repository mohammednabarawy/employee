from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QFileDialog, QTabWidget, QWidget,
                             QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
                             QTextEdit, QFormLayout, QGroupBox, QFrame)
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
        photo_layout = self.setup_photo_section()
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
        dept_layout = QHBoxLayout()
        self.department_combo = QComboBox()
        
        # Load departments from database
        success, departments = self.employee_controller.get_departments()
        if success:
            # Add departments to combo box
            for dept in departments:
                self.department_combo.addItem(dept['name'], dept['id'])
            
            # Set default value to first department if available
            if departments and len(departments) > 0:
                self.department_combo.setCurrentIndex(0)
        
        add_dept_btn = QPushButton("+")
        add_dept_btn.setMaximumWidth(30)
        add_dept_btn.clicked.connect(self.add_new_department)
        
        dept_layout.addWidget(self.department_combo)
        dept_layout.addWidget(add_dept_btn)
        
        layout.addRow("القسم:", dept_layout)
        
        # Position
        pos_layout = QHBoxLayout()
        self.position_combo = QComboBox()
        
        # Load positions from database
        success, positions = self.employee_controller.get_positions()
        if success:
            # Add positions to combo box
            for pos in positions:
                self.position_combo.addItem(pos['name'], pos['id'])
            
            # Set default value to first position if available
            if positions and len(positions) > 0:
                self.position_combo.setCurrentIndex(0)
        
        add_pos_btn = QPushButton("+")
        add_pos_btn.setMaximumWidth(30)
        add_pos_btn.clicked.connect(self.add_new_position)
        
        pos_layout.addWidget(self.position_combo)
        pos_layout.addWidget(add_pos_btn)
        
        layout.addRow("المسمى الوظيفي:", pos_layout)
        
        # Hire Date
        self.hire_date_edit = QDateEdit()
        self.hire_date_edit.setCalendarPopup(True)
        self.hire_date_edit.setDate(QDate.currentDate())
        layout.addRow("تاريخ التعيين:", self.hire_date_edit)
        
        # Contract Type
        self.contract_type_combo = QComboBox()
        self.contract_type_combo.addItems(["دائم", "مؤقت", "متعاقد", "دوام جزئي"])
        layout.addRow("نوع العقد:", self.contract_type_combo)
        
        # Salary Type
        self.salary_type_combo = QComboBox()
        self.salary_type_combo.addItems(["شهري", "أسبوعي", "يومي", "بالساعة"])
        layout.addRow("نوع الراتب:", self.salary_type_combo)
        
        # Basic Salary
        self.basic_salary_edit = QLineEdit()
        self.basic_salary_edit.setPlaceholderText("أدخل الراتب الأساسي")
        layout.addRow("الراتب الأساسي:", self.basic_salary_edit)
        
        # Currency
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["ريال", "دولار", "يورو", "جنيه"])
        layout.addRow("العملة:", self.currency_combo)
        
        # Working Hours
        self.working_hours_edit = QLineEdit()
        self.working_hours_edit.setPlaceholderText("عدد ساعات العمل")
        layout.addRow("ساعات العمل:", self.working_hours_edit)
        
        # Bank Account
        self.bank_account_edit = QLineEdit()
        self.bank_account_edit.setPlaceholderText("رقم الحساب البنكي")
        layout.addRow("رقم الحساب:", self.bank_account_edit)
        
        # Bank Name
        self.bank_name_edit = QLineEdit()
        self.bank_name_edit.setPlaceholderText("اسم البنك")
        layout.addRow("اسم البنك:", self.bank_name_edit)
        
        # Employee Status
        status_layout = QHBoxLayout()
        self.status_label = QLabel("حالة الموظف:")
        self.status_toggle = QPushButton("نشط")
        self.status_toggle.setCheckable(True)
        self.status_toggle.setChecked(True)
        self.status_toggle.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:checked {
                background-color: #e74c3c;
            }
        """)
        self.status_toggle.clicked.connect(self.toggle_employee_status)
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.status_toggle)
        status_layout.addStretch()
        
        layout.addRow(status_layout)
        
        tab.setLayout(layout)
        return tab
        
    def toggle_employee_status(self):
        """Toggle employee active status"""
        if self.status_toggle.isChecked():
            self.status_toggle.setText("نشط")
            self.status_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:checked {
                    background-color: #e74c3c;
                }
            """)
        else:
            self.status_toggle.setText("غير نشط")
            self.status_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:checked {
                    background-color: #27ae60;
                }
            """)
            
    def setup_navigation_buttons(self):
        """Setup navigation buttons."""
        nav_layout = QHBoxLayout()
        action_layout = QHBoxLayout()
        
        # Navigation buttons
        self.first_btn = QPushButton("<<")
        self.first_btn.setToolTip("الأول")
        self.first_btn.clicked.connect(self.go_to_first)
        
        self.prev_btn = QPushButton("<")
        self.prev_btn.setToolTip("السابق")
        self.prev_btn.clicked.connect(self.go_to_previous)
        
        self.next_btn = QPushButton(">")
        self.next_btn.setToolTip("التالي")
        self.next_btn.clicked.connect(self.go_to_next)
        
        self.last_btn = QPushButton(">>")
        self.last_btn.setToolTip("الأخير")
        self.last_btn.clicked.connect(self.go_to_last)
        
        # Navigation counter
        self.nav_counter = QLabel("0/0")
        
        nav_layout.addWidget(self.first_btn)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.nav_counter)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.last_btn)
        nav_layout.addStretch()
        
        # Action buttons
        self.new_btn = QPushButton("جديد")
        self.new_btn.setToolTip("إضافة موظف جديد")
        self.new_btn.clicked.connect(self.new_employee)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.setToolTip("حفظ بيانات الموظف")
        self.save_btn.clicked.connect(self.save_employee)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.setToolTip("حذف الموظف الحالي")
        self.delete_btn.clicked.connect(self.delete_employee)
        
        self.export_btn = QPushButton("تصدير")
        self.export_btn.setToolTip("تصدير بيانات الموظفين إلى ملف CSV")
        self.export_btn.clicked.connect(self.export_employees)
        
        action_layout.addWidget(self.new_btn)
        action_layout.addWidget(self.save_btn)
        action_layout.addWidget(self.delete_btn)
        action_layout.addWidget(self.export_btn)
        
        return nav_layout, action_layout
        
    def export_employees(self):
        """Export employees data to CSV file"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير بيانات الموظفين",
            "employees.csv",
            "CSV Files (*.csv)"
        )
        
        if file_name:
            success, result = self.employee_controller.export_employees_to_csv(file_name)
            if success:
                QMessageBox.information(
                    self,
                    "تم التصدير بنجاح",
                    f"تم تصدير بيانات الموظفين بنجاح إلى:\n{result}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "خطأ في التصدير",
                    f"حدث خطأ أثناء تصدير البيانات:\n{result}"
                )
                
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
            self.nav_counter.setText(
                f"{current_index + 1}/{len(self.filtered_employees)}"
            )
        else:
            self.nav_counter.setText("0/0")

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
        employees = self.employee_controller.get_all_employees()
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
            'is_active': 1 if self.status_toggle.isChecked() else 0
        }
        
        # Always include photo_path in the data dictionary, even if it's None
        # This allows us to explicitly clear the photo when photo_path is None
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
            # Reset photo_path to indicate we're using the existing photo from the database
            self.photo_path = ''
        else:
            self.photo_label.clear()
            # Reset photo_path to None to indicate there's no photo
            self.photo_path = None
            
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
        
        # Status toggle
        is_active = employee_data.get('is_active', 1)
        self.status_toggle.setChecked(is_active == 1)
        if is_active == 1:
            self.status_toggle.setText("نشط")
            self.status_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:checked {
                    background-color: #e74c3c;
                }
            """)
        else:
            self.status_toggle.setText("غير نشط")
            self.status_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border-radius: 4px;
                    padding: 5px 10px;
                }
                QPushButton:checked {
                    background-color: #27ae60;
                }
            """)
            
    def setup_photo_section(self):
        """Setup employee photo section"""
        photo_layout = QHBoxLayout()
        
        # Photo display
        photo_frame = QFrame()
        photo_frame.setFrameShape(QFrame.StyledPanel)
        photo_frame.setFixedSize(150, 150)
        photo_frame_layout = QVBoxLayout(photo_frame)
        
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setFixedSize(140, 140)
        self.photo_label.setStyleSheet("background-color: #f0f0f0; border-radius: 5px;")
        photo_frame_layout.addWidget(self.photo_label)
        
        # Photo buttons
        photo_buttons_layout = QVBoxLayout()
        
        self.select_photo_btn = QPushButton("اختيار صورة")
        self.select_photo_btn.setToolTip("اختر صورة للموظف")
        self.select_photo_btn.clicked.connect(self.select_photo)
        
        self.clear_photo_btn = QPushButton("حذف الصورة")
        self.clear_photo_btn.setToolTip("حذف صورة الموظف")
        self.clear_photo_btn.clicked.connect(self.clear_photo)
        
        photo_buttons_layout.addWidget(self.select_photo_btn)
        photo_buttons_layout.addWidget(self.clear_photo_btn)
        photo_buttons_layout.addStretch()
        
        photo_layout.addWidget(photo_frame)
        photo_layout.addLayout(photo_buttons_layout)
        photo_layout.addStretch()
        
        return photo_layout
        
    def clear_photo(self):
        """Clear the employee photo"""
        self.photo_label.clear()
        # Set photo_path to None explicitly to indicate that the photo should be removed from the database
        self.photo_path = None
        
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
            success, result = self.employee_controller.update_employee(current_id, data)
            if success:
                QMessageBox.information(self, "نجاح", "تم تحديث بيانات الموظف بنجاح")
                
                # Update the employee in the employees list
                for i, emp in enumerate(self.employees):
                    if emp['id'] == current_id:
                        self.employees[i] = result
                        break
                
                # Update the employee in the filtered_employees list
                for i, emp in enumerate(self.filtered_employees):
                    if emp['id'] == current_id:
                        self.filtered_employees[i] = result
                        self.current_employee_index = i
                        break
                
                # Load the updated employee directly
                self.load_employee(result)
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في تحديث بيانات الموظف: {result}")
        else:  # Add new employee
            success, result = self.employee_controller.add_employee(data)
            if success:
                QMessageBox.information(self, "نجاح", "تم إضافة الموظف بنجاح")
                # Reload employees and select the new employee
                self.load_employees()
                if self.filtered_employees:
                    self.current_employee_index = 0
                    self.load_current_employee()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل في إضافة الموظف: {result}")

    def apply_filters(self):
        """Apply search and filter criteria to employees list"""
        search_text = self.search_edit.text().lower()
        department = self.filter_dept_combo.currentText()
        status = self.filter_status_combo.currentText()
        salary_range = self.filter_salary_combo.currentText()
        
        self.filtered_employees = []
        
        for emp in self.employees:
            # Check search text - search in specific fields
            if search_text:
                search_fields = ['name', 'name_ar', 'code', 'email', 'phone', 'national_id', 'position_name', 'department_name']
                found = False
                for field in search_fields:
                    if field in emp and search_text in str(emp.get(field, '')).lower():
                        found = True
                        break
                if not found:
                    continue
            
            # Check department
            if department != "كل الأقسام" and emp.get('department_name') != department:
                continue
            
            # Check status - fix to use is_active field
            if status != "الكل":
                is_active = emp.get('is_active', 1)
                if status == "نشط" and is_active != 1:
                    continue
                elif status == "غير نشط" and is_active == 1:
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

    def add_new_department(self):
        """Open dialog to add a new department"""
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة قسم جديد")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # Department name
        name_layout = QFormLayout()
        name_edit = QLineEdit()
        name_layout.addRow("اسم القسم:", name_edit)
        
        # Department name in Arabic
        name_ar_layout = QFormLayout()
        name_ar_edit = QLineEdit()
        name_ar_layout.addRow("اسم القسم (عربي):", name_ar_edit)
        
        # Department description
        desc_layout = QFormLayout()
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(100)
        desc_layout.addRow("الوصف:", desc_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        cancel_btn = QPushButton("إلغاء")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(name_layout)
        layout.addLayout(name_ar_layout)
        layout.addLayout(desc_layout)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connect buttons
        cancel_btn.clicked.connect(dialog.reject)
        
        def save_department():
            dept_name = name_edit.text().strip()
            if not dept_name:
                QMessageBox.warning(dialog, "خطأ", "يجب إدخال اسم القسم")
                return
                
            dept_data = {
                'name': dept_name,
                'name_ar': name_ar_edit.text().strip(),
                'description': desc_edit.toPlainText(),
                'is_active': 1
            }
            
            success, result = self.employee_controller.add_department(dept_data)
            if success:
                QMessageBox.information(dialog, "نجاح", "تم إضافة القسم بنجاح")
                # Add the new department to the combobox
                self.department_combo.addItem(dept_data['name'], result)
                # Select the newly added department
                index = self.department_combo.findData(result)
                if index >= 0:
                    self.department_combo.setCurrentIndex(index)
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "خطأ", f"فشل في إضافة القسم: {result}")
        
        save_btn.clicked.connect(save_department)
        
        dialog.exec_()
        
    def add_new_position(self):
        """Open dialog to add a new position"""
        dialog = QDialog(self)
        dialog.setWindowTitle("إضافة مسمى وظيفي جديد")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        # Position name
        name_layout = QFormLayout()
        name_edit = QLineEdit()
        name_layout.addRow("المسمى الوظيفي:", name_edit)
        
        # Position name in Arabic
        name_ar_edit = QLineEdit()
        name_layout.addRow("المسمى الوظيفي (عربي):", name_ar_edit)
        
        # Department selection
        dept_layout = QFormLayout()
        dept_combo = QComboBox()
        
        # Load departments from database
        success, departments = self.employee_controller.get_departments()
        if success:
            for dept in departments:
                dept_combo.addItem(dept['name'], dept['id'])
            
            # Set default value to first department if available
            if departments and len(departments) > 0:
                dept_combo.setCurrentIndex(0)
                
        dept_layout.addRow("القسم:", dept_combo)
        
        # Position description
        desc_layout = QFormLayout()
        desc_edit = QTextEdit()
        desc_edit.setMaximumHeight(100)
        desc_layout.addRow("الوصف:", desc_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("حفظ")
        cancel_btn = QPushButton("إلغاء")
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(name_layout)
        layout.addLayout(dept_layout)
        layout.addLayout(desc_layout)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        # Connect buttons
        cancel_btn.clicked.connect(dialog.reject)
        
        def save_position():
            pos_name = name_edit.text().strip()
            if not pos_name:
                QMessageBox.warning(dialog, "خطأ", "يجب إدخال المسمى الوظيفي")
                return
                
            department_id = dept_combo.currentData()
            
            pos_data = {
                'name': pos_name,
                'name_ar': name_ar_edit.text().strip(),
                'department_id': department_id,
                'description': desc_edit.toPlainText(),
                'is_active': 1
            }
            
            success, result = self.employee_controller.add_position(pos_data)
            if success:
                QMessageBox.information(dialog, "نجاح", "تم إضافة المسمى الوظيفي بنجاح")
                # Add the new position to the combobox
                self.position_combo.addItem(pos_data['name'], result)
                # Select the newly added position
                index = self.position_combo.findData(result)
                if index >= 0:
                    self.position_combo.setCurrentIndex(index)
                dialog.accept()
            else:
                QMessageBox.warning(dialog, "خطأ", f"فشل في إضافة المسمى الوظيفي: {result}")
        
        save_btn.clicked.connect(save_position)
        
        dialog.exec_()
