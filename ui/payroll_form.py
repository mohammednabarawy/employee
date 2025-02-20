from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QCalendarWidget, QDialog, QCheckBox, 
                             QDoubleSpinBox, QFormLayout, QDialogButtonBox, 
                             QTextEdit, QMenu, QLineEdit, QFrame)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
import qtawesome as qta
from datetime import datetime
from ui.styles import Styles

class AddEmployeeDialog(QDialog):
    def __init__(self, employee_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.selected_employees = []
        self.all_employees = []  # Initialize all_employees list
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("إضافة موظفين")
        self.setMinimumWidth(800)
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add employee list first
        self.employee_list = QTableWidget()
        self.employee_list.setColumnCount(5)
        self.employee_list.setHorizontalHeaderLabels([
            "تحديد", "الرقم", "الاسم", "القسم", "الراتب الأساسي"
        ])
        self.employee_list.setAlternatingRowColors(True)
        layout.addWidget(self.employee_list)
        
        # Create search and filter frame
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Add search box with icon
        search_layout = QHBoxLayout()
        search_icon = QLabel()
        search_icon.setPixmap(qta.icon('fa5s.search', color='#3498db').pixmap(16, 16))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("بحث عن موظف...")
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_box)
        filter_layout.addLayout(search_layout)
        
        # Add department filter with icon
        dept_layout = QHBoxLayout()
        dept_icon = QLabel()
        dept_icon.setPixmap(qta.icon('fa5s.building', color='#3498db').pixmap(16, 16))
        self.dept_combo = QComboBox()
        
        # Get departments
        success, departments = self.employee_controller.get_departments()
        if success:
            self.dept_combo.addItem("كل الأقسام", None)
            for dept in departments:
                self.dept_combo.addItem(dept['name'], dept['id'])
                
        dept_layout.addWidget(dept_icon)
        dept_layout.addWidget(self.dept_combo)
        filter_layout.addLayout(dept_layout)
        
        layout.addWidget(filter_frame)
        
        # Add select all checkbox with icon
        select_all_layout = QHBoxLayout()
        select_icon = QLabel()
        select_icon.setPixmap(qta.icon('fa5s.check-square', color='#3498db').pixmap(16, 16))
        self.select_all = QCheckBox("تحديد الكل")
        select_all_layout.addWidget(select_icon)
        select_all_layout.addWidget(self.select_all)
        layout.addLayout(select_all_layout)
        
        # Add buttons
        button_box = QDialogButtonBox()
        ok_button = button_box.addButton(QDialogButtonBox.Ok)
        cancel_button = button_box.addButton(QDialogButtonBox.Cancel)
        
        # Add icons to buttons
        ok_button.setIcon(qta.icon('fa5s.check', color='white'))
        cancel_button.setIcon(qta.icon('fa5s.times', color='white'))
        
        # Set button text
        ok_button.setText("موافق")
        cancel_button.setText("إلغاء")
        
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Load employees
        self.load_employees()
        
        # Connect signals after everything is set up
        self.search_box.textChanged.connect(self.filter_employees)
        self.dept_combo.currentIndexChanged.connect(self.filter_employees)
        self.select_all.stateChanged.connect(self.toggle_all)
        
    def load_employees(self):
        success, employees = self.employee_controller.get_active_employees()
        if not success:
            QMessageBox.warning(self, "خطأ", "حدث خطأ أثناء تحميل بيانات الموظفين: " + str(employees))
            return
            
        self.all_employees = employees
        self.filter_employees()
        
    def filter_employees(self):
        if not hasattr(self, 'all_employees') or not hasattr(self, 'employee_list'):
            return
            
        search_text = self.search_box.text().lower()
        selected_dept = self.dept_combo.currentData()
        
        filtered_employees = []
        for emp in self.all_employees:
            # Apply search filter
            if search_text and search_text not in emp['name'].lower():
                continue
                
            # Apply department filter
            if selected_dept and emp['department_id'] != selected_dept:
                continue
                
            filtered_employees.append(emp)
        
        self.employee_list.setRowCount(len(filtered_employees))
        for i, emp in enumerate(filtered_employees):
            # Add checkbox
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            self.employee_list.setItem(i, 0, checkbox)
            
            # Add employee info with icons
            id_item = QTableWidgetItem(str(emp['id']))
            id_item.setIcon(qta.icon('fa5s.id-badge', color='#3498db'))
            
            name_item = QTableWidgetItem(emp['name'])
            name_item.setIcon(qta.icon('fa5s.user', color='#3498db'))
            
            dept_item = QTableWidgetItem(emp.get('department_name', ''))
            dept_item.setIcon(qta.icon('fa5s.building', color='#3498db'))
            
            salary_item = QTableWidgetItem(f"{float(emp['basic_salary']):,.2f}")
            salary_item.setIcon(qta.icon('fa5s.money-bill', color='#3498db'))
            
            self.employee_list.setItem(i, 1, id_item)
            self.employee_list.setItem(i, 2, name_item)
            self.employee_list.setItem(i, 3, dept_item)
            self.employee_list.setItem(i, 4, salary_item)
            
        self.employee_list.resizeColumnsToContents()
        
    def toggle_all(self, state):
        for row in range(self.employee_list.rowCount()):
            self.employee_list.item(row, 0).setCheckState(
                Qt.Checked if state == Qt.Checked else Qt.Unchecked
            )
            
    def get_selected_employees(self):
        selected_ids = []
        for row in range(self.employee_list.rowCount()):
            if self.employee_list.item(row, 0).checkState() == Qt.Checked:
                employee_id = int(self.employee_list.item(row, 1).text())
                selected_ids.append(employee_id)
        return selected_ids

