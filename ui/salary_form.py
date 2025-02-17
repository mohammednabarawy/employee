from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox,
                           QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from utils.validation import ValidationUtils

class SalaryForm(QWidget):
    salary_saved = pyqtSignal(dict)

    def __init__(self, salary_controller, employee_controller, parent=None):
        super().__init__(parent)
        self.salary_controller = salary_controller
        self.employee_controller = employee_controller
        self.current_employee_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Employee Selection
        employee_layout = QHBoxLayout()
        self.employee_combo = QComboBox()
        self.refresh_employee_list()
        self.employee_combo.currentIndexChanged.connect(self.employee_selected)
        
        employee_layout.addWidget(QLabel("Select Employee:"))
        employee_layout.addWidget(self.employee_combo)
        
        # Salary Information Form
        form_layout = QFormLayout()
        
        self.base_salary_spin = QDoubleSpinBox()
        self.base_salary_spin.setRange(0, 1000000)
        self.base_salary_spin.setDecimals(2)
        self.base_salary_spin.setSingleStep(100)
        self.base_salary_spin.valueChanged.connect(self.calculate_total)
        
        self.bonuses_spin = QDoubleSpinBox()
        self.bonuses_spin.setRange(0, 100000)
        self.bonuses_spin.setDecimals(2)
        self.bonuses_spin.setSingleStep(50)
        self.bonuses_spin.valueChanged.connect(self.calculate_total)
        
        self.deductions_spin = QDoubleSpinBox()
        self.deductions_spin.setRange(0, 100000)
        self.deductions_spin.setDecimals(2)
        self.deductions_spin.setSingleStep(50)
        self.deductions_spin.valueChanged.connect(self.calculate_total)
        
        self.overtime_pay_spin = QDoubleSpinBox()
        self.overtime_pay_spin.setRange(0, 100000)
        self.overtime_pay_spin.setDecimals(2)
        self.overtime_pay_spin.setSingleStep(50)
        self.overtime_pay_spin.valueChanged.connect(self.calculate_total)
        
        self.total_salary_label = QLabel("$0.00")
        self.total_salary_label.setStyleSheet("font-weight: bold; color: green;")
        
        form_layout.addRow("Base Salary:", self.base_salary_spin)
        form_layout.addRow("Bonuses:", self.bonuses_spin)
        form_layout.addRow("Deductions:", self.deductions_spin)
        form_layout.addRow("Overtime Pay:", self.overtime_pay_spin)
        form_layout.addRow("Total Salary:", self.total_salary_label)
        
        # Payment Section
        payment_layout = QFormLayout()
        
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate())
        
        self.payment_mode_combo = QComboBox()
        self.payment_mode_combo.addItems(['Bank Transfer', 'Cash', 'Cheque'])
        
        self.payment_amount_spin = QDoubleSpinBox()
        self.payment_amount_spin.setRange(0, 1000000)
        self.payment_amount_spin.setDecimals(2)
        self.payment_amount_spin.setSingleStep(100)
        
        payment_layout.addRow("Payment Date:", self.payment_date_edit)
        payment_layout.addRow("Payment Mode:", self.payment_mode_combo)
        payment_layout.addRow("Amount to Pay:", self.payment_amount_spin)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_salary_btn = QPushButton("Save Salary Structure")
        self.save_salary_btn.clicked.connect(self.save_salary)
        
        self.process_payment_btn = QPushButton("Process Payment")
        self.process_payment_btn.clicked.connect(self.process_payment)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.save_salary_btn)
        button_layout.addWidget(self.process_payment_btn)
        button_layout.addWidget(self.clear_btn)
        
        # Add all layouts to main layout
        layout.addLayout(employee_layout)
        layout.addLayout(form_layout)
        layout.addLayout(payment_layout)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def refresh_employee_list(self):
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.employee_combo.clear()
            self.employee_combo.addItem("Select Employee", None)
            for employee in employees:
                self.employee_combo.addItem(
                    f"{employee['name']} ({employee['department']})",
                    employee['id']
                )

    def employee_selected(self):
        employee_id = self.employee_combo.currentData()
        if employee_id:
            self.current_employee_id = employee_id
            success, salary_info = self.salary_controller.get_salary_info(employee_id)
            if success:
                self.base_salary_spin.setValue(salary_info['base_salary'])
                self.bonuses_spin.setValue(salary_info['bonuses'])
                self.deductions_spin.setValue(salary_info['deductions'])
                self.overtime_pay_spin.setValue(salary_info['overtime_pay'])
                self.payment_amount_spin.setValue(salary_info['total_salary'])
            else:
                success, employee = self.employee_controller.get_employee(employee_id)
                if success:
                    self.base_salary_spin.setValue(float(employee['basic_salary']))
                    self.bonuses_spin.setValue(0)
                    self.deductions_spin.setValue(0)
                    self.overtime_pay_spin.setValue(0)
                    self.payment_amount_spin.setValue(float(employee['basic_salary']))

    def calculate_total(self):
        total = (
            self.base_salary_spin.value() +
            self.bonuses_spin.value() +
            self.overtime_pay_spin.value() -
            self.deductions_spin.value()
        )
        self.total_salary_label.setText(f"${total:.2f}")
        self.payment_amount_spin.setValue(total)

    def get_salary_data(self):
        return {
            'base_salary': self.base_salary_spin.value(),
            'bonuses': self.bonuses_spin.value(),
            'deductions': self.deductions_spin.value(),
            'overtime_pay': self.overtime_pay_spin.value()
        }

    def get_payment_data(self):
        return {
            'employee_id': self.current_employee_id,
            'amount_paid': self.payment_amount_spin.value(),
            'payment_date': self.payment_date_edit.date().toString('yyyy-MM-dd'),
            'payment_mode': self.payment_mode_combo.currentText()
        }

    def save_salary(self):
        if not self.current_employee_id:
            QMessageBox.warning(self, "Error", "Please select an employee first")
            return
        
        data = self.get_salary_data()
        valid, msg = ValidationUtils.validate_salary_data(data)
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return
        
        success, error = self.salary_controller.update_salary(self.current_employee_id, data)
        if success:
            self.salary_saved.emit(data)
            QMessageBox.information(self, "Success", "Salary structure saved successfully!")
        else:
            QMessageBox.warning(self, "Error", f"Failed to save salary structure: {error}")

    def process_payment(self):
        if not self.current_employee_id:
            QMessageBox.warning(self, "Error", "Please select an employee first")
            return
        
        data = self.get_payment_data()
        valid, msg = ValidationUtils.validate_payment_data(data)
        if not valid:
            QMessageBox.warning(self, "Validation Error", msg)
            return
        
        success, error = self.salary_controller.process_payment(data)
        if success:
            QMessageBox.information(self, "Success", "Payment processed successfully!")
            self.clear_form()
        else:
            QMessageBox.warning(self, "Error", f"Failed to process payment: {error}")

    def clear_form(self):
        self.employee_combo.setCurrentIndex(0)
        self.current_employee_id = None
        self.base_salary_spin.setValue(0)
        self.bonuses_spin.setValue(0)
        self.deductions_spin.setValue(0)
        self.overtime_pay_spin.setValue(0)
        self.payment_date_edit.setDate(QDate.currentDate())
        self.payment_mode_combo.setCurrentIndex(0)
        self.payment_amount_spin.setValue(0)
