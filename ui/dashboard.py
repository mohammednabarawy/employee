from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QSizePolicy, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis
from PyQt5.QtGui import QPainter, QColor, QPixmap, QFont, QLinearGradient, QPalette
from datetime import datetime, timedelta
from controllers import ReportController
from utils import chart_utils
from utils.company_info import CompanyInfo

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
        self.value_label = QLabel(str(value))
        self.value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {color};
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def set_value(self, value):
        """Update the displayed value"""
        self.value_label.setText(str(value))

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
        """Initialize the UI"""
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Enhanced Company info section with modern design
        self.company_info_frame = QFrame()
        self.company_info_frame.setObjectName("company_info_frame")
        self.company_info_frame.setMinimumHeight(150)
        self.company_info_frame.setStyleSheet("""
            QFrame#company_info_frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 15px;
                padding: 15px;
                margin-bottom: 10px;
            }
            QLabel#company_name_label {
                font-size: 24px;
                font-weight: bold;
                color: white;
                margin: 5px;
            }
            QLabel#register_label {
                font-size: 14px;
                color: #ecf0f1;
                margin: 2px;
            }
        """)
        
        company_info_layout = QHBoxLayout(self.company_info_frame)
        company_info_layout.setContentsMargins(20, 15, 20, 15)
        
        # Get company info
        company_name = CompanyInfo.get_company_name(self.db.db_file)
        commercial_register = CompanyInfo.get_commercial_register(self.db.db_file)
        tax_number = CompanyInfo.get_tax_number(self.db.db_file)
        social_insurance = CompanyInfo.get_social_insurance(self.db.db_file)
        
        # Logo section (left side)
        logo_container = QFrame()
        logo_container.setFixedWidth(150)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # Get and display logo
        logo_data, logo_mime = CompanyInfo.get_logo(self.db.db_file)
        if logo_data:
            logo_label = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(logo_data)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            
            # Add circular frame to logo
            logo_label.setStyleSheet("""
                background-color: white;
                border-radius: 60px;
                padding: 5px;
                margin: 5px;
            """)
            logo_layout.addWidget(logo_label)
        else:
            # Default logo if none exists
            default_logo_label = QLabel("LOGO")
            default_logo_label.setStyleSheet("""
                background-color: white;
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                border-radius: 60px;
                padding: 40px;
                margin: 5px;
            """)
            default_logo_label.setFixedSize(120, 120)
            default_logo_label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(default_logo_label)
        
        # Company details section (right side)
        details_container = QFrame()
        details_layout = QVBoxLayout(details_container)
        details_layout.setAlignment(Qt.AlignVCenter)
        
        # Company name with shadow effect
        if company_name:
            company_name_label = QLabel(company_name)
            company_name_label.setObjectName("company_name_label")
            company_name_label.setAlignment(Qt.AlignRight)
            details_layout.addWidget(company_name_label)
            
            # Company details in a grid layout
            details_grid = QFrame()
            details_grid_layout = QVBoxLayout(details_grid)
            details_grid_layout.setSpacing(5)
            details_grid_layout.setContentsMargins(0, 5, 0, 0)
            
            # Commercial register
            if commercial_register:
                register_label = QLabel(f"رقم السجل التجاري: {commercial_register}")
                register_label.setObjectName("register_label")
                register_label.setAlignment(Qt.AlignRight)
                details_grid_layout.addWidget(register_label)
            
            # Tax number
            if tax_number:
                tax_label = QLabel(f"الرقم الضريبي: {tax_number}")
                tax_label.setObjectName("register_label")
                tax_label.setAlignment(Qt.AlignRight)
                details_grid_layout.addWidget(tax_label)
            
            # Social insurance
            if social_insurance:
                insurance_label = QLabel(f"رقم التأمينات الاجتماعية: {social_insurance}")
                insurance_label.setObjectName("register_label")
                insurance_label.setAlignment(Qt.AlignRight)
                details_grid_layout.addWidget(insurance_label)
            
            details_layout.addWidget(details_grid)
        else:
            # Default company name if none exists
            default_name_label = QLabel("شركتك")
            default_name_label.setObjectName("company_name_label")
            default_name_label.setAlignment(Qt.AlignRight)
            details_layout.addWidget(default_name_label)
        
        # Add the logo and details sections to the company info layout
        company_info_layout.addWidget(logo_container)
        company_info_layout.addWidget(details_container, 1)  # Give the details section more space
        
        main_layout.addWidget(self.company_info_frame)
        
        # Database info section
        db_info_frame = QFrame()
        db_info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        db_info_layout = QHBoxLayout(db_info_frame)
        
        db_label = QLabel("قاعدة البيانات الحالية:")
        db_label.setStyleSheet("font-weight: bold;")
        self.db_path_label = QLabel(self.db.db_file)
        self.db_path_label.setStyleSheet("color: #3498db;")
        
        db_info_layout.addWidget(db_label)
        db_info_layout.addWidget(self.db_path_label, 1)
        
        main_layout.addWidget(db_info_frame)
        
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
            
            # Update total employees stat card
            self.total_employees_card.set_value(str(len(employees)))
            
            # Calculate active employees
            active_employees = sum(1 for emp in employees if emp.get('is_active', 1) == 1)
            self.active_employees_card.set_value(str(active_employees))
            
            # Calculate total and average salaries
            if employees:
                total_salary = sum(float(emp.get('basic_salary', 0)) for emp in employees)
                avg_salary = total_salary / len(employees) if len(employees) > 0 else 0
                self.total_salaries_card.set_value(f"{total_salary:,.2f}")
                self.avg_salary_card.set_value(f"{avg_salary:,.2f}")
            
            # Update department chart
            if employees and hasattr(self, 'dept_series'):
                self.dept_series.clear()
                dept_counts = {}
                for emp in employees:
                    dept_name = emp.get('department_name', 'غير محدد')
                    dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1
                
                for dept, count in dept_counts.items():
                    self.dept_series.append(dept, count)
            
            # Update salary distribution chart
            if employees and hasattr(self, 'salary_series'):
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
                    count = sum(1 for emp in employees if start <= float(emp.get('basic_salary', 0)) < end)
                    salary_dist.append(count)
                    categories.append(label)
                
                self.salary_series.append(salary_dist)
                
                # Make sure we have at least one axis attached
                if self.salary_series.attachedAxes():
                    self.salary_series.attachedAxes()[1].setCategories(categories)
            
            # Only proceed if we have employees
            if employees:
                try:
                    # Get recent employees (up to 5)
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
        """Update the payroll distribution chart"""
        try:
            success, data = self.report_controller.get_payroll_distribution()
            if success:
                labels, values = data
                
                # Create chart
                chart = QChart()
                chart.setTitle("توزيع الرواتب حسب الأقسام")
                chart.setAnimationOptions(QChart.SeriesAnimations)
                
                # Create pie series
                series = QPieSeries()
                
                # Add data to series
                for i, label in enumerate(labels):
                    series.append(f"{label} ({values[i]:,.2f})", values[i])
                
                # Make first slice exploded
                if series.count() > 0:
                    slice = series.slices()[0]
                    slice.setExploded(True)
                    slice.setLabelVisible(True)
                
                chart.addSeries(series)
                chart.legend().setVisible(True)
                chart.legend().setAlignment(Qt.AlignBottom)
                
                # Set chart to chart view
                self.payroll_chart.setChart(chart)
                
        except Exception as e:
            print(f"Error updating payroll chart: {str(e)}")

    def update_attendance_chart(self):
        """Update the attendance chart"""
        try:
            # Get attendance data for the last 7 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            # Create dummy data since get_attendance_summary doesn't exist
            attendance_data = []
            current_date = start_date
            while current_date <= end_date:
                # Generate random data for demonstration
                present = int(30 * 0.7)  # 70% present
                absent = 30 - present
                attendance_data.append((current_date, present, absent))
                current_date += timedelta(days=1)
            
            # Create bar chart
            attendance_chart = QChart()
            attendance_chart.setTitle("الحضور والغياب (آخر 7 أيام)")
            attendance_chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            bar_series = QBarSeries()
            
            # Create bar sets for present and absent
            present_set = QBarSet("حاضر")
            absent_set = QBarSet("غائب")
            
            # Set colors
            present_set.setColor(QColor("#2ecc71"))
            absent_set.setColor(QColor("#e74c3c"))
            
            # Add data to sets
            categories = []
            for date, present, absent in attendance_data:
                categories.append(date.strftime("%m/%d"))
                present_set.append(present)
                absent_set.append(absent)
            
            # Add sets to series
            bar_series.append(present_set)
            bar_series.append(absent_set)
            
            # Add series to chart
            attendance_chart.addSeries(bar_series)
            
            # Create axes
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            attendance_chart.addAxis(axis_x, Qt.AlignBottom)
            bar_series.attachAxis(axis_x)
            
            axis_y = QValueAxis()
            attendance_chart.addAxis(axis_y, Qt.AlignLeft)
            bar_series.attachAxis(axis_y)
            
            # Simply update the existing chart view instead of replacing it
            self.attendance_chart.setChart(attendance_chart)
        
        except Exception as e:
            print(f"Error updating attendance chart: {str(e)}")

    def update_db_info(self, db_file):
        """Update the database info displayed in the dashboard"""
        self.db_path_label.setText(db_file)
        
        # Refresh company info
        self.refresh_company_info(db_file)
    
    def refresh_company_info(self, db_file):
        """Refresh company information based on the current database"""
        # Remove old company info frame if it exists
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item.widget() and isinstance(item.widget(), QFrame):
                if item.widget().objectName() == "company_info_frame":
                    item.widget().deleteLater()
                    break
        
        # Create new company info frame
        company_info_frame = QFrame()
        company_info_frame.setObjectName("company_info_frame")
        company_info_frame.setMinimumHeight(150)
        company_info_frame.setStyleSheet("""
            QFrame#company_info_frame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 15px;
                padding: 15px;
                margin-bottom: 10px;
            }
            QLabel#company_name_label {
                font-size: 24px;
                font-weight: bold;
                color: white;
                margin: 5px;
            }
            QLabel#register_label {
                font-size: 14px;
                color: #ecf0f1;
                margin: 2px;
            }
        """)
        
        company_info_layout = QHBoxLayout(company_info_frame)
        company_info_layout.setContentsMargins(20, 15, 20, 15)
        
        # Get company info
        company_name = CompanyInfo.get_company_name(db_file)
        commercial_register = CompanyInfo.get_commercial_register(db_file)
        tax_number = CompanyInfo.get_tax_number(db_file)
        social_insurance = CompanyInfo.get_social_insurance(db_file)
        
        # Logo section (left side)
        logo_container = QFrame()
        logo_container.setFixedWidth(150)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)
        
        # Get and display logo
        logo_data, logo_mime = CompanyInfo.get_logo(db_file)
        if logo_data:
            logo_label = QLabel()
            pixmap = QPixmap()
            pixmap.loadFromData(logo_data)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            
            # Add circular frame to logo
            logo_label.setStyleSheet("""
                background-color: white;
                border-radius: 60px;
                padding: 5px;
                margin: 5px;
            """)
            logo_layout.addWidget(logo_label)
        else:
            # Default logo if none exists
            default_logo_label = QLabel("LOGO")
            default_logo_label.setStyleSheet("""
                background-color: white;
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                border-radius: 60px;
                padding: 40px;
                margin: 5px;
            """)
            default_logo_label.setFixedSize(120, 120)
            default_logo_label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(default_logo_label)
        
        # Company details section (right side)
        details_container = QFrame()
        details_layout = QVBoxLayout(details_container)
        details_layout.setAlignment(Qt.AlignVCenter)
        
        # Company name with shadow effect
        if company_name:
            company_name_label = QLabel(company_name)
            company_name_label.setObjectName("company_name_label")
            company_name_label.setAlignment(Qt.AlignRight)
            details_layout.addWidget(company_name_label)
            
            # Company details in a grid layout
            details_grid = QFrame()
            details_grid_layout = QVBoxLayout(details_grid)
            details_grid_layout.setSpacing(5)
            details_grid_layout.setContentsMargins(0, 5, 0, 0)
            
            # Commercial register
            if commercial_register:
                register_label = QLabel(f"رقم السجل التجاري: {commercial_register}")
                register_label.setObjectName("register_label")
                register_label.setAlignment(Qt.AlignRight)
                details_grid_layout.addWidget(register_label)
            
            # Tax number
            if tax_number:
                tax_label = QLabel(f"الرقم الضريبي: {tax_number}")
                tax_label.setObjectName("register_label")
                tax_label.setAlignment(Qt.AlignRight)
                details_grid_layout.addWidget(tax_label)
            
            # Social insurance
            if social_insurance:
                insurance_label = QLabel(f"رقم التأمينات الاجتماعية: {social_insurance}")
                insurance_label.setObjectName("register_label")
                insurance_label.setAlignment(Qt.AlignRight)
                details_grid_layout.addWidget(insurance_label)
            
            details_layout.addWidget(details_grid)
        else:
            # Default company name if none exists
            default_name_label = QLabel("شركتك")
            default_name_label.setObjectName("company_name_label")
            default_name_label.setAlignment(Qt.AlignRight)
            details_layout.addWidget(default_name_label)
        
        # Add the logo and details sections to the company info layout
        company_info_layout.addWidget(logo_container)
        company_info_layout.addWidget(details_container, 1)  # Give the details section more space
        
        # Insert at the top of the layout
        self.layout().insertWidget(0, company_info_frame)
