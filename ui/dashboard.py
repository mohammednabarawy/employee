from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QSizePolicy, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from PyQt5.QtGui import QPainter, QColor
from datetime import datetime, timedelta

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
    def __init__(self, employee_controller, salary_controller):
        super().__init__()
        self.employee_controller = employee_controller
        self.salary_controller = salary_controller
        self.init_ui()
        self.refresh_data()
        
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
        self.salary_series.attachAxis(salary_axis_y)
        
        salary_axis_x = QBarCategoryAxis()
        salary_chart.addAxis(salary_axis_x, Qt.AlignBottom)
        self.salary_series.attachAxis(salary_axis_x)
        
        salary_chart.addSeries(self.salary_series)
        
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
        
        self.recent_employees_table = RecentTable(["الاسم", "القسم", "تاريخ التعيين"])
        recent_employees_layout.addWidget(self.recent_employees_table)
        recent_layout.addLayout(recent_employees_layout)
        
        # Recent salaries
        recent_salaries_layout = QVBoxLayout()
        recent_salaries_title = QLabel("آخر المدفوعات")
        recent_salaries_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        recent_salaries_layout.addWidget(recent_salaries_title)
        
        self.recent_salaries_table = RecentTable(["الموظف", "المبلغ", "التاريخ", "الحالة"])
        recent_salaries_layout.addWidget(self.recent_salaries_table)
        recent_layout.addLayout(recent_salaries_layout)
        
        content_layout.addLayout(recent_layout)
        
        # Set content widget to scroll area
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def refresh_data(self):
        # Get statistics
        employees = self.employee_controller.get_all_employees()
        salaries = self.salary_controller.get_all_salaries()
        
        # Update stat cards
        total_employees = len(employees)
        active_employees = sum(1 for emp in employees if emp['status'] == 'active')
        total_salaries = sum(float(salary['amount']) for salary in salaries)
        avg_salary = total_salaries / total_employees if total_employees > 0 else 0
        
        self.total_employees_card.findChild(QLabel, None, Qt.FindChildOption.FindChildrenRecursively)[1].setText(str(total_employees))
        self.active_employees_card.findChild(QLabel, None, Qt.FindChildOption.FindChildrenRecursively)[1].setText(str(active_employees))
        self.total_salaries_card.findChild(QLabel, None, Qt.FindChildOption.FindChildrenRecursively)[1].setText(f"{total_salaries:,.2f}")
        self.avg_salary_card.findChild(QLabel, None, Qt.FindChildOption.FindChildrenRecursively)[1].setText(f"{avg_salary:,.2f}")
        
        # Update department chart
        self.dept_series.clear()
        dept_counts = {}
        for emp in employees:
            dept = emp['department']
            dept_counts[dept] = dept_counts.get(dept, 0) + 1
        
        for dept, count in dept_counts.items():
            self.dept_series.append(dept, count)
        
        # Update salary distribution chart
        self.salary_series.clear()
        salary_ranges = [
            (0, 5000, "0-5k"),
            (5000, 10000, "5k-10k"),
            (10000, 15000, "10k-15k"),
            (15000, 20000, "15k-20k"),
            (20000, float('inf'), "20k+")
        ]
        
        salary_dist = QBarSet("توزيع الرواتب")
        categories = []
        
        for start, end, label in salary_ranges:
            count = sum(1 for emp in employees if start <= float(emp['basic_salary']) < end)
            salary_dist.append(count)
            categories.append(label)
        
        self.salary_series.append(salary_dist)
        self.salary_series.attachedAxes()[1].setCategories(categories)
        
        # Update recent employees table
        self.recent_employees_table.setRowCount(0)
        sorted_employees = sorted(employees, key=lambda x: x['hire_date'], reverse=True)[:5]
        
        for i, emp in enumerate(sorted_employees):
            self.recent_employees_table.insertRow(i)
            self.recent_employees_table.setItem(i, 0, QTableWidgetItem(emp['name']))
            self.recent_employees_table.setItem(i, 1, QTableWidgetItem(emp['department']))
            self.recent_employees_table.setItem(i, 2, QTableWidgetItem(emp['hire_date']))
        
        # Update recent salaries table
        self.recent_salaries_table.setRowCount(0)
        sorted_salaries = sorted(salaries, key=lambda x: x['payment_date'], reverse=True)[:5]
        
        for i, salary in enumerate(sorted_salaries):
            self.recent_salaries_table.insertRow(i)
            emp = next((emp for emp in employees if emp['id'] == salary['employee_id']), None)
            self.recent_salaries_table.setItem(i, 0, QTableWidgetItem(emp['name'] if emp else str(salary['employee_id'])))
            self.recent_salaries_table.setItem(i, 1, QTableWidgetItem(f"{float(salary['amount']):,.2f}"))
            self.recent_salaries_table.setItem(i, 2, QTableWidgetItem(salary['payment_date']))
            self.recent_salaries_table.setItem(i, 3, QTableWidgetItem(salary['status']))
