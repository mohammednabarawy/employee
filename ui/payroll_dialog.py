from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QDoubleSpinBox, QFormLayout, QDialogButtonBox,
                             QMessageBox)
from PyQt5.QtCore import Qt
import qtawesome as qta

class EditEmployeePayrollDialog(QDialog):
    def __init__(self, payroll_controller, employee_data, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.employee_data = employee_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("تعديل راتب الموظف")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Employee name (read-only)
        name_label = QLabel(self.employee_data.get('employee_name', ''))
        form_layout.addRow("الموظف:", name_label)
        
        # Basic salary
        self.basic_salary_spin = QDoubleSpinBox()
        self.basic_salary_spin.setRange(0, 1000000)
        self.basic_salary_spin.setDecimals(2)
        self.basic_salary_spin.setValue(float(self.employee_data.get('basic_salary', 0)))
        form_layout.addRow("الراتب الأساسي:", self.basic_salary_spin)
        
        # Allowances
        self.allowances_spin = QDoubleSpinBox()
        self.allowances_spin.setRange(0, 1000000)
        self.allowances_spin.setDecimals(2)
        self.allowances_spin.setValue(float(self.employee_data.get('total_allowances', 0)))
        form_layout.addRow("البدلات:", self.allowances_spin)
        
        # Deductions
        self.deductions_spin = QDoubleSpinBox()
        self.deductions_spin.setRange(0, 1000000)
        self.deductions_spin.setDecimals(2)
        self.deductions_spin.setValue(float(self.employee_data.get('total_deductions', 0)))
        form_layout.addRow("الخصومات:", self.deductions_spin)
        
        # Absence deduction
        self.absence_deduction_spin = QDoubleSpinBox()
        self.absence_deduction_spin.setRange(0, 1000000)
        self.absence_deduction_spin.setDecimals(2)
        self.absence_deduction_spin.setValue(float(self.employee_data.get('absence_deduction', 0)))
        form_layout.addRow("خصم الغياب:", self.absence_deduction_spin)
        
        # Net salary (calculated automatically)
        self.net_salary_label = QLabel()
        self.update_net_salary()
        form_layout.addRow("صافي الراتب:", self.net_salary_label)
        
        # Connect signals for automatic net salary calculation
        self.basic_salary_spin.valueChanged.connect(self.update_net_salary)
        self.allowances_spin.valueChanged.connect(self.update_net_salary)
        self.deductions_spin.valueChanged.connect(self.update_net_salary)
        self.absence_deduction_spin.valueChanged.connect(self.update_net_salary)
        
        layout.addLayout(form_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def update_net_salary(self):
        """Update net salary based on current values"""
        basic = self.basic_salary_spin.value()
        allowances = self.allowances_spin.value()
        deductions = self.deductions_spin.value()
        absence = self.absence_deduction_spin.value()
        
        net_salary = basic + allowances - deductions - absence
        self.net_salary_label.setText(f"{net_salary:,.2f}")
        
    def get_values(self):
        """Get the current values from the dialog"""
        return {
            'basic_salary': self.basic_salary_spin.value(),
            'total_allowances': self.allowances_spin.value(),
            'total_deductions': self.deductions_spin.value(),
            'absence_deduction': self.absence_deduction_spin.value(),
            'net_salary': float(self.net_salary_label.text().replace(',', ''))
        }
