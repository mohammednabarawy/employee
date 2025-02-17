from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QFormLayout,
                             QDoubleSpinBox, QMessageBox, QDateEdit)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime

class SalaryForm(QWidget):
    def __init__(self, salary_controller, parent=None):
        super().__init__(parent)
        self.salary_controller = salary_controller
        self.current_salary_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("إدارة الرواتب")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Employee ID/Name
        self.employee_id_edit = QLineEdit()
        form_layout.addRow("رقم الموظف:", self.employee_id_edit)
        
        # Basic Salary
        self.basic_salary_spin = QDoubleSpinBox()
        self.basic_salary_spin.setRange(0, 1000000)
        self.basic_salary_spin.setDecimals(2)
        self.basic_salary_spin.setSingleStep(100)
        form_layout.addRow("الراتب الأساسي:", self.basic_salary_spin)
        
        # Allowances
        self.housing_allowance_spin = QDoubleSpinBox()
        self.housing_allowance_spin.setRange(0, 100000)
        self.housing_allowance_spin.setDecimals(2)
        form_layout.addRow("بدل السكن:", self.housing_allowance_spin)
        
        self.transport_allowance_spin = QDoubleSpinBox()
        self.transport_allowance_spin.setRange(0, 50000)
        self.transport_allowance_spin.setDecimals(2)
        form_layout.addRow("بدل النقل:", self.transport_allowance_spin)
        
        # Deductions
        self.loan_deduction_spin = QDoubleSpinBox()
        self.loan_deduction_spin.setRange(0, 100000)
        self.loan_deduction_spin.setDecimals(2)
        form_layout.addRow("خصم القرض:", self.loan_deduction_spin)
        
        self.absence_deduction_spin = QDoubleSpinBox()
        self.absence_deduction_spin.setRange(0, 100000)
        self.absence_deduction_spin.setDecimals(2)
        form_layout.addRow("خصم الغياب:", self.absence_deduction_spin)
        
        # Payment Details
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([
            "تحويل بنكي",
            "نقدي",
            "شيك"
        ])
        form_layout.addRow("طريقة الدفع:", self.payment_method_combo)
        
        # Payment Date
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate())
        form_layout.addRow("تاريخ الدفع:", self.payment_date_edit)
        
        # Payment Status
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItems([
            "تم الدفع",
            "معلق",
            "ملغي"
        ])
        form_layout.addRow("حالة الدفع:", self.payment_status_combo)
        
        # Add form layout to main layout
        layout.addLayout(form_layout)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        self.calculate_btn = QPushButton("حساب الراتب")
        self.calculate_btn.clicked.connect(self.calculate_salary)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_salary)
        
        self.clear_btn = QPushButton("مسح")
        self.clear_btn.clicked.connect(self.clear_form)
        
        buttons_layout.addWidget(self.calculate_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.clear_btn)
        
        layout.addLayout(buttons_layout)
        
        # Total amount label
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        self.total_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.total_label)
        
        # Add stretch to push everything to the top
        layout.addStretch()

    def calculate_salary(self):
        """Calculate the total salary including allowances and deductions."""
        basic = self.basic_salary_spin.value()
        housing = self.housing_allowance_spin.value()
        transport = self.transport_allowance_spin.value()
        loan = self.loan_deduction_spin.value()
        absence = self.absence_deduction_spin.value()
        
        total = basic + housing + transport - loan - absence
        
        self.total_label.setText(f"إجمالي الراتب: {total:,.2f} ريال")

    def save_salary(self):
        """Save the salary record."""
        if not self.employee_id_edit.text():
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال رقم الموظف")
            return
        
        data = {
            'employee_id': self.employee_id_edit.text(),
            'basic_salary': self.basic_salary_spin.value(),
            'housing_allowance': self.housing_allowance_spin.value(),
            'transport_allowance': self.transport_allowance_spin.value(),
            'loan_deduction': self.loan_deduction_spin.value(),
            'absence_deduction': self.absence_deduction_spin.value(),
            'payment_method': self.payment_method_combo.currentText(),
            'payment_date': self.payment_date_edit.date().toString('yyyy-MM-dd'),
            'payment_status': self.payment_status_combo.currentText(),
            'total_amount': float(self.total_label.text().split(':')[1].replace('ريال', '').strip().replace(',', ''))
        }
        
        if self.current_salary_id:
            success, error = self.salary_controller.update_salary(self.current_salary_id, data)
            message = "تم تحديث الراتب بنجاح" if success else f"فشل تحديث الراتب: {error}"
        else:
            success, error = self.salary_controller.add_salary(data)
            message = "تم حفظ الراتب بنجاح" if success else f"فشل حفظ الراتب: {error}"
        
        if success:
            QMessageBox.information(self, "نجاح", message)
            self.clear_form()
        else:
            QMessageBox.warning(self, "خطأ", message)

    def clear_form(self):
        """Clear all form fields."""
        self.current_salary_id = None
        self.employee_id_edit.clear()
        self.basic_salary_spin.setValue(0)
        self.housing_allowance_spin.setValue(0)
        self.transport_allowance_spin.setValue(0)
        self.loan_deduction_spin.setValue(0)
        self.absence_deduction_spin.setValue(0)
        self.payment_method_combo.setCurrentIndex(0)
        self.payment_date_edit.setDate(QDate.currentDate())
        self.payment_status_combo.setCurrentIndex(0)
        self.total_label.clear()

    def load_salary(self, salary_data):
        """Load salary data into the form."""
        self.current_salary_id = salary_data.get('id')
        self.employee_id_edit.setText(str(salary_data.get('employee_id', '')))
        self.basic_salary_spin.setValue(float(salary_data.get('basic_salary', 0)))
        self.housing_allowance_spin.setValue(float(salary_data.get('housing_allowance', 0)))
        self.transport_allowance_spin.setValue(float(salary_data.get('transport_allowance', 0)))
        self.loan_deduction_spin.setValue(float(salary_data.get('loan_deduction', 0)))
        self.absence_deduction_spin.setValue(float(salary_data.get('absence_deduction', 0)))
        self.payment_method_combo.setCurrentText(salary_data.get('payment_method', 'تحويل بنكي'))
        self.payment_date_edit.setDate(QDate.fromString(salary_data.get('payment_date', datetime.now().strftime('%Y-%m-%d')), 'yyyy-MM-dd'))
        self.payment_status_combo.setCurrentText(salary_data.get('payment_status', 'معلق'))
        
        # Calculate total
        self.calculate_salary()
