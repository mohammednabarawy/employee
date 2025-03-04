from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QComboBox, QDateEdit, QGroupBox, QFormLayout,
                             QFrame, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import qtawesome as qta
from datetime import datetime
from ui.styles import Styles

class SalaryHistoryDialog(QDialog):
    """Dialog to display salary history for an employee"""
    
    def __init__(self, payroll_controller, employee_data, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.employee_data = employee_data
        self.init_ui()
        self.load_history()
        
    def init_ui(self):
        self.setWindowTitle(f"سجل الرواتب - {self.employee_data.get('name', '')}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Employee info header
        info_frame = QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QHBoxLayout(info_frame)
        
        # Employee details
        details_group = QGroupBox("بيانات الموظف")
        details_layout = QFormLayout(details_group)
        
        name_label = QLabel(self.employee_data.get('name', ''))
        name_label.setObjectName("employeeName")
        
        code_label = QLabel(self.employee_data.get('employee_code', ''))
        department_label = QLabel(self.employee_data.get('department_name', ''))
        position_label = QLabel(self.employee_data.get('position_name', ''))
        
        details_layout.addRow(QLabel("الاسم:"), name_label)
        details_layout.addRow(QLabel("الرقم الوظيفي:"), code_label)
        details_layout.addRow(QLabel("القسم:"), department_label)
        details_layout.addRow(QLabel("المسمى الوظيفي:"), position_label)
        
        # Salary summary
        summary_group = QGroupBox("ملخص الراتب")
        summary_layout = QFormLayout(summary_group)
        
        self.basic_salary_label = QLabel(f"{float(self.employee_data.get('basic_salary', 0)):,.2f}")
        self.last_payment_label = QLabel("-")
        self.total_payments_label = QLabel("-")
        
        summary_layout.addRow(QLabel("الراتب الأساسي:"), self.basic_salary_label)
        summary_layout.addRow(QLabel("آخر راتب:"), self.last_payment_label)
        summary_layout.addRow(QLabel("إجمالي المدفوعات:"), self.total_payments_label)
        
        info_layout.addWidget(details_group)
        info_layout.addWidget(summary_group)
        
        layout.addWidget(info_frame)
        
        # Filter controls
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Year filter
        year_layout = QHBoxLayout()
        year_icon = QLabel()
        year_icon.setPixmap(qta.icon('fa5s.calendar-alt', color='#3498db').pixmap(16, 16))
        self.year_combo = QComboBox()
        
        # Add current year and previous years
        current_year = datetime.now().year
        for year in range(current_year, current_year - 5, -1):
            self.year_combo.addItem(str(year), year)
            
        year_layout.addWidget(year_icon)
        year_layout.addWidget(self.year_combo)
        
        # Date range filter
        date_range_layout = QHBoxLayout()
        date_icon = QLabel()
        date_icon.setPixmap(qta.icon('fa5s.calendar-day', color='#3498db').pixmap(16, 16))
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-12))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        
        date_range_layout.addWidget(date_icon)
        date_range_layout.addWidget(QLabel("من:"))
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(QLabel("إلى:"))
        date_range_layout.addWidget(self.end_date)
        
        # Filter button
        self.filter_button = QPushButton("تطبيق")
        self.filter_button.setIcon(qta.icon('fa5s.filter', color='white'))
        self.filter_button.clicked.connect(self.apply_filter)
        
        filter_layout.addLayout(year_layout)
        filter_layout.addLayout(date_range_layout)
        filter_layout.addWidget(self.filter_button)
        
        layout.addWidget(filter_frame)
        
        # Salary history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "الفترة", "الراتب الأساسي", "البدلات", "الخصومات", 
            "التعديلات", "أيام العمل", "صافي الراتب", "حالة الدفع"
        ])
        
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.history_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.print_button = QPushButton("طباعة")
        self.print_button.setIcon(qta.icon('fa5s.print', color='white'))
        self.print_button.clicked.connect(self.print_history)
        
        self.export_button = QPushButton("تصدير")
        self.export_button.setIcon(qta.icon('fa5s.file-export', color='white'))
        self.export_button.clicked.connect(self.export_history)
        
        self.close_button = QPushButton("إغلاق")
        self.close_button.setIcon(qta.icon('fa5s.times', color='white'))
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.print_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def load_history(self, start_date=None, end_date=None):
        """Load salary history for the employee"""
        employee_id = self.employee_data.get('id')
        
        # Convert QDate to string if provided
        if isinstance(start_date, QDate):
            start_date = start_date.toString("yyyy-MM-dd")
            
        if isinstance(end_date, QDate):
            end_date = end_date.toString("yyyy-MM-dd")
            
        success, history = self.payroll_controller.get_employee_salary_history(
            employee_id, start_date, end_date
        )
        
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل سجل الرواتب: {history}")
            return
            
        # Update summary
        if history:
            # Last payment
            last_payment = history[0]
            self.last_payment_label.setText(f"{float(last_payment['net_salary']):,.2f}")
            
            # Total payments
            total = sum(entry['net_salary'] for entry in history if entry['payment_status'] == 'paid')
            self.total_payments_label.setText(f"{float(total):,.2f}")
            
        # Clear table
        self.history_table.setRowCount(0)
        
        # Populate table
        for i, entry in enumerate(history):
            self.history_table.insertRow(i)
            
            # Period
            period_text = f"{entry['period_month']}/{entry['period_year']}"
            period_item = QTableWidgetItem(period_text)
            period_item.setTextAlignment(Qt.AlignCenter)
            
            # Basic salary
            basic_salary_item = QTableWidgetItem(f"{float(entry['basic_salary']):,.2f}")
            basic_salary_item.setTextAlignment(Qt.AlignCenter)
            
            # Allowances
            allowances_item = QTableWidgetItem(f"{float(entry['total_allowances']):,.2f}")
            allowances_item.setTextAlignment(Qt.AlignCenter)
            
            # Deductions
            deductions_item = QTableWidgetItem(f"{float(entry['total_deductions']):,.2f}")
            deductions_item.setTextAlignment(Qt.AlignCenter)
            
            # Adjustments
            adjustments_item = QTableWidgetItem(f"{float(entry['total_adjustments']):,.2f}")
            adjustments_item.setTextAlignment(Qt.AlignCenter)
            
            # Working days
            working_days_item = QTableWidgetItem(str(entry['working_days']))
            working_days_item.setTextAlignment(Qt.AlignCenter)
            
            # Net salary
            net_salary_item = QTableWidgetItem(f"{float(entry['net_salary']):,.2f}")
            net_salary_item.setTextAlignment(Qt.AlignCenter)
            
            # Payment status
            status_map = {
                'pending': 'قيد الانتظار',
                'processing': 'قيد المعالجة',
                'paid': 'تم الدفع',
                'cancelled': 'ملغي'
            }
            
            status_text = status_map.get(entry['payment_status'], entry['payment_status'])
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            
            # Set background color based on status
            if entry['payment_status'] == 'paid':
                status_item.setBackground(QColor('#d4efdf'))  # Light green
            elif entry['payment_status'] == 'pending':
                status_item.setBackground(QColor('#eaeded'))  # Light gray
            elif entry['payment_status'] == 'processing':
                status_item.setBackground(QColor('#ebf5fb'))  # Light blue
            elif entry['payment_status'] == 'cancelled':
                status_item.setBackground(QColor('#fadbd8'))  # Light red
                
            # Add items to row
            self.history_table.setItem(i, 0, period_item)
            self.history_table.setItem(i, 1, basic_salary_item)
            self.history_table.setItem(i, 2, allowances_item)
            self.history_table.setItem(i, 3, deductions_item)
            self.history_table.setItem(i, 4, adjustments_item)
            self.history_table.setItem(i, 5, working_days_item)
            self.history_table.setItem(i, 6, net_salary_item)
            self.history_table.setItem(i, 7, status_item)
            
        self.history_table.resizeColumnsToContents()
        
    def apply_filter(self):
        """Apply date filter to history"""
        selected_year = self.year_combo.currentData()
        
        if selected_year:
            # Filter by year
            start_date = QDate(selected_year, 1, 1)
            end_date = QDate(selected_year, 12, 31)
        else:
            # Filter by date range
            start_date = self.start_date.date()
            end_date = self.end_date.date()
            
        self.load_history(start_date, end_date)
        
    def print_history(self):
        """Print salary history report"""
        # Implementation for printing would go here
        QMessageBox.information(self, "طباعة", "جاري إعداد التقرير للطباعة...")
        
    def export_history(self):
        """Export salary history to Excel or CSV"""
        # Implementation for exporting would go here
        QMessageBox.information(self, "تصدير", "جاري تصدير البيانات...")
