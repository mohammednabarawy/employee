from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QCalendarWidget, QDialog, QCheckBox, 
                             QDoubleSpinBox, QFormLayout, QDialogButtonBox, 
                             QTextEdit, QMenu, QLineEdit, QFrame, QGroupBox,
                             QScrollArea, QTabWidget)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
import qtawesome as qta
from datetime import datetime, timedelta
import calendar
from ui.styles import Styles
from ui.payroll_dialog import EditEmployeePayrollDialog

class PayrollForm(QWidget):
    def __init__(self, payroll_controller, employee_controller, attendance_controller):
        super().__init__()
        self.payroll_controller = payroll_controller
        self.employee_controller = employee_controller
        self.attendance_controller = attendance_controller
        self.current_period_id = None
        self.checkboxes = []  # Initialize checkboxes list
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Period selection
        period_layout = QHBoxLayout()
        period_label = QLabel("فترة الرواتب:")
        self.period_combo = QComboBox()
        self.period_combo.currentIndexChanged.connect(self.period_selected)
        
        # Add period button with icon
        add_period_btn = QPushButton()
        add_period_btn.setIcon(qta.icon('fa5s.plus-circle', color='white'))
        add_period_btn.setToolTip("إضافة فترة جديدة")
        add_period_btn.clicked.connect(self.create_period)
        
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_combo)
        period_layout.addWidget(add_period_btn)
        layout.addLayout(period_layout)
        
        # Add employee button with icon
        add_employee_btn = QPushButton("إضافة موظفين")
        add_employee_btn.setIcon(qta.icon('fa5s.user-plus', color='white'))
        add_employee_btn.clicked.connect(self.add_employees)
        layout.addWidget(add_employee_btn)
        
        # Create tab widget for Payroll and Attendance
        tab_widget = QTabWidget()
        
        # Payroll tab
        payroll_tab = QWidget()
        payroll_layout = QVBoxLayout()
        
        # Payroll table
        self.payroll_table = QTableWidget()
        self.payroll_table.setColumnCount(9)
        self.payroll_table.setHorizontalHeaderLabels([
            "الموظف", "الراتب الأساسي", "أيام الحضور", "أيام الغياب",
            "البدلات", "الخصومات", "خصم الغياب", "صافي الراتب", "الحالة"
        ])
        self.payroll_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.payroll_table.customContextMenuRequested.connect(self.show_context_menu)
        self.payroll_table.itemDoubleClicked.connect(self.edit_entry)
        payroll_layout.addWidget(self.payroll_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.approve_btn = QPushButton("اعتماد كشف الرواتب")
        self.approve_btn.setIcon(qta.icon('fa5s.check-circle', color='white'))
        self.approve_btn.clicked.connect(self.approve_payroll)
        
        self.process_btn = QPushButton("صرف الرواتب")
        self.process_btn.setIcon(qta.icon('fa5s.money-bill-wave', color='white'))
        self.process_btn.clicked.connect(self.process_payroll)
        
        action_layout.addWidget(self.approve_btn)
        action_layout.addWidget(self.process_btn)
        payroll_layout.addLayout(action_layout)
        
        payroll_tab.setLayout(payroll_layout)
        tab_widget.addTab(payroll_tab, "الرواتب")
        
        # Attendance tab
        attendance_tab = QWidget()
        attendance_layout = QVBoxLayout()
        
        # Employee selection for attendance
        emp_layout = QHBoxLayout()
        emp_label = QLabel("الموظف:")
        self.emp_combo = QComboBox()
        emp_layout.addWidget(emp_label)
        emp_layout.addWidget(self.emp_combo)
        attendance_layout.addLayout(emp_layout)
        
        # Attendance group
        attendance_group = QGroupBox("الحضور والانصراف")
        attendance_inner_layout = QVBoxLayout()
        
        # Add buttons layout
        buttons_layout = QHBoxLayout()
        
        # Check All button
        self.check_all_btn = QPushButton("تحديد الكل")
        self.check_all_btn.clicked.connect(self.check_all_attendance)
        buttons_layout.addWidget(self.check_all_btn)
        
        # Uncheck All button
        self.uncheck_all_btn = QPushButton("إلغاء تحديد الكل")
        self.uncheck_all_btn.clicked.connect(self.uncheck_all_attendance)
        buttons_layout.addWidget(self.uncheck_all_btn)
        
        attendance_inner_layout.addLayout(buttons_layout)
        
        # Create scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.checkboxes_layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        attendance_inner_layout.addWidget(scroll)
        
        attendance_group.setLayout(attendance_inner_layout)
        attendance_layout.addWidget(attendance_group)
        
        # Save attendance button
        self.save_attendance_btn = QPushButton("حفظ الحضور")
        self.save_attendance_btn.clicked.connect(self.save_attendance)
        attendance_layout.addWidget(self.save_attendance_btn)
        
        attendance_tab.setLayout(attendance_layout)
        tab_widget.addTab(attendance_tab, "الحضور والانصراف")
        
        layout.addWidget(tab_widget)
        
        # Load initial data
        self.load_periods()
        self.load_employees()
        
    def load_employees(self):
        """Load all active employees into the employee combo box"""
        employees = self.employee_controller.get_all_employees()
        self.emp_combo.clear()
        
        if employees:
            for employee in employees:
                self.emp_combo.addItem(
                    f"{employee['name']} ({employee['id']})", 
                    employee['id']
                )
            self.emp_combo.currentIndexChanged.connect(self.employee_selected)
            
    def employee_selected(self):
        """Handle employee selection change"""
        employee_id = self.emp_combo.currentData()
        if employee_id:
            self.update_attendance_checkboxes()
            
    def update_attendance_checkboxes(self):
        """Update attendance checkboxes based on selected employee and period"""
        if not self.current_period_id:
            return
            
        employee_id = self.emp_combo.currentData()
        if not employee_id:
            return
            
        # Clear existing checkboxes
        while self.checkboxes_layout.count():
            child = self.checkboxes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Get period dates
        period = next((p for p in self.periods if p['id'] == self.current_period_id), None)
        if not period:
            return
            
        start_date = datetime.strptime(period['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(period['end_date'], '%Y-%m-%d')
        current_date = start_date
        
        self.checkboxes = []  # Store checkboxes for easy access
        
        # Create checkbox for each day in the period
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            checkbox = QCheckBox(date_str)
            
            # Check if employee was present on this day
            status = self.attendance_controller.get_attendance_status_for_date(
                employee_id,
                date_str
            )
            checkbox.setChecked(status == "present")
            
            self.checkboxes_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
            
            current_date += timedelta(days=1)
            
    def check_all_attendance(self):
        """Check all attendance checkboxes"""
        if hasattr(self, 'checkboxes'):
            for checkbox in self.checkboxes:
                checkbox.setChecked(True)

    def uncheck_all_attendance(self):
        """Uncheck all attendance checkboxes"""
        if hasattr(self, 'checkboxes'):
            for checkbox in self.checkboxes:
                checkbox.setChecked(False)
            
    def save_attendance(self):
        """Save attendance records for the selected employee"""
        employee_id = self.emp_combo.currentData()
        if not employee_id or not self.current_period_id:
            return
            
        try:
            # Save attendance for each day
            for checkbox in self.checkboxes:
                date_str = checkbox.text()
                status = "present" if checkbox.isChecked() else "absent"
                
                self.attendance_controller.mark_attendance_for_date(
                    employee_id,
                    date_str,
                    status
                )
            
            # Update payroll entry with new attendance data
            success, entries = self.payroll_controller.get_payroll_entries(self.current_period_id)
            if success:
                for entry in entries:
                    if entry['employee_id'] == employee_id:
                        # Get attendance data
                        attendance_data = self.attendance_controller.get_attendance_data_for_period(
                            employee_id,
                            self.current_period_id
                        )
                        
                        if attendance_data:
                            # Calculate absence deduction
                            daily_rate = entry['basic_salary'] / attendance_data['total_days'] if attendance_data['total_days'] > 0 else 0
                            absence_deduction = daily_rate * attendance_data['absent_days']
                            
                            # Update payroll entry
                            self.payroll_controller.update_payroll_entry(
                                entry_id=entry['id'],
                                adjustments={
                                    'basic_salary': entry['basic_salary'],
                                    'total_allowances': entry['total_allowances'],
                                    'total_deductions': entry['total_deductions'],
                                    'absence_deduction': absence_deduction
                                },
                                reason="تحديث الحضور والغياب",
                                updated_by=1  # TODO: Get actual user ID
                            )
            
            QMessageBox.information(self, "نجاح", "تم حفظ بيانات الحضور بنجاح")
            self.load_payroll_data()
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    def load_periods(self):
        """Load all payroll periods into the combo box"""
        self.period_combo.clear()
        self.period_combo.addItem("اختر فترة الرواتب...", None)
        
        success, periods = self.payroll_controller.get_payroll_periods()
        if success:
            self.periods = periods
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
            self.approve_btn.setEnabled(False)
            self.process_btn.setEnabled(False)
            return
            
        self.current_period_id = self.period_combo.itemData(index)
        self.load_payroll_data()
        
        # Update button states based on period status
        success, status = self.payroll_controller.get_period_status(self.current_period_id)
        if success:
            self.approve_btn.setEnabled(status == 'draft')
            self.process_btn.setEnabled(status == 'approved')
            
    def load_payroll_data(self):
        """Load payroll data for the current period"""
        if not self.current_period_id:
            return
            
        success, entries = self.payroll_controller.get_payroll_entries(self.current_period_id)
        if not success:
            return
            
        self.payroll_table.setRowCount(len(entries))
        for i, entry in enumerate(entries):
            # Get attendance data
            attendance_data = self.attendance_controller.get_attendance_data_for_period(
                entry['employee_id'],
                self.current_period_id
            )
            
            present_days = attendance_data.get('present_days', 0) if attendance_data else 0
            absent_days = attendance_data.get('absent_days', 0) if attendance_data else 0
            
            # Employee name with ID as UserRole
            name_item = QTableWidgetItem(entry['employee_name'])
            name_item.setData(Qt.UserRole, entry['id'])
            self.payroll_table.setItem(i, 0, name_item)
            
            # Basic salary
            self.payroll_table.setItem(i, 1, QTableWidgetItem(f"{float(entry['basic_salary']):,.2f}"))
            
            # Attendance
            self.payroll_table.setItem(i, 2, QTableWidgetItem(str(present_days)))
            self.payroll_table.setItem(i, 3, QTableWidgetItem(str(absent_days)))
            
            # Financial details
            self.payroll_table.setItem(i, 4, QTableWidgetItem(f"{float(entry['total_allowances']):,.2f}"))
            self.payroll_table.setItem(i, 5, QTableWidgetItem(f"{float(entry['total_deductions']):,.2f}"))
            self.payroll_table.setItem(i, 6, QTableWidgetItem(f"{float(entry.get('absence_deduction', 0)):,.2f}"))
            self.payroll_table.setItem(i, 7, QTableWidgetItem(f"{float(entry['net_salary']):,.2f}"))
            self.payroll_table.setItem(i, 8, QTableWidgetItem(entry['payment_status']))
        
        self.payroll_table.resizeColumnsToContents()
        
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
        """Edit a payroll entry"""
        row = item.row()
        employee_data = {
            'employee_id': self.payroll_table.item(row, 0).data(Qt.UserRole),
            'employee_name': self.payroll_table.item(row, 0).text(),
            'basic_salary': float(self.payroll_table.item(row, 1).text().replace(',', '')),
            'total_allowances': float(self.payroll_table.item(row, 4).text().replace(',', '')),
            'total_deductions': float(self.payroll_table.item(row, 5).text().replace(',', '')),
            'absence_deduction': float(self.payroll_table.item(row, 6).text().replace(',', '')),
            'net_salary': float(self.payroll_table.item(row, 7).text().replace(',', ''))
        }
        
        dialog = EditEmployeePayrollDialog(self.payroll_controller, employee_data, self)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            # Get the current user ID (you should implement this)
            updated_by = 1  # TODO: Get actual user ID
            
            success, message = self.payroll_controller.update_payroll_entry(
                entry_id=employee_data['employee_id'],
                adjustments=values,
                reason="تحديث بيانات الراتب",
                updated_by=updated_by
            )
            
            if success:
                self.load_payroll_data()
            else:
                QMessageBox.warning(self, "خطأ", message)

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
