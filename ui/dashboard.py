from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet
from PyQt5.QtGui import QPainter

class StatCard(QFrame):
    def __init__(self, title, value, icon=None, color="#3498db"):
        super().__init__()
        self.setObjectName("card")
        self.setMinimumSize(200, 120)
        
        layout = QVBoxLayout(self)
        
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

class Dashboard(QWidget):
    def __init__(self, controllers):
        super().__init__()
        self.controllers = controllers
        self.init_ui()
        
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Add statistics cards
        stats_layout = QHBoxLayout()
        
        # Total Employees
        total_employees = StatCard(
            "Total Employees",
            "156",
            color="#3498db"
        )
        
        # Present Today
        present_today = StatCard(
            "Present Today",
            "143",
            color="#2ecc71"
        )
        
        # On Leave
        on_leave = StatCard(
            "On Leave",
            "13",
            color="#e74c3c"
        )
        
        # Total Payroll
        total_payroll = StatCard(
            "Monthly Payroll",
            "$125,430",
            color="#f1c40f"
        )
        
        stats_layout.addWidget(total_employees)
        stats_layout.addWidget(present_today)
        stats_layout.addWidget(on_leave)
        stats_layout.addWidget(total_payroll)
        
        content_layout.addLayout(stats_layout)
        
        # Add charts section
        charts_layout = QHBoxLayout()
        
        # Department Distribution Chart
        dept_chart = self.create_department_chart()
        dept_chart.setMinimumSize(400, 300)
        
        # Salary Distribution Chart
        salary_chart = self.create_salary_chart()
        salary_chart.setMinimumSize(400, 300)
        
        charts_layout.addWidget(dept_chart)
        charts_layout.addWidget(salary_chart)
        
        content_layout.addLayout(charts_layout)
        
        # Recent Activities
        activities_frame = QFrame()
        activities_frame.setObjectName("card")
        activities_layout = QVBoxLayout(activities_frame)
        
        # Title
        activities_title = QLabel("Recent Activities")
        activities_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        activities_layout.addWidget(activities_title)
        
        # Activity items
        activities = [
            ("John Doe", "Marked attendance", "2 minutes ago"),
            ("Jane Smith", "Requested leave", "1 hour ago"),
            ("Mike Johnson", "Updated profile", "2 hours ago"),
            ("Sarah Williams", "Submitted timesheet", "3 hours ago")
        ]
        
        for name, action, time in activities:
            activity_widget = QWidget()
            activity_layout = QHBoxLayout(activity_widget)
            
            name_label = QLabel(name)
            name_label.setStyleSheet("font-weight: bold;")
            
            action_label = QLabel(action)
            
            time_label = QLabel(time)
            time_label.setStyleSheet("color: #7f8c8d;")
            
            activity_layout.addWidget(name_label)
            activity_layout.addWidget(action_label)
            activity_layout.addStretch()
            activity_layout.addWidget(time_label)
            
            activities_layout.addWidget(activity_widget)
        
        content_layout.addWidget(activities_frame)
        content_layout.addStretch()
        
        # Set scroll area widget
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    
    def create_department_chart(self):
        # Create chart
        chart = QChart()
        chart.setTitle("Employee Distribution by Department")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create pie series
        series = QPieSeries()
        series.append("IT", 35)
        series.append("HR", 15)
        series.append("Finance", 20)
        series.append("Sales", 30)
        series.append("Operations", 25)
        
        # Add series to chart
        chart.addSeries(series)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
    
    def create_salary_chart(self):
        # Create chart
        chart = QChart()
        chart.setTitle("Salary Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Create bar series
        series = QBarSeries()
        
        # Create bar set
        salary_set = QBarSet("Employees")
        salary_set.append([10, 15, 20, 8, 5])  # Number of employees in each range
        series.append(salary_set)
        
        # Add series to chart
        chart.addSeries(series)
        
        # Create chart view
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
