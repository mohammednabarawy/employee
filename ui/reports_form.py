from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QSpinBox)
from PyQt5.QtCore import Qt
from datetime import datetime

class ReportWidget(QWidget):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("report_widget")
        self.setStyleSheet("""
            QWidget#report_widget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title_label)
        
        # Content will be added by child classes
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        layout.addWidget(self.content_widget)

class TableReport(ReportWidget):
    def __init__(self, title, headers):
        super().__init__(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)
        
        self.content_layout.addWidget(self.table)

class ChartReport(ReportWidget):
    def __init__(self, title):
        super().__init__(title)
        
        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        
        self.content_layout.addWidget(self.chart_view)

class ReportsForm(QWidget):
    def __init__(self, employee_controller, payroll_controller):
        super().__init__()
        self.employee_controller = employee_controller
        self.payroll_controller = payroll_controller
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add title
        title = QLabel("التقارير")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Report type selector
        type_layout = QHBoxLayout()
        type_label = QLabel("نوع التقرير:")
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "تقرير الموظفين",
            "تقرير الرواتب",
            "تقرير الحضور والانصراف"
        ])
        self.type_combo.currentIndexChanged.connect(self.on_report_type_changed)
        
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Period selector for payroll reports
        period_layout = QHBoxLayout()
        
        year_label = QLabel("السنة:")
        self.year_combo = QComboBox()
        current_year = datetime.now().year
        self.year_combo.addItems([str(year) for year in range(current_year - 2, current_year + 3)])
        self.year_combo.setCurrentText(str(current_year))
        
        month_label = QLabel("الشهر:")
        self.month_combo = QComboBox()
        self.month_combo.addItems([
            "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ])
        current_month = datetime.now().month
        self.month_combo.setCurrentIndex(current_month - 1)
        
        period_layout.addWidget(year_label)
        period_layout.addWidget(self.year_combo)
        period_layout.addWidget(month_label)
        period_layout.addWidget(self.month_combo)
        layout.addLayout(period_layout)

        # Generate button
        self.generate_btn = QPushButton("إنشاء التقرير")
        self.generate_btn.clicked.connect(self.generate_report)
        layout.addWidget(self.generate_btn)

        # Report table
        self.report_table = QTableWidget()
        layout.addWidget(self.report_table)

        # Initially load employee report
        self.load_employee_report()

    def on_report_type_changed(self, index):
        if index == 0:  # Employee report
            self.load_employee_report()
        elif index == 1:  # Payroll report
            self.load_payroll_report()
        elif index == 2:  # Attendance report
            self.load_attendance_report()

    def load_employee_report(self):
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "الرقم", "الاسم", "القسم", "تاريخ التعيين",
            "الراتب الأساسي", "الحالة"
        ])
        
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.report_table.setRowCount(len(employees))
            for i, emp in enumerate(employees):
                self.report_table.setItem(i, 0, QTableWidgetItem(str(emp['id'])))
                self.report_table.setItem(i, 1, QTableWidgetItem(emp['name']))
                self.report_table.setItem(i, 2, QTableWidgetItem(emp.get('department_name', '')))
                self.report_table.setItem(i, 3, QTableWidgetItem(str(emp['hire_date'])))
                self.report_table.setItem(i, 4, QTableWidgetItem(f"{float(emp['basic_salary']):,.2f}"))
                self.report_table.setItem(i, 5, QTableWidgetItem(emp.get('employee_status', 'نشط')))
        
        self.report_table.resizeColumnsToContents()

    def load_payroll_report(self):
        year = int(self.year_combo.currentText())
        month = self.month_combo.currentIndex() + 1
        
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels([
            "الموظف", "الراتب الأساسي", "البدلات",
            "الاستقطاعات", "صافي الراتب", "طريقة الدفع", "الحالة"
        ])
        
        success, period_id = self.payroll_controller.get_period_id(year, month)
        if not success:
            self.report_table.setRowCount(0)
            return
            
        success, entries = self.payroll_controller.get_payroll_entries(period_id)
        if success:
            self.report_table.setRowCount(len(entries))
            for i, entry in enumerate(entries):
                self.report_table.setItem(i, 0, QTableWidgetItem(entry['employee_name']))
                self.report_table.setItem(i, 1, QTableWidgetItem(f"{float(entry['basic_salary']):,.2f}"))
                self.report_table.setItem(i, 2, QTableWidgetItem(f"{float(entry['total_allowances']):,.2f}"))
                self.report_table.setItem(i, 3, QTableWidgetItem(f"{float(entry['total_deductions']):,.2f}"))
                self.report_table.setItem(i, 4, QTableWidgetItem(f"{float(entry['net_salary']):,.2f}"))
                self.report_table.setItem(i, 5, QTableWidgetItem(entry['payment_method_name']))
                self.report_table.setItem(i, 6, QTableWidgetItem(entry['payment_status']))
        
        self.report_table.resizeColumnsToContents()

    def load_attendance_report(self):
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "الموظف", "التاريخ", "وقت الحضور",
            "وقت الانصراف", "ساعات العمل", "الحالة"
        ])
        
        # TODO: Implement attendance report
        self.report_table.setRowCount(0)

    def generate_report(self):
        report_type = self.type_combo.currentIndex()
        if report_type == 0:
            self.load_employee_report()
        elif report_type == 1:
            self.load_payroll_report()
        elif report_type == 2:
            self.load_attendance_report()
