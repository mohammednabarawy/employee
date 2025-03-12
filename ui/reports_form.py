from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QSpinBox, QHeaderView, QFrame,
                             )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QTextDocument
from PyQt5.QtChart import QChart, QChartView
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from datetime import datetime
from utils.company_info import CompanyInfo

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
    def __init__(self, employee_controller, payroll_controller, attendance_controller):
        super().__init__()
        self.employee_controller = employee_controller
        self.payroll_controller = payroll_controller
        self.attendance_controller = attendance_controller
        self.db_file = self.employee_controller.db.db_file
        self.init_ui()

    def init_ui(self):
        """Initialize the UI"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create controls widget
        self.controls_widget = QWidget()
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add title
        title = QLabel("التقارير")
        title.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(title)

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
        controls_layout.addLayout(type_layout)

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
        controls_layout.addLayout(period_layout)

        # Generate button
        self.generate_btn = QPushButton("إنشاء التقرير")
        self.generate_btn.clicked.connect(self.generate_report)
        controls_layout.addWidget(self.generate_btn)

        # Print button
        self.print_btn = QPushButton("طباعة التقرير")
        self.print_btn.clicked.connect(self.print_report)
        controls_layout.addWidget(self.print_btn)

        main_layout.addWidget(self.controls_widget)

        # Report table
        self.report_table = QTableWidget()
        main_layout.addWidget(self.report_table)

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
        employees = self.employee_controller.get_all_employees()
        
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "الرقم", "الاسم", "القسم", "تاريخ التعيين",
            "الراتب الأساسي", "الحالة"
        ])
        
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
        
        self.report_table.setColumnCount(9)
        self.report_table.setHorizontalHeaderLabels([
            "الموظف", "الراتب الأساسي", "أيام الحضور", "أيام الغياب",
            "البدلات", "الخصومات", "خصم الغياب", "صافي الراتب", "الحالة"
        ])
        
        success, period_id = self.payroll_controller.get_period_id(year, month)
        if not success:
            self.report_table.setRowCount(0)
            return
            
        success, entries = self.payroll_controller.get_payroll_entries(period_id)
        if success:
            self.report_table.setRowCount(len(entries))
            for i, entry in enumerate(entries):
                # Get attendance data
                attendance_data = self.attendance_controller.get_attendance_data_for_period(
                    entry['employee_id'],
                    period_id
                )
                if attendance_data:
                    present_days = attendance_data.get('present_days', 0)
                    absent_days = attendance_data.get('absent_days', 0)
                else:
                    present_days = 0
                    absent_days = 0
                    
                self.report_table.setItem(i, 0, QTableWidgetItem(entry.get('employee_name', '')))
                self.report_table.setItem(i, 1, QTableWidgetItem(f"{float(entry.get('basic_salary', 0)):,.2f}"))
                self.report_table.setItem(i, 2, QTableWidgetItem(str(present_days)))
                self.report_table.setItem(i, 3, QTableWidgetItem(str(absent_days)))
                self.report_table.setItem(i, 4, QTableWidgetItem(f"{float(entry.get('total_allowances', 0)):,.2f}"))
                self.report_table.setItem(i, 5, QTableWidgetItem(f"{float(entry.get('total_deductions', 0)):,.2f}"))
                self.report_table.setItem(i, 6, QTableWidgetItem(f"{float(entry.get('absence_deduction', 0)):,.2f}"))
                self.report_table.setItem(i, 7, QTableWidgetItem(f"{float(entry.get('net_salary', 0)):,.2f}"))
                self.report_table.setItem(i, 8, QTableWidgetItem(entry.get('payment_status', '')))
            
            self.report_table.resizeColumnsToContents()

    def load_attendance_report(self):
        year = int(self.year_combo.currentText())
        month = self.month_combo.currentIndex() + 1
        
        self.report_table.setColumnCount(7)
        self.report_table.setHorizontalHeaderLabels([
            "الموظف", "القسم", "أيام العمل", "أيام الحضور",
            "أيام الغياب", "أيام التأخير", "نسبة الحضور"
        ])
        
        success, period_id = self.payroll_controller.get_period_id(year, month)
        if not success:
            self.report_table.setRowCount(0)
            return
            
        employees = self.employee_controller.get_all_employees()
        self.report_table.setRowCount(len(employees))
        
        for i, emp in enumerate(employees):
            attendance_data = self.attendance_controller.get_attendance_data_for_period(
                emp['id'],
                period_id
            )
            
            if attendance_data:
                total_days = attendance_data.get('total_days', 0)
                present_days = attendance_data.get('present_days', 0)
                absent_days = attendance_data.get('absent_days', 0)
                late_days = attendance_data.get('late_days', 0)
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
            else:
                total_days = 0
                present_days = 0
                absent_days = 0
                late_days = 0
                attendance_rate = 0
                
            self.report_table.setItem(i, 0, QTableWidgetItem(emp['name']))
            self.report_table.setItem(i, 1, QTableWidgetItem(emp.get('department_name', '')))
            self.report_table.setItem(i, 2, QTableWidgetItem(str(total_days)))
            self.report_table.setItem(i, 3, QTableWidgetItem(str(present_days)))
            self.report_table.setItem(i, 4, QTableWidgetItem(str(absent_days)))
            self.report_table.setItem(i, 5, QTableWidgetItem(str(late_days)))
            self.report_table.setItem(i, 6, QTableWidgetItem(f"{attendance_rate:.1f}%"))
            
        self.report_table.resizeColumnsToContents()

    def generate_report(self):
        """Generate the selected report"""
        report_type = self.type_combo.currentIndex()
        if report_type == 0:
            self.load_employee_report()
        elif report_type == 1:
            self.load_payroll_report()
        else:
            self.load_attendance_report()

    def print_report(self):
        """Print the current report"""
        printer = QPrinter(QPrinter.HighResolution)
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.handle_print_request)
        preview.exec_()

    def handle_print_request(self, printer):
        """Handle the print request"""
        document = QTextDocument()
        cursor = document.rootFrame().firstCursorPosition()
        
        # Add company info
        company_name = CompanyInfo.get_company_name(self.db_file)
        cursor.insertHtml(f"<h1 style='text-align: center;'>{company_name}</h1>")
        cursor.insertHtml("<br>")
        
        # Add report title
        report_type = self.type_combo.currentText()
        cursor.insertHtml(f"<h2 style='text-align: center;'>{report_type}</h2>")
        cursor.insertHtml("<br>")
        
        # Add period info
        year = self.year_combo.currentText()
        month = self.month_combo.currentText()
        cursor.insertHtml(f"<p style='text-align: center;'>{month} {year}</p>")
        cursor.insertHtml("<br>")
        
        # Create table HTML
        table_html = "<table border='1' cellspacing='0' cellpadding='4' width='100%'>"
        
        # Add headers
        table_html += "<tr>"
        for col in range(self.report_table.columnCount()):
            header = self.report_table.horizontalHeaderItem(col).text()
            table_html += f"<th>{header}</th>"
        table_html += "</tr>"
        
        # Add data
        for row in range(self.report_table.rowCount()):
            table_html += "<tr>"
            for col in range(self.report_table.columnCount()):
                item = self.report_table.item(row, col)
                text = item.text() if item else ""
                table_html += f"<td>{text}</td>"
            table_html += "</tr>"
            
        table_html += "</table>"
        
        cursor.insertHtml(table_html)
        document.print_(printer)
