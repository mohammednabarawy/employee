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
    def __init__(self, employee_controller, payroll_controller):
        super().__init__()
        self.employee_controller = employee_controller
        self.payroll_controller = payroll_controller
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
        # Add company header
        company_name = CompanyInfo.get_company_name(self.db_file)
        commercial_register = CompanyInfo.get_commercial_register(self.db_file)
        
        # Set report title based on type
        report_type = self.type_combo.currentIndex()
        report_title = self.type_combo.currentText()
        
        # Create header widget
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        
        # Add company name if available
        if company_name:
            company_label = QLabel(company_name)
            company_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
            company_label.setAlignment(Qt.AlignCenter)
            header_layout.addWidget(company_label)
            
            # Add commercial register if available
            if commercial_register:
                register_label = QLabel(f"رقم السجل التجاري: {commercial_register}")
                register_label.setAlignment(Qt.AlignCenter)
                register_label.setStyleSheet("color: #7f8c8d;")
                header_layout.addWidget(register_label)
        
        # Add report title
        title_label = QLabel(f"تقرير {report_title}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Add date
        date_label = QLabel(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}")
        date_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(date_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        header_layout.addWidget(separator)
        
        # Clear previous report
        for i in reversed(range(self.layout().count())):
            widget = self.layout().itemAt(i).widget()
            if widget and widget != self.controls_widget:
                widget.deleteLater()
        
        # Add header to layout
        self.layout().addWidget(header_widget)
        
        # Create report content widget
        report_widget = QWidget()
        report_layout = QVBoxLayout(report_widget)
        
        # Create table for report
        self.report_table = QTableWidget()
        self.report_table.setAlternatingRowColors(True)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        report_layout.addWidget(self.report_table)
        
        # Add report to layout
        self.layout().addWidget(report_widget)
        
        # Load report data based on type
        if report_type == 0:
            self.load_employee_report()
        elif report_type == 1:
            self.load_payroll_report()
        elif report_type == 2:
            self.load_attendance_report()

    def print_report(self):
        """Print the current report"""
        # Get company information
        company_name = CompanyInfo.get_company_name(self.db_file)
        commercial_register = CompanyInfo.get_commercial_register(self.db_file)
        
        # Create printer
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        
        # Show print preview dialog
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(lambda p: self.print_preview(p, company_name, commercial_register))
        preview.exec_()
        
    def print_preview(self, printer, company_name, commercial_register):
        """Handle print preview"""
        # Create document
        document = QTextDocument()
        
        # Get report title
        report_type = self.type_combo.currentText()
        
        # Create HTML content
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .company-name {{ font-size: 18px; font-weight: bold; }}
                .company-info {{ font-size: 12px; color: #666; margin-bottom: 10px; }}
                .title {{ font-size: 16px; font-weight: bold; margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: right; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
        """
        
        # Add company info if available
        if company_name:
            html += f'<div class="company-name">{company_name}</div>'
            if commercial_register:
                html += f'<div class="company-info">رقم السجل التجاري: {commercial_register}</div>'
        
        # Add report title and date
        html += f"""
                <div class="title">تقرير {report_type}</div>
                <div>تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
        """
        
        # Add table headers
        for col in range(self.report_table.columnCount()):
            header_text = self.report_table.horizontalHeaderItem(col).text()
            html += f'<th>{header_text}</th>'
        
        html += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add table data
        for row in range(self.report_table.rowCount()):
            html += '<tr>'
            for col in range(self.report_table.columnCount()):
                item = self.report_table.item(row, col)
                text = item.text() if item else ''
                html += f'<td>{text}</td>'
            html += '</tr>'
        
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Set HTML content
        document.setHtml(html)
        
        # Print document
        document.print_(printer)