class EditEmployeePayrollDialog(QDialog):
    def __init__(self, payroll_controller, employee_data, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.employee_data = employee_data
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"تعديل راتب - {self.employee_data.get('name', '')}")
        layout = QFormLayout()
        self.setLayout(layout)

        # Basic salary
        self.basic_salary = QDoubleSpinBox()
        self.basic_salary.setMaximum(1000000)
        self.basic_salary.setValue(float(self.employee_data.get('basic_salary', 0)))
        layout.addRow("الراتب الأساسي:", self.basic_salary)

        # Allowances
        success, components = self.payroll_controller.get_salary_components('allowance')
        if success:
            self.allowance_fields = {}
            for comp in components:
                field = QDoubleSpinBox()
                field.setMaximum(1000000)
                value = comp.get('value')
                if value is not None:
                    field.setValue(float(value))
                else:
                    field.setValue(0.0)
                layout.addRow(f"{comp['name_ar']}:", field)
                self.allowance_fields[comp['id']] = field

        # Deductions
        success, components = self.payroll_controller.get_salary_components('deduction')
        if success:
            self.deduction_fields = {}
            for comp in components:
                field = QDoubleSpinBox()
                field.setMaximum(1000000)
                value = comp.get('value')
                if value is not None:
                    field.setValue(float(value))
                else:
                    field.setValue(0.0)
                layout.addRow(f"{comp['name_ar']}:", field)
                self.deduction_fields[comp['id']] = field

        # Payment method
        self.payment_method = QComboBox()
        success, methods = self.payroll_controller.get_payment_methods()
        if success:
            for method in methods:
                self.payment_method.addItem(method['name_ar'], method['id'])
        layout.addRow("طريقة الدفع:", self.payment_method)

        # Notes
        self.notes = QTextEdit()
        layout.addRow("ملاحظات:", self.notes)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_values(self):
        values = {
            'basic_salary': self.basic_salary.value(),
            'payment_method': self.payment_method.currentData(),
            'notes': self.notes.toPlainText(),
            'allowances': {comp_id: field.value() 
                         for comp_id, field in self.allowance_fields.items()},
            'deductions': {comp_id: field.value() 
                         for comp_id, field in self.deduction_fields.items()}
        }
        return values

