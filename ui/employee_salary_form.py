from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QSpinBox, QDoubleSpinBox,
                             QFormLayout, QDialogButtonBox, QLineEdit, QCheckBox,
                             QDateEdit)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
import qtawesome as qta
from ui.styles import Styles
from datetime import date

class AddEmployeeComponentDialog(QDialog):
    def __init__(self, payroll_controller, employee_id, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.employee_id = employee_id
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("إضافة عنصر راتب للموظف")
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        # Component selection
        self.component_combo = QComboBox()
        success, components = self.payroll_controller.get_salary_components()
        if success:
            for comp in components:
                self.component_combo.addItem(
                    comp['name_ar'],
                    userData=comp
                )
        layout.addRow("العنصر:", self.component_combo)
        
        # Value
        self.value = QDoubleSpinBox()
        self.value.setMaximum(1000000)
        self.value.setMinimum(0)
        self.value.setDecimals(2)
        self.value.setPrefix("ر.س ")
        layout.addRow("القيمة:", self.value)
        
        # Start date
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.start_date.setCalendarPopup(True)
        layout.addRow("تاريخ البدء:", self.start_date)
        
        # End date (optional)
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate().addYears(1))
        self.end_date.setCalendarPopup(True)
        self.end_date_enabled = QCheckBox("تحديد تاريخ انتهاء")
        self.end_date_enabled.stateChanged.connect(
            lambda state: self.end_date.setEnabled(state == Qt.Checked)
        )
        self.end_date.setEnabled(False)
        
        end_date_layout = QHBoxLayout()
        end_date_layout.addWidget(self.end_date)
        end_date_layout.addWidget(self.end_date_enabled)
        layout.addRow("تاريخ الانتهاء:", end_date_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
        # Connect component selection to value update
        self.component_combo.currentIndexChanged.connect(self.update_value_settings)
        self.update_value_settings()
        
    def update_value_settings(self):
        component = self.component_combo.currentData()
        if component:
            if component['is_percentage']:
                self.value.setMaximum(100)
                self.value.setPrefix("")
                self.value.setSuffix("%")
                self.value.setValue(component['percentage'] or 0)
            else:
                self.value.setMaximum(1000000)
                self.value.setPrefix("ر.س ")
                self.value.setSuffix("")
                self.value.setValue(component['value'] or 0)
                
    def get_data(self):
        component = self.component_combo.currentData()
        return {
            'employee_id': self.employee_id,
            'component_id': component['id'],
            'value': self.value.value(),
            'start_date': self.start_date.date().toPyDate(),
            'end_date': self.end_date.date().toPyDate() if self.end_date_enabled.isChecked() else None
        }

class EmployeeSalaryForm(QWidget):
    def __init__(self, payroll_controller, employee_id, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.employee_id = employee_id
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(Styles.LIGHT_THEME)
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Basic salary section
        basic_salary_layout = QHBoxLayout()
        basic_salary_layout.addWidget(QLabel("الراتب الأساسي:"))
        
        self.basic_salary = QDoubleSpinBox()
        self.basic_salary.setMaximum(1000000)
        self.basic_salary.setMinimum(0)
        self.basic_salary.setDecimals(2)
        self.basic_salary.setPrefix("ر.س ")
        self.basic_salary.valueChanged.connect(self.update_basic_salary)
        basic_salary_layout.addWidget(self.basic_salary)
        
        layout.addLayout(basic_salary_layout)
        
        # Add toolbar
        toolbar = QHBoxLayout()
        
        # Add component button
        add_btn = QPushButton()
        add_btn.setIcon(qta.icon('fa5s.plus', color='white'))
        add_btn.setText("إضافة عنصر جديد")
        add_btn.clicked.connect(self.add_component)
        toolbar.addWidget(add_btn)
        
        # Filter by type
        self.type_filter = QComboBox()
        self.type_filter.addItems(["الكل", "البدلات", "الخصومات"])
        self.type_filter.currentIndexChanged.connect(self.load_components)
        toolbar.addWidget(QLabel("تصفية:"))
        toolbar.addWidget(self.type_filter)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Components table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "العنصر", "النوع", "القيمة", "تاريخ البدء",
            "تاريخ الانتهاء", "الحالة", ""
        ])
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Summary section
        summary_layout = QFormLayout()
        self.total_allowances = QLabel("0.00 ر.س")
        self.total_deductions = QLabel("0.00 ر.س")
        self.net_salary = QLabel("0.00 ر.س")
        
        summary_layout.addRow("إجمالي البدلات:", self.total_allowances)
        summary_layout.addRow("إجمالي الخصومات:", self.total_deductions)
        summary_layout.addRow("صافي الراتب:", self.net_salary)
        
        layout.addLayout(summary_layout)
        
        # Load initial data
        self.load_employee_salary()
        self.load_components()
        
    def load_employee_salary(self):
        success, salary_info = self.payroll_controller.get_employee_salary(self.employee_id)
        if success:
            self.basic_salary.setValue(salary_info['basic_salary'])
            
    def update_basic_salary(self):
        success, message = self.payroll_controller.update_employee_basic_salary(
            self.employee_id,
            self.basic_salary.value()
        )
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحديث الراتب الأساسي: {message}")
        self.update_summary()
        
    def load_components(self):
        filter_type = self.type_filter.currentText()
        component_type = None
        if filter_type == "البدلات":
            component_type = "allowance"
        elif filter_type == "الخصومات":
            component_type = "deduction"
            
        success, components = self.payroll_controller.get_employee_components(
            self.employee_id,
            component_type
        )
        
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل عناصر الراتب: {components}")
            return
            
        self.table.setRowCount(len(components))
        for i, comp in enumerate(components):
            # Component name
            self.table.setItem(i, 0, QTableWidgetItem(comp['name_ar']))
            
            # Type
            type_text = "بدل" if comp['type'] == 'allowance' else "خصم"
            type_item = QTableWidgetItem(type_text)
            type_item.setIcon(
                qta.icon('fa5s.plus-circle', color='#27ae60')
                if comp['type'] == 'allowance'
                else qta.icon('fa5s.minus-circle', color='#c0392b')
            )
            self.table.setItem(i, 1, type_item)
            
            # Value
            if comp['is_percentage']:
                value = comp['percentage']
                value_text = f"{value}% ({value/100 * self.basic_salary.value():,.2f} ر.س)"
            else:
                value_text = f"{comp['value']:,.2f} ر.س"
            self.table.setItem(i, 2, QTableWidgetItem(value_text))
            
            # Start date
            start_date = QTableWidgetItem(comp['start_date'].strftime('%Y/%m/%d'))
            self.table.setItem(i, 3, start_date)
            
            # End date
            end_date = comp.get('end_date')
            end_date_text = end_date.strftime('%Y/%m/%d') if end_date else "-"
            self.table.setItem(i, 4, QTableWidgetItem(end_date_text))
            
            # Status
            today = date.today()
            status_text = "نشط"
            status_icon = 'fa5s.check-circle'
            status_color = '#27ae60'
            
            if end_date and end_date < today:
                status_text = "منتهي"
                status_icon = 'fa5s.times-circle'
                status_color = '#c0392b'
            elif not comp['is_active']:
                status_text = "موقوف"
                status_icon = 'fa5s.pause-circle'
                status_color = '#f39c12'
                
            status_item = QTableWidgetItem(status_text)
            status_item.setIcon(qta.icon(status_icon, color=status_color))
            self.table.setItem(i, 5, status_item)
            
            # Actions
            actions_layout = QHBoxLayout()
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            
            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon('fa5s.edit', color='white'))
            edit_btn.clicked.connect(lambda checked, row=i: self.edit_component(row))
            
            delete_btn = QPushButton()
            delete_btn.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            delete_btn.setProperty('class', 'danger')
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_component(row))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            self.table.setCellWidget(i, 6, actions_widget)
            
        self.table.resizeColumnsToContents()
        self.update_summary()
        
    def update_summary(self):
        success, summary = self.payroll_controller.get_employee_salary_summary(
            self.employee_id
        )
        if success:
            self.total_allowances.setText(f"{summary['total_allowances']:,.2f} ر.س")
            self.total_deductions.setText(f"{summary['total_deductions']:,.2f} ر.س")
            self.net_salary.setText(f"{summary['net_salary']:,.2f} ر.س")
        
    def add_component(self):
        dialog = AddEmployeeComponentDialog(
            self.payroll_controller,
            self.employee_id,
            self
        )
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            success, message = self.payroll_controller.add_employee_component(data)
            
            if success:
                self.load_components()
            else:
                QMessageBox.warning(
                    self, "خطأ",
                    f"حدث خطأ أثناء إضافة عنصر الراتب: {message}"
                )
                
    def edit_component(self, row):
        component_id = self.table.item(row, 0).data(Qt.UserRole)
        dialog = AddEmployeeComponentDialog(
            self.payroll_controller,
            self.employee_id,
            self
        )
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            success, message = self.payroll_controller.update_employee_component(
                component_id,
                data
            )
            
            if success:
                self.load_components()
            else:
                QMessageBox.warning(
                    self, "خطأ",
                    f"حدث خطأ أثناء تحديث عنصر الراتب: {message}"
                )
                
    def delete_component(self, row):
        component_id = self.table.item(row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا العنصر؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.payroll_controller.delete_employee_component(
                component_id
            )
            
            if success:
                self.load_components()
            else:
                QMessageBox.warning(
                    self, "خطأ",
                    f"حدث خطأ أثناء حذف عنصر الراتب: {message}"
                )
