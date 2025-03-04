from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QCalendarWidget, QDialog, QCheckBox, 
                             QDoubleSpinBox, QFormLayout, QDialogButtonBox, 
                             QTextEdit, QMenu, QLineEdit, QFrame, QGroupBox)
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
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Period selection
        period_layout = QHBoxLayout()
        period_label = QLabel("فترة الرواتب:")
        self.period_combo = QComboBox()
        self.period_combo.setMinimumWidth(200)
        self.period_combo.currentIndexChanged.connect(self.period_selected)  # Add this line
        
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_combo)
        
        # Create period button
        create_period_btn = QPushButton("إنشاء فترة جديدة")
        create_period_btn.setIcon(qta.icon('fa5s.plus-circle', color='white'))
        create_period_btn.clicked.connect(self.create_period)
        
        # Add employees button
        add_employees_btn = QPushButton("إضافة موظفين")
        add_employees_btn.setIcon(qta.icon('fa5s.user-plus', color='white'))
        add_employees_btn.clicked.connect(self.add_employees)
        
        # Salary comparison button
        compare_btn = QPushButton("مقارنة الرواتب")
        compare_btn.setIcon(qta.icon('fa5s.chart-bar', color='white'))
        compare_btn.clicked.connect(self.show_salary_comparison)
        
        # Add to toolbar
        toolbar.addLayout(period_layout)
        toolbar.addWidget(create_period_btn)
        toolbar.addWidget(add_employees_btn)
        toolbar.addWidget(compare_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.add_employee_btn = QPushButton("إضافة موظفين")
        self.add_employee_btn.clicked.connect(self.add_employees)
        self.add_employee_btn.setEnabled(False)
        
        self.approve_btn = QPushButton("اعتماد كشف الرواتب")
        self.approve_btn.clicked.connect(self.approve_payroll)
        self.approve_btn.setEnabled(False)
        
        self.process_btn = QPushButton("صرف الرواتب")
        self.process_btn.clicked.connect(self.process_payroll)
        self.process_btn.setEnabled(False)
        
        self.print_all_btn = QPushButton("طباعة جميع قسائم الرواتب")
        self.print_all_btn.clicked.connect(self.print_all_payslips)
        self.print_all_btn.setEnabled(False)
        
        button_layout.addWidget(self.add_employee_btn)
        button_layout.addWidget(self.approve_btn)
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.print_all_btn)
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
        
        # Load existing periods
        self.load_periods()
        
    def load_periods(self):
        """Load all payroll periods into the combo box"""
        self.period_combo.clear()
        self.period_combo.addItem("اختر فترة الرواتب...", None)
        
        success, periods = self.payroll_controller.get_payroll_periods()
        if success:
            for period in periods:
                # Get Arabic month name
                month_names = [
                    "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
                    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
                ]
                month_name = month_names[period['month'] - 1]
                
                # Create display text
                display_text = f"{month_name} {period['year']} - {period['status']}"
                self.period_combo.addItem(display_text, period['id'])
    
    def period_selected(self, index):
        """Handle period selection"""
        if index < 0:
            self.current_period_id = None
            self.add_employee_btn.setEnabled(False)
            self.approve_btn.setEnabled(False)
            self.process_btn.setEnabled(False)
            self.print_all_btn.setEnabled(False)
            return
            
        self.current_period_id = self.period_combo.itemData(index)
        self.load_payroll_data()
        
        # Update button states based on period status
        success, status = self.payroll_controller.get_period_status(self.current_period_id)
        if success:
            self.add_employee_btn.setEnabled(status in ['draft', 'processing'])
            self.approve_btn.setEnabled(status == 'draft')
            self.process_btn.setEnabled(status == 'approved')
            # Enable print button for any status as long as there are entries
            success, entries = self.payroll_controller.get_payroll_entries(self.current_period_id)
            self.print_all_btn.setEnabled(success and len(entries) > 0)

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
            edit_action = menu.addAction(qta.icon('fa5s.edit', color='#f39c12'), "تعديل")
            delete_action = menu.addAction(qta.icon('fa5s.trash-alt', color='#e74c3c'), "حذف")
            
        view_action = menu.addAction(qta.icon('fa5s.eye', color='#3498db'), "عرض التفاصيل")
        history_action = menu.addAction(qta.icon('fa5s.history', color='#2ecc71'), "سجل الرواتب")
        print_action = menu.addAction(qta.icon('fa5s.print', color='#9b59b6'), "طباعة قسيمة الراتب")
        
        action = menu.exec_(self.payroll_table.viewport().mapToGlobal(pos))
        if not action:
            return
            
        employee_data = self.get_row_data(row)
        
        if action == edit_action and status in ['draft', 'processing']:
            self.edit_entry(self.payroll_table.item(row, 0))
        elif action == delete_action and status in ['draft', 'processing']:
            self.delete_employee(row)
        elif action == view_action:
            self.view_employee_details(employee_data)
        elif action == history_action:
            self.view_salary_history(employee_data)
        elif action == print_action:
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
        """Print payslip for a single employee"""
        if not self.current_period_id or not employee_data.get('id'):
            return
            
        # Get entry ID
        entry_id = None
        success, entries = self.payroll_controller.get_payroll_entries(self.current_period_id)
        if success:
            for entry in entries:
                if entry.get('employee_id') == employee_data.get('id'):
                    entry_id = entry.get('id')
                    break
        
        if not entry_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على بيانات الراتب لهذا الموظف")
            return
            
        # Get detailed payslip data
        success, payslip_data = self.payroll_controller.get_employee_payslip(entry_id)
        if not success:
            QMessageBox.warning(self, "خطأ", f"فشل استرجاع بيانات قسيمة الراتب: {payslip_data}")
            return
        
        # Add database file to payslip data for company info
        payslip_data['db_file'] = self.payroll_controller.db.db_file
            
        # Print the payslip
        try:
            from .payslip_template import PayslipPrinter
            PayslipPrinter.print_multiple_payslips(self, [payslip_data])
        except ImportError:
            # Try alternative import path
            try:
                from ui.payslip_template import PayslipPrinter
                PayslipPrinter.print_multiple_payslips(self, [payslip_data])
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"فشل طباعة قسيمة الراتب: {str(e)}")

    def print_all_payslips(self):
        """Print payslips for all employees in the current period"""
        if not self.current_period_id:
            return
            
        # Get all entries for the current period
        success, entries = self.payroll_controller.get_payroll_entries(self.current_period_id)
        if not success or not entries:
            QMessageBox.warning(self, "خطأ", "لا توجد بيانات رواتب للطباعة")
            return
            
        # Get detailed payslip data for each entry
        payslips_data = []
        for entry in entries:
            entry_id = entry.get('id')
            if entry_id:
                success, payslip_data = self.payroll_controller.get_employee_payslip(entry_id)
                if success:
                    # Add database file to payslip data for company info
                    payslip_data['db_file'] = self.payroll_controller.db.db_file
                    payslips_data.append(payslip_data)
        
        if not payslips_data:
            QMessageBox.warning(self, "خطأ", "فشل استرجاع بيانات قسائم الرواتب")
            return
            
        # Print all payslips
        try:
            from .payslip_template import PayslipPrinter
            PayslipPrinter.print_multiple_payslips(self, payslips_data)
        except ImportError:
            # Try alternative import path
            try:
                from ui.payslip_template import PayslipPrinter
                PayslipPrinter.print_multiple_payslips(self, payslips_data)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"فشل طباعة قسائم الرواتب: {str(e)}")

    def view_salary_history(self, employee_data):
        """Show salary history for an employee"""
        from ui.salary_history_dialog import SalaryHistoryDialog
        dialog = SalaryHistoryDialog(self.payroll_controller, employee_data, self)
        dialog.exec_()

    def show_salary_comparison(self):
        """Show salary comparison dialog"""
        from ui.salary_comparison_dialog import SalaryComparisonDialog
        dialog = SalaryComparisonDialog(self.payroll_controller, self.employee_controller, self)
        dialog.exec_()

    def create_period(self):
        """Create a new payroll period"""
        current_date = QDate.currentDate()
        year = current_date.year()
        month = current_date.month()
        
        # Create dialog to select year and month
        dialog = QDialog(self)
        dialog.setWindowTitle("إنشاء فترة رواتب جديدة")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        form_layout = QFormLayout()
        
        # Year selection
        year_combo = QComboBox()
        years = [year - 1, year, year + 1]
        for y in years:
            year_combo.addItem(str(y), y)
        year_combo.setCurrentText(str(year))
        form_layout.addRow("السنة:", year_combo)
        
        # Month selection
        month_combo = QComboBox()
        months = [
            ("يناير", 1), ("فبراير", 2), ("مارس", 3), ("أبريل", 4),
            ("مايو", 5), ("يونيو", 6), ("يوليو", 7), ("أغسطس", 8),
            ("سبتمبر", 9), ("أكتوبر", 10), ("نوفمبر", 11), ("ديسمبر", 12)
        ]
        for month_name, month_num in months:
            month_combo.addItem(month_name, month_num)
        month_combo.setCurrentIndex(month - 1)
        form_layout.addRow("الشهر:", month_combo)
        
        layout.addLayout(form_layout)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_():
            selected_year = year_combo.currentData()
            selected_month = month_combo.currentData()
            
            # Create the period
            success, result = self.payroll_controller.create_payroll_period(selected_year, selected_month)
            
            if success:
                self.current_period_id = result
                self.load_periods()
                QMessageBox.information(self, "نجاح", "تم إنشاء فترة الرواتب بنجاح")
                
                # Find the index of the new period in the combo box
                for i in range(self.period_combo.count()):
                    if self.period_combo.itemData(i) == self.current_period_id:
                        self.period_combo.setCurrentIndex(i)
                        break
                
                self.load_payroll_data()
            else:
                QMessageBox.warning(self, "خطأ", f"فشل إنشاء فترة الرواتب: {result}")

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
            self.approve_btn.setEnabled(status == 'draft')
            self.process_btn.setEnabled(status == 'approved')
            # Enable print button if there are entries
            self.print_all_btn.setEnabled(len(entries) > 0)

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
            # Using user ID 1 as default processor
            success, message = self.payroll_controller.process_payroll(
                self.current_period_id,
                processed_by=1
            )
            if success:
                self.load_payroll_data()
                QMessageBox.information(self, "نجاح", "تم صرف الرواتب بنجاح")
            else:
                QMessageBox.warning(self, "خطأ", f"فشل صرف الرواتب: {message}")
