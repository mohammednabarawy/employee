from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTableWidget, QFrame,
                             QTableWidgetItem, QDateEdit, QFileDialog,
                             QMessageBox, QHeaderView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from PyQt5.QtGui import QPainter
import pandas as pd
from datetime import datetime

class ReportWidget(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("report_widget")
        self.setStyleSheet("""
            QFrame#report_widget {
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
    def __init__(self, employee_controller, salary_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.salary_controller = salary_controller
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("التقارير")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Report type selector
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "تقرير الموظفين",
            "تقرير الرواتب",
            "تقرير الحضور",
            "تقرير الأقسام",
            "تقرير المدفوعات"
        ])
        self.report_type_combo.currentTextChanged.connect(self.report_type_changed)
        header_layout.addWidget(QLabel("نوع التقرير:"))
        header_layout.addWidget(self.report_type_combo)
        
        # Date range
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        
        header_layout.addWidget(QLabel("من:"))
        header_layout.addWidget(self.start_date)
        header_layout.addWidget(QLabel("إلى:"))
        header_layout.addWidget(self.end_date)
        
        # Export button
        self.export_btn = QPushButton("تصدير")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.export_btn.clicked.connect(self.export_report)
        header_layout.addWidget(self.export_btn)
        
        # Generate button
        self.generate_btn = QPushButton("إنشاء التقرير")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_report)
        header_layout.addWidget(self.generate_btn)
        
        layout.addLayout(header_layout)
        
        # Reports container
        self.reports_layout = QVBoxLayout()
        layout.addLayout(self.reports_layout)
        
        # Initial report
        self.report_type_changed(self.report_type_combo.currentText())
    
    def clear_reports(self):
        while self.reports_layout.count():
            item = self.reports_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def report_type_changed(self, report_type):
        self.clear_reports()
        self.current_report_type = report_type
        self.generate_report()
    
    def generate_report(self):
        self.clear_reports()
        
        if self.current_report_type == "تقرير الموظفين":
            self.generate_employee_report()
        elif self.current_report_type == "تقرير الرواتب":
            self.generate_salary_report()
        elif self.current_report_type == "تقرير الحضور":
            self.generate_attendance_report()
        elif self.current_report_type == "تقرير الأقسام":
            self.generate_department_report()
        elif self.current_report_type == "تقرير المدفوعات":
            self.generate_payment_report()
    
    def generate_employee_report(self):
        # Employee List
        headers = ["الاسم", "القسم", "المنصب", "تاريخ التعيين", "الراتب الأساسي", "الحالة"]
        employee_list = TableReport("قائمة الموظفين", headers)
        
        success, employees = self.employee_controller.get_all_employees()
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل بيانات الموظفين: {employees}")
            return
            
        employee_list.table.setRowCount(len(employees))
        
        for i, emp in enumerate(employees):
            employee_list.table.setItem(i, 0, QTableWidgetItem(emp.get('name', '')))
            employee_list.table.setItem(i, 1, QTableWidgetItem(emp.get('department_name', 'الإدارة العامة')))
            employee_list.table.setItem(i, 2, QTableWidgetItem(emp.get('position_title', 'موظف')))
            employee_list.table.setItem(i, 3, QTableWidgetItem(emp.get('hire_date', '')))
            employee_list.table.setItem(i, 4, QTableWidgetItem(f"{float(emp.get('basic_salary', 0) or 0):,.2f}"))
            employee_list.table.setItem(i, 5, QTableWidgetItem(emp.get('employee_status', 'نشط')))
        
        self.reports_layout.addWidget(employee_list)
        
        # Department Statistics Table instead of Chart
        headers = ["القسم", "عدد الموظفين", "النسبة المئوية"]
        dept_stats = TableReport("إحصائيات الأقسام", headers)
        
        dept_counts = {}
        total_employees = len(employees)
        
        for emp in employees:
            dept = emp.get('department_name', 'الإدارة العامة')
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        dept_stats.table.setRowCount(len(dept_counts))
        
        for i, (dept, count) in enumerate(dept_counts.items()):
            percentage = (count / total_employees * 100) if total_employees > 0 else 0
            dept_stats.table.setItem(i, 0, QTableWidgetItem(dept))
            dept_stats.table.setItem(i, 1, QTableWidgetItem(str(count)))
            dept_stats.table.setItem(i, 2, QTableWidgetItem(f"{percentage:.1f}%"))
        
        self.reports_layout.addWidget(dept_stats)
    
    def generate_salary_report(self):
        # Salary Summary
        headers = ["المستوى", "عدد الموظفين", "متوسط الراتب", "إجمالي الرواتب"]
        salary_summary = TableReport("ملخص الرواتب", headers)
        
        success, employees = self.employee_controller.get_all_employees()
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل بيانات الموظفين: {employees}")
            return
        
        salary_ranges = [
            (0, 5000, "0-5,000"),
            (5000, 10000, "5,000-10,000"),
            (10000, 15000, "10,000-15,000"),
            (15000, 20000, "15,000-20,000"),
            (20000, float('inf'), "20,000+")
        ]
        
        salary_summary.table.setRowCount(len(salary_ranges))
        
        for i, (start, end, label) in enumerate(salary_ranges):
            employees_in_range = [emp for emp in employees 
                                if start <= float(emp.get('basic_salary', 0) or 0) < end]
            count = len(employees_in_range)
            avg_salary = sum(float(emp.get('basic_salary', 0) or 0) for emp in employees_in_range) / count if count > 0 else 0
            total_salary = sum(float(emp.get('basic_salary', 0) or 0) for emp in employees_in_range)
            
            salary_summary.table.setItem(i, 0, QTableWidgetItem(label))
            salary_summary.table.setItem(i, 1, QTableWidgetItem(str(count)))
            salary_summary.table.setItem(i, 2, QTableWidgetItem(f"{avg_salary:,.2f}"))
            salary_summary.table.setItem(i, 3, QTableWidgetItem(f"{total_salary:,.2f}"))
        
        self.reports_layout.addWidget(salary_summary)
        
        # Salary Distribution Chart
        salary_chart = ChartReport("توزيع الرواتب")
        series = QBarSeries()
        
        bar_set = QBarSet("عدد الموظفين")
        categories = []
        
        for start, end, label in salary_ranges:
            count = sum(1 for emp in employees if start <= float(emp.get('basic_salary', 0) or 0) < end)
            bar_set.append(count)
            categories.append(label)
        
        series.append(bar_set)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("عدد الموظفين")
        salary_chart.chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        salary_chart.chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        salary_chart.chart.addSeries(series)
        self.reports_layout.addWidget(salary_chart)
    
    def generate_payment_report(self):
        headers = ["الموظف", "المبلغ", "تاريخ الدفع", "طريقة الدفع", "الحالة"]
        payment_list = TableReport("سجل المدفوعات", headers)
        
        start_date = self.start_date.date().toString(Qt.ISODate)
        end_date = self.end_date.date().toString(Qt.ISODate)
        
        payments = self.salary_controller.get_payments_by_date_range(start_date, end_date)
        if not payments:
            payment_list.table.setRowCount(0)
            self.reports_layout.addWidget(payment_list)
            return
            
        success, employees = self.employee_controller.get_all_employees()
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل بيانات الموظفين: {employees}")
            return
            
        employees_dict = {emp['id']: emp for emp in employees}
        payment_list.table.setRowCount(len(payments))
        
        for i, payment in enumerate(payments):
            try:
                emp = employees_dict.get(payment.get('employee_id'))
                payment_list.table.setItem(i, 0, QTableWidgetItem(emp['name'] if emp else str(payment.get('employee_id', 'غير معروف'))))
                payment_list.table.setItem(i, 1, QTableWidgetItem(f"{float(payment.get('amount', 0)):,.2f}"))
                payment_list.table.setItem(i, 2, QTableWidgetItem(payment.get('payment_date', '')))
                payment_list.table.setItem(i, 3, QTableWidgetItem(payment.get('payment_method', '')))
                payment_list.table.setItem(i, 4, QTableWidgetItem(payment.get('status', '')))
            except (TypeError, ValueError, KeyError) as e:
                print(f"Error processing payment {payment}: {str(e)}")
                continue
        
        self.reports_layout.addWidget(payment_list)
        
        # Add payment summary
        summary_headers = ["إجمالي المدفوعات", "عدد المدفوعات", "متوسط المدفوعات"]
        summary = TableReport("ملخص المدفوعات", summary_headers)
        summary.table.setRowCount(1)
        
        try:
            total_amount = sum(float(payment.get('amount', 0)) for payment in payments)
            payment_count = len(payments)
            avg_amount = total_amount / payment_count if payment_count > 0 else 0
            
            summary.table.setItem(0, 0, QTableWidgetItem(f"{total_amount:,.2f}"))
            summary.table.setItem(0, 1, QTableWidgetItem(str(payment_count)))
            summary.table.setItem(0, 2, QTableWidgetItem(f"{avg_amount:,.2f}"))
        except (TypeError, ValueError) as e:
            print(f"Error calculating payment summary: {str(e)}")
            
        self.reports_layout.addWidget(summary)
    
    def export_report(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "تصدير التقرير",
            "",
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        
        if not file_name:
            return
        
        try:
            if self.current_report_type == "تقرير الموظفين":
                self.export_employee_report(file_name)
            elif self.current_report_type == "تقرير الرواتب":
                self.export_salary_report(file_name)
            elif self.current_report_type == "تقرير المدفوعات":
                self.export_payment_report(file_name)
            
            QMessageBox.information(self, "نجاح", "تم تصدير التقرير بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تصدير التقرير: {str(e)}")
    
    def export_employee_report(self, file_name):
        employees = self.employee_controller.get_all_employees()
        df = pd.DataFrame(employees)
        df.to_excel(file_name, index=False) if file_name.endswith('.xlsx') else df.to_csv(file_name, index=False)
    
    def export_salary_report(self, file_name):
        employees = self.employee_controller.get_all_employees()
        df = pd.DataFrame([{
            'name': emp['name'],
            'department': emp['department'],
            'position': emp['position'],
            'basic_salary': emp['basic_salary'],
            'currency': emp['currency']
        } for emp in employees])
        df.to_excel(file_name, index=False) if file_name.endswith('.xlsx') else df.to_csv(file_name, index=False)
    
    def export_payment_report(self, file_name):
        start_date = self.start_date.date().toString(Qt.ISODate)
        end_date = self.end_date.date().toString(Qt.ISODate)
        payments = self.salary_controller.get_payments_by_date_range(start_date, end_date)
        df = pd.DataFrame(payments)
        df.to_excel(file_name, index=False) if file_name.endswith('.xlsx') else df.to_csv(file_name, index=False)
