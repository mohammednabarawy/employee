from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QSizePolicy, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from PyQt5.QtGui import QPainter, QColor
from datetime import datetime, timedelta
from controllers import ReportController
from utils import chart_utils

class StatCard(QFrame):
    def __init__(self, title, value, icon=None, color="#3498db"):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumSize(200, 120)
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        
        # Value
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {color};
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()

class RecentTable(QTableWidget):
    def __init__(self, headers):
        super().__init__()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)

class Dashboard(QWidget):
    def __init__(self, employee_controller, payroll_controller, db):
        super().__init__()
        self.employee_controller = employee_controller
        self.payroll_controller = payroll_controller
        self.db = db
        self.report_controller = ReportController(db)
        self.init_ui()
        self.refresh_data()
        self.load_data()
        
        # Setup auto-refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_data)
        self.timer.start(30000)  # Refresh every 30 seconds

    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)
        
        # Title
        title = QLabel("لوحة المعلومات")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        content_layout.addWidget(title)
        
        # Add statistics cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.total_employees_card = StatCard("إجمالي الموظفين", "0", color="#3498db")
        self.active_employees_card = StatCard("الموظفين النشطين", "0", color="#2ecc71")
        self.total_salaries_card = StatCard("إجمالي الرواتب", "0", color="#e74c3c")
        self.avg_salary_card = StatCard("متوسط الراتب", "0", color="#f1c40f")
        
        stats_layout.addWidget(self.total_employees_card)
        stats_layout.addWidget(self.active_employees_card)
        stats_layout.addWidget(self.total_salaries_card)
        stats_layout.addWidget(self.avg_salary_card)
        content_layout.addLayout(stats_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        
        # Department distribution chart
        dept_chart = QChart()
        dept_chart.setTitle("توزيع الموظفين حسب الأقسام")
        dept_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.dept_series = QPieSeries()
        dept_chart.addSeries(self.dept_series)
        
        dept_chart_view = QChartView(dept_chart)
        dept_chart_view.setRenderHint(QPainter.Antialiasing)
        charts_layout.addWidget(dept_chart_view)
        
        # Salary distribution chart
        salary_chart = QChart()
        salary_chart.setTitle("توزيع الرواتب")
        salary_chart.setAnimationOptions(QChart.SeriesAnimations)
        self.salary_series = QBarSeries()
        
        salary_axis_y = QValueAxis()
        salary_axis_y.setTitleText("عدد الموظفين")
        salary_chart.addAxis(salary_axis_y, Qt.AlignLeft)
        
        salary_axis_x = QBarCategoryAxis()
        salary_chart.addAxis(salary_axis_x, Qt.AlignBottom)
        
        salary_chart.addSeries(self.salary_series)
        self.salary_series.attachAxis(salary_axis_y)
        self.salary_series.attachAxis(salary_axis_x)
        
        salary_chart_view = QChartView(salary_chart)
        salary_chart_view.setRenderHint(QPainter.Antialiasing)
        charts_layout.addWidget(salary_chart_view)
        
        content_layout.addLayout(charts_layout)
        
        # Recent activities section
        recent_layout = QHBoxLayout()
        
        # Recent employees
        recent_employees_layout = QVBoxLayout()
        recent_employees_title = QLabel("آخر الموظفين المضافين")
        recent_employees_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        recent_employees_layout.addWidget(recent_employees_title)
        
        self.recent_employees_table = RecentTable(["الاسم", "المنصب", "تاريخ التعيين"])
        recent_employees_layout.addWidget(self.recent_employees_table)
        recent_layout.addLayout(recent_employees_layout)
        
        # Recent salaries
        recent_salaries_layout = QVBoxLayout()
        recent_salaries_title = QLabel("آخر المدفوعات")
        recent_salaries_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        recent_salaries_layout.addWidget(recent_salaries_title)
        
        self.recent_payroll_table = RecentTable(["الموظف", "المبلغ", "التاريخ"])
        recent_salaries_layout.addWidget(self.recent_payroll_table)
        recent_layout.addLayout(recent_salaries_layout)
        
        content_layout.addLayout(recent_layout)
        
        # Real-time dashboard components
        metrics_layout = QHBoxLayout()
        self.employee_count = QLabel('Loading...')
        self.payroll_total = QLabel('Loading...')
        self.active_users = QLabel('Loading...')
        
        for widget in [self.employee_count, self.payroll_total, self.active_users]:
            widget.setAlignment(Qt.AlignCenter)
            widget.setStyleSheet('font-size: 16px; padding: 15px;')
            metrics_layout.addWidget(widget)
        
        content_layout.addLayout(metrics_layout)

        charts_layout = QHBoxLayout()
        self.payroll_chart = QChartView()
        self.attendance_chart = QChartView()
        
        for chart in [self.payroll_chart, self.attendance_chart]:
            chart.setRenderHint(QPainter.Antialiasing)
            charts_layout.addWidget(chart)
        
        content_layout.addLayout(charts_layout)
        
        # Set content widget to scroll area
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def refresh_data(self):
        """Refresh dashboard data"""
        try:
            # Get employee count - handle tuple return value (success, data)
            result = self.employee_controller.get_all_employees()
            if isinstance(result, tuple) and len(result) == 2:
                success, employees = result
                if not success or not employees:
                    employees = []
            else:
                # Direct list return
                employees = result if isinstance(result, list) else []
            
            # Update stat cards safely
            for card in [self.total_employees_card, self.active_employees_card, self.total_salaries_card, self.avg_salary_card]:
                if hasattr(card, 'set_value'):
                    card.set_value(str(len(employees)))
                    break
            
            # Only proceed if we have employees
            if employees:
                # Get recent employees (up to 5)
                try:
                    recent_employees = sorted(employees, key=lambda x: x.get('hire_date', ''), reverse=True)
                    if len(recent_employees) > 5:
                        recent_employees = recent_employees[:5]
                    
                    # Clear and update recent employees table
                    self.recent_employees_table.setRowCount(0)
                    for i, emp in enumerate(recent_employees):
                        self.recent_employees_table.insertRow(i)
                        self.recent_employees_table.setItem(i, 0, QTableWidgetItem(str(emp.get('name', ''))))
                        self.recent_employees_table.setItem(i, 1, QTableWidgetItem(str(emp.get('position', ''))))
                        self.recent_employees_table.setItem(i, 2, QTableWidgetItem(str(emp.get('hire_date', ''))))
                except Exception as e:
                    print(f"Error updating employee table: {str(e)}")
            
            # Get recent payroll entries
            result = self.payroll_controller.get_recent_entries(5)
            if isinstance(result, tuple) and len(result) == 2:
                success, entries = result
                if not success or not entries:
                    entries = []
            else:
                # Direct list return
                entries = result if isinstance(result, list) else []
            
            # Update payroll table if we have entries
            if entries:
                try:
                    # Clear and update recent payroll table
                    self.recent_payroll_table.setRowCount(0)
                    for i, entry in enumerate(entries):
                        self.recent_payroll_table.insertRow(i)
                        self.recent_payroll_table.setItem(i, 0, QTableWidgetItem(str(entry.get('employee_name', ''))))
                        self.recent_payroll_table.setItem(i, 1, QTableWidgetItem(str(entry.get('gross_salary', 0))))
                        self.recent_payroll_table.setItem(i, 2, QTableWidgetItem(str(entry.get('payment_date', ''))))
                except Exception as e:
                    print(f"Error updating payroll table: {str(e)}")
            
            # Try to update real-time metrics
            try:
                self.load_data()
            except Exception as inner_e:
                print(f"Warning: Could not update real-time metrics: {str(inner_e)}")
            
        except Exception as e:
            print(f"Error refreshing dashboard data: {str(e)}")

    def load_data(self):
        # Load metrics
        self.update_employee_count()
        self.update_payroll_total()
        self.update_active_users()
        
        # Load charts
        self.update_payroll_chart()
        self.update_attendance_chart()

    def update_employee_count(self):
        success, count = self.report_controller.get_employee_count()
        if success:
            self.employee_count.setText(f"Total Employees\n{count}")

    def update_payroll_total(self):
        success, total = self.report_controller.get_monthly_payroll()
        if success:
            self.payroll_total.setText(f"Monthly Payroll\n{total:,.2f} EGP")

    def update_active_users(self):
        success, count = self.report_controller.get_active_users()
        if success:
            self.active_users.setText(f"Active Users\n{count}")

    def update_payroll_chart(self):
        success, data = self.report_controller.get_payroll_distribution()
        if success:
            chart = chart_utils.create_pie_chart("Payroll Distribution", data)
            self.payroll_chart.setChart(chart.chart())

    def update_attendance_chart(self):
        success, data = self.report_controller.get_attendance_stats()
        if success:
            chart = chart_utils.create_bar_chart(
                "Attendance Overview",
                data['departments'],
                data['attendance_rates'],
                QColor('#27ae60')
            )
            self.attendance_chart.setChart(chart.chart())