class PayrollForm(QWidget):
    def __init__(self, payroll_controller, employee_controller):
        super().__init__()
        self.payroll_controller = payroll_controller
        self.employee_controller = employee_controller
        self.current_period_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add title
        title = QLabel("إدارة الرواتب")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Add period selector
        period_layout = QHBoxLayout()
        
        # Month selector
        month_label = QLabel("الشهر:")
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ])
        current_month = datetime.now().month
        self.month_combo.setCurrentIndex(current_month - 1)
        
        # Year selector
        year_label = QLabel("السنة:")
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        self.year_combo.addItems([str(year) for year in range(current_year - 2, current_year + 3)])
        self.year_combo.setCurrentText(str(current_year))
        
        period_layout.addWidget(month_label)
        period_layout.addWidget(self.month_combo)
        period_layout.addWidget(year_label)
        period_layout.addWidget(self.year_combo)
        layout.addLayout(period_layout)

        # Add action buttons
        button_layout = QHBoxLayout()
        
        self.create_period_btn = QPushButton("إنشاء فترة جديدة")
        self.create_period_btn.clicked.connect(self.create_period)
        
        self.add_employee_btn = QPushButton("إضافة موظفين")
        self.add_employee_btn.clicked.connect(self.add_employees)
        self.add_employee_btn.setEnabled(False)
        
        self.approve_btn = QPushButton("اعتماد كشف الرواتب")
        self.approve_btn.clicked.connect(self.approve_payroll)
        self.approve_btn.setEnabled(False)
        
        self.process_btn = QPushButton("صرف الرواتب")
        self.process_btn.clicked.connect(self.process_payroll)
        self.process_btn.setEnabled(False)
        
        button_layout.addWidget(self.create_period_btn)
        button_layout.addWidget(self.add_employee_btn)
        button_layout.addWidget(self.approve_btn)
        button_layout.addWidget(self.process_btn)
        layout.addLayout(button_layout)

        # Add payroll table
        self.payroll_table = QTableWidget()
        self.payroll_table.setColumnCount(9)
        self.payroll_table.setHorizontalHeaderLabels([
            "الموظف", "الراتب الأساسي", "البدلات",
            "الاستقطاعات", "صافي الراتب", "طريقة الدفع", 
            "الحالة", "تعديل", "حذف"
        ])
        self.payroll_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.payroll_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.payroll_table)

    def show_context_menu(self, pos):
        row = self.payroll_table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        
        # Get period status
        success, status = self.payroll_controller.get_period_status(self.current_period_id)
        if not success:
            return
            
        # Only show edit options if period is draft or processing
        if status in ['draft', 'processing']:
            edit_action = menu.addAction("تعديل")
            delete_action = menu.addAction("حذف")
            
        view_details = menu.addAction("عرض التفاصيل")
        print_slip = menu.addAction("طباعة قسيمة الراتب")
        
        action = menu.exec_(self.payroll_table.viewport().mapToGlobal(pos))
        if not action:
            return
            
        employee_data = self.get_row_data(row)
        
        if action == edit_action and status in ['draft', 'processing']:
            self.edit_entry(self.payroll_table.item(row, 0))
        elif action == delete_action and status in ['draft', 'processing']:
            self.delete_employee(row)
        elif action == view_details:
            self.view_employee_details(employee_data)
        elif action == print_slip:
            self.print_payslip(employee_data)

    def delete_employee(self, row):
        employee_data = self.get_row_data(row)
        employee_id = employee_data.get('id')
        
        if not employee_id:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا الموظف من كشف الرواتب؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.payroll_controller.remove_employee_from_payroll(
                self.current_period_id, employee_id
            )
            if success:
                self.load_payroll_data()
                QMessageBox.information(self, "نجاح", "تم حذف الموظف بنجاح")
            else:
                QMessageBox.warning(self, "خطأ", f"فشل حذف الموظف: {message}")

    def view_employee_details(self, employee_data):
        # TODO: Implement employee details view
        QMessageBox.information(self, "تفاصيل الموظف", 
                              f"سيتم عرض تفاصيل الموظف {employee_data.get('الموظف', '')}")

    def print_payslip(self, employee_data):
        # TODO: Implement payslip printing
        QMessageBox.information(self, "طباعة قسيمة الراتب", 
                              f"سيتم طباعة قسيمة راتب الموظف {employee_data.get('الموظف', '')}")

    def create_period(self):
        try:
            year = int(self.year_combo.currentText())
            month = self.month_combo.currentIndex() + 1
            
            # Create payroll period
            success, result = self.payroll_controller.create_payroll_period(year, month)
            if not success:
                QMessageBox.warning(self, "خطأ", f"فشل إنشاء فترة الرواتب: {result}")
                return
                
            self.current_period_id = result
            self.add_employee_btn.setEnabled(True)
            QMessageBox.information(self, "نجاح", "تم إنشاء فترة الرواتب بنجاح")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع: {str(e)}")

    def add_employees(self):
        dialog = AddEmployeeDialog(self.employee_controller, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_employees = dialog.get_selected_employees()
            if selected_employees:
                success, message = self.payroll_controller.add_employees_to_payroll(
                    self.current_period_id, selected_employees)
                if success:
                    self.load_payroll_data()
                    QMessageBox.information(self, "نجاح", "تم إضافة الموظفين بنجاح")
                else:
                    QMessageBox.warning(self, "خطأ", f"فشل إضافة الموظفين: {message}")

    def edit_entry(self, item):
        row = item.row()
        employee_data = self.get_row_data(row)
        
        dialog = EditEmployeePayrollDialog(self.payroll_controller, employee_data, self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            success, message = self.payroll_controller.update_payroll_entry(
                self.current_period_id, employee_data['id'], values)
            if success:
                self.load_payroll_data()
                QMessageBox.information(self, "نجاح", "تم تحديث البيانات بنجاح")
            else:
                QMessageBox.warning(self, "خطأ", f"فشل تحديث البيانات: {message}")

    def get_row_data(self, row):
        """Get data for a specific row in the payroll table"""
        data = {}
        # Get the employee ID from the item's data
        name_item = self.payroll_table.item(row, 0)
        if name_item:
            data['id'] = name_item.data(Qt.UserRole)  # Get stored employee ID
            
        # Get other data from visible columns
        for col in range(self.payroll_table.columnCount()):
            item = self.payroll_table.item(row, col)
            if item:
                header = self.payroll_table.horizontalHeaderItem(col).text()
                data[header] = item.text()
        return data

    def load_payroll_data(self):
        if not self.current_period_id:
            return
            
        success, entries = self.payroll_controller.get_payroll_entries(self.current_period_id)
        if not success:
            QMessageBox.warning(self, "خطأ", f"فشل تحميل بيانات الرواتب: {entries}")
            return
            
        self.payroll_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            # Create name item with employee ID stored in user role
            name_item = QTableWidgetItem(entry.get('employee_name', ''))
            name_item.setData(Qt.UserRole, entry.get('employee_id'))  # Store employee ID
            self.payroll_table.setItem(i, 0, name_item)
            
            self.payroll_table.setItem(i, 1, QTableWidgetItem(f"{float(entry.get('basic_salary', 0)):,.2f}"))
            self.payroll_table.setItem(i, 2, QTableWidgetItem(f"{float(entry.get('total_allowances', 0)):,.2f}"))
            self.payroll_table.setItem(i, 3, QTableWidgetItem(f"{float(entry.get('total_deductions', 0)):,.2f}"))
            self.payroll_table.setItem(i, 4, QTableWidgetItem(f"{float(entry.get('net_salary', 0)):,.2f}"))
            self.payroll_table.setItem(i, 5, QTableWidgetItem(entry.get('payment_method_name', '')))
            self.payroll_table.setItem(i, 6, QTableWidgetItem(entry.get('payment_status', '')))
            
            # Add edit button
            edit_btn = QPushButton("تعديل")
            edit_btn.clicked.connect(lambda checked, row=i: self.edit_entry(self.payroll_table.item(row, 0)))
            self.payroll_table.setCellWidget(i, 7, edit_btn)
            
            # Add delete button
            delete_btn = QPushButton("حذف")
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_employee(row))
            self.payroll_table.setCellWidget(i, 8, delete_btn)
        
        self.payroll_table.resizeColumnsToContents()
        
        # Update button states based on period status
        success, status = self.payroll_controller.get_period_status(self.current_period_id)
        if success:
            self.add_employee_btn.setEnabled(status in ['draft', 'processing'])
            self.approve_btn.setEnabled(status == 'processing')
            self.process_btn.setEnabled(status == 'approved')

    def approve_payroll(self):
        if not self.current_period_id:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد",
            "هل أنت متأكد من اعتماد كشف الرواتب؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Using user ID 1 as default approver
            success, message = self.payroll_controller.approve_payroll(
                self.current_period_id, 
                approved_by=1
            )
            if success:
                self.load_payroll_data()
                QMessageBox.information(self, "نجاح", "تم اعتماد كشف الرواتب بنجاح")
            else:
                QMessageBox.warning(self, "خطأ", f"فشل اعتماد كشف الرواتب: {message}")

    def process_payroll(self):
        if not self.current_period_id:
            return
            
        reply = QMessageBox.question(
            self, "تأكيد",
            "هل أنت متأكد من صرف الرواتب؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.payroll_controller.process_payroll(self.current_period_id)
            if success:
                self.load_payroll_data()
                QMessageBox.information(self, "نجاح", "تم صرف الرواتب بنجاح")
            else:
                QMessageBox.warning(self, "خطأ", f"فشل صرف الرواتب: {message}")
