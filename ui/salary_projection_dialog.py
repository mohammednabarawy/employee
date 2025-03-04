from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QComboBox, QSpinBox, QGroupBox, QFormLayout,
                             QFrame, QHeaderView, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import qtawesome as qta
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from ui.styles import Styles

class SalaryProjectionDialog(QDialog):
    """Dialog to project salary costs for budget planning"""
    
    def __init__(self, salary_controller, employee_controller, parent=None):
        super().__init__(parent)
        self.salary_controller = salary_controller
        self.employee_controller = employee_controller
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("توقعات الرواتب")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Filter controls
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Year selection
        year_layout = QHBoxLayout()
        year_icon = QLabel()
        year_icon.setPixmap(qta.icon('fa5s.calendar-alt', color='#3498db').pixmap(16, 16))
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2020, 2030)
        self.year_spin.setValue(2023)
        
        year_layout.addWidget(year_icon)
        year_layout.addWidget(QLabel("السنة:"))
        year_layout.addWidget(self.year_spin)
        
        # Department filter
        dept_layout = QHBoxLayout()
        dept_icon = QLabel()
        dept_icon.setPixmap(qta.icon('fa5s.building', color='#3498db').pixmap(16, 16))
        self.dept_combo = QComboBox()
        
        # Get departments
        success, departments = self.employee_controller.get_departments()
        if success:
            self.dept_combo.addItem("كل الأقسام", None)
            for dept in departments:
                self.dept_combo.addItem(dept['name'], dept['id'])
                
        dept_layout.addWidget(dept_icon)
        dept_layout.addWidget(QLabel("القسم:"))
        dept_layout.addWidget(self.dept_combo)
        
        # Options
        options_layout = QHBoxLayout()
        self.include_allowances = QCheckBox("تضمين البدلات")
        self.include_allowances.setChecked(True)
        self.include_deductions = QCheckBox("تضمين الخصومات")
        self.include_deductions.setChecked(True)
        
        options_layout.addWidget(self.include_allowances)
        options_layout.addWidget(self.include_deductions)
        
        # Apply button
        self.apply_button = QPushButton("حساب")
        self.apply_button.setIcon(qta.icon('fa5s.calculator', color='white'))
        self.apply_button.clicked.connect(self.calculate_projections)
        
        filter_layout.addLayout(year_layout)
        filter_layout.addLayout(dept_layout)
        filter_layout.addLayout(options_layout)
        filter_layout.addWidget(self.apply_button)
        
        layout.addWidget(filter_frame)
        
        # Summary section
        summary_frame = QFrame()
        summary_frame.setObjectName("summaryFrame")
        summary_layout = QHBoxLayout(summary_frame)
        
        # Annual total
        annual_group = QGroupBox("إجمالي الرواتب السنوي")
        annual_layout = QVBoxLayout(annual_group)
        self.annual_total_label = QLabel("0.00")
        self.annual_total_label.setObjectName("totalLabel")
        self.annual_total_label.setAlignment(Qt.AlignCenter)
        annual_layout.addWidget(self.annual_total_label)
        
        # Monthly average
        monthly_group = QGroupBox("متوسط الرواتب الشهري")
        monthly_layout = QVBoxLayout(monthly_group)
        self.monthly_avg_label = QLabel("0.00")
        self.monthly_avg_label.setObjectName("totalLabel")
        self.monthly_avg_label.setAlignment(Qt.AlignCenter)
        monthly_layout.addWidget(self.monthly_avg_label)
        
        summary_layout.addWidget(annual_group)
        summary_layout.addWidget(monthly_group)
        
        layout.addWidget(summary_frame)
        
        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(1)  # Antialiasing
        self.chart_view.setMinimumHeight(300)
        
        layout.addWidget(self.chart_view)
        
        # Department breakdown table
        dept_group = QGroupBox("توزيع الرواتب حسب الأقسام")
        dept_layout = QVBoxLayout(dept_group)
        
        self.dept_table = QTableWidget()
        self.dept_table.setColumnCount(3)
        self.dept_table.setHorizontalHeaderLabels([
            "القسم", "إجمالي الرواتب السنوي", "النسبة المئوية"
        ])
        
        self.dept_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.dept_table.setAlternatingRowColors(True)
        
        dept_layout.addWidget(self.dept_table)
        layout.addWidget(dept_group)
        
        # Monthly breakdown table
        month_group = QGroupBox("توزيع الرواتب الشهري")
        month_layout = QVBoxLayout(month_group)
        
        self.month_table = QTableWidget()
        self.month_table.setColumnCount(2)
        self.month_table.setHorizontalHeaderLabels([
            "الشهر", "إجمالي الرواتب"
        ])
        
        self.month_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.month_table.setAlternatingRowColors(True)
        
        month_layout.addWidget(self.month_table)
        layout.addWidget(month_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.print_button = QPushButton("طباعة")
        self.print_button.setIcon(qta.icon('fa5s.print', color='white'))
        self.print_button.clicked.connect(self.print_projections)
        
        self.export_button = QPushButton("تصدير")
        self.export_button.setIcon(qta.icon('fa5s.file-export', color='white'))
        self.export_button.clicked.connect(self.export_projections)
        
        self.close_button = QPushButton("إغلاق")
        self.close_button.setIcon(qta.icon('fa5s.times', color='white'))
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.print_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Initial calculation
        self.calculate_projections()
        
    def calculate_projections(self):
        """Calculate salary projections based on current settings"""
        year = self.year_spin.value()
        department_id = self.dept_combo.currentData()
        include_allowances = self.include_allowances.isChecked()
        include_deductions = self.include_deductions.isChecked()
        
        success, projections = self.salary_controller.calculate_salary_projections(
            year, include_allowances, include_deductions, department_id
        )
        
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء حساب التوقعات: {projections}")
            return
            
        # Update summary
        annual_total = projections['annual_total']
        monthly_avg = annual_total / 12
        
        self.annual_total_label.setText(f"{annual_total:,.2f}")
        self.monthly_avg_label.setText(f"{monthly_avg:,.2f}")
        
        # Update department table
        self.dept_table.setRowCount(0)
        
        for i, dept in enumerate(projections['department_totals']):
            self.dept_table.insertRow(i)
            
            # Department name
            name_item = QTableWidgetItem(dept['name'])
            name_item.setIcon(qta.icon('fa5s.building', color='#3498db'))
            
            # Total
            total = float(dept['total'])
            total_item = QTableWidgetItem(f"{total:,.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            
            # Percentage
            percentage = (total / annual_total) * 100 if annual_total > 0 else 0
            percentage_item = QTableWidgetItem(f"{percentage:.2f}%")
            percentage_item.setTextAlignment(Qt.AlignCenter)
            
            # Add items to row
            self.dept_table.setItem(i, 0, name_item)
            self.dept_table.setItem(i, 1, total_item)
            self.dept_table.setItem(i, 2, percentage_item)
            
        self.dept_table.resizeColumnsToContents()
        
        # Update monthly table
        self.month_table.setRowCount(0)
        
        month_names = [
            "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ]
        
        for i, month_proj in enumerate(projections['monthly_projections']):
            self.month_table.insertRow(i)
            
            # Month name
            month_item = QTableWidgetItem(month_names[i])
            month_item.setIcon(qta.icon('fa5s.calendar-day', color='#3498db'))
            
            # Total
            total = float(month_proj['total'])
            total_item = QTableWidgetItem(f"{total:,.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            
            # Add items to row
            self.month_table.setItem(i, 0, month_item)
            self.month_table.setItem(i, 1, total_item)
            
        self.month_table.resizeColumnsToContents()
        
        # Create chart
        self.create_chart(projections['monthly_projections'], month_names)
        
    def create_chart(self, monthly_projections, month_names):
        """Create bar chart for monthly projections"""
        # Create chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("توقعات الرواتب الشهرية")
        chart.setTheme(QChart.ChartThemeLight)
        
        # Create bar series
        series = QBarSeries()
        
        # Create bar set for monthly totals
        monthly_set = QBarSet("إجمالي الرواتب")
        monthly_set.setColor(QColor('#3498db'))
        
        # Add data to bar set
        for month_proj in monthly_projections:
            monthly_set.append(float(month_proj['total']))
            
        series.append(monthly_set)
        chart.addSeries(series)
        
        # Create axes
        axis_x = QBarCategoryAxis()
        axis_x.append(month_names)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Set chart to view
        self.chart_view.setChart(chart)
        
    def print_projections(self):
        """Print projections report"""
        # Implementation for printing would go here
        QMessageBox.information(self, "طباعة", "جاري إعداد التقرير للطباعة...")
        
    def export_projections(self):
        """Export projections to Excel or CSV"""
        # Implementation for exporting would go here
        QMessageBox.information(self, "تصدير", "جاري تصدير البيانات...")
