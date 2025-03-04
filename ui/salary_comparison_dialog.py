from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QPushButton, 
                             QComboBox, QGroupBox, QFormLayout, QFrame,
                             QHeaderView, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import qtawesome as qta
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from ui.styles import Styles

class SalaryComparisonDialog(QDialog):
    """Dialog to compare salaries across departments or positions"""
    
    def __init__(self, payroll_controller, employee_controller, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.employee_controller = employee_controller
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("مقارنة الرواتب")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Filter controls
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        
        # Comparison type
        type_layout = QHBoxLayout()
        type_icon = QLabel()
        type_icon.setPixmap(qta.icon('fa5s.chart-bar', color='#3498db').pixmap(16, 16))
        self.type_combo = QComboBox()
        self.type_combo.addItem("حسب القسم", "department")
        self.type_combo.addItem("حسب المسمى الوظيفي", "position")
        
        type_layout.addWidget(type_icon)
        type_layout.addWidget(QLabel("نوع المقارنة:"))
        type_layout.addWidget(self.type_combo)
        
        # Department filter (for position comparison)
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
        self.show_names = QCheckBox("عرض الأسماء")
        self.show_names.setChecked(True)
        self.show_chart = QCheckBox("عرض الرسم البياني")
        self.show_chart.setChecked(True)
        
        options_layout.addWidget(self.show_names)
        options_layout.addWidget(self.show_chart)
        
        # Apply button
        self.apply_button = QPushButton("تطبيق")
        self.apply_button.setIcon(qta.icon('fa5s.filter', color='white'))
        self.apply_button.clicked.connect(self.apply_filter)
        
        filter_layout.addLayout(type_layout)
        filter_layout.addLayout(dept_layout)
        filter_layout.addLayout(options_layout)
        filter_layout.addWidget(self.apply_button)
        
        layout.addWidget(filter_frame)
        
        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(1)  # Antialiasing
        self.chart_view.setMinimumHeight(300)
        
        layout.addWidget(self.chart_view)
        
        # Comparison table
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(5)
        self.comparison_table.setHorizontalHeaderLabels([
            "القسم/المسمى", "عدد الموظفين", "متوسط الراتب", "أقل راتب", "أعلى راتب"
        ])
        
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comparison_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.comparison_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.print_button = QPushButton("طباعة")
        self.print_button.setIcon(qta.icon('fa5s.print', color='white'))
        self.print_button.clicked.connect(self.print_comparison)
        
        self.export_button = QPushButton("تصدير")
        self.export_button.setIcon(qta.icon('fa5s.file-export', color='white'))
        self.export_button.clicked.connect(self.export_comparison)
        
        self.close_button = QPushButton("إغلاق")
        self.close_button.setIcon(qta.icon('fa5s.times', color='white'))
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.print_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.type_combo.currentIndexChanged.connect(self.toggle_department_filter)
        
        # Initial load
        self.toggle_department_filter()
        self.apply_filter()
        
    def toggle_department_filter(self):
        """Show/hide department filter based on comparison type"""
        comparison_type = self.type_combo.currentData()
        self.dept_combo.setEnabled(comparison_type == "position")
        
    def apply_filter(self):
        """Apply filters and load comparison data"""
        comparison_type = self.type_combo.currentData()
        department_id = self.dept_combo.currentData() if self.dept_combo.isEnabled() else None
        
        # Get comparison data
        if comparison_type == "department":
            self.load_department_comparison()
        else:
            self.load_position_comparison(department_id)
            
    def load_department_comparison(self):
        """Load salary comparison by department"""
        try:
            conn = self.employee_controller.db.get_connection()
            cursor = conn.cursor()
            
            # Get salary data by department
            cursor.execute("""
                SELECT 
                    d.id,
                    d.name,
                    COUNT(e.id) as employee_count,
                    AVG(e.basic_salary) as avg_salary,
                    MIN(e.basic_salary) as min_salary,
                    MAX(e.basic_salary) as max_salary
                FROM departments d
                LEFT JOIN employees e ON d.id = e.department_id
                WHERE d.is_active = 1 AND e.is_active = 1
                GROUP BY d.id, d.name
                ORDER BY avg_salary DESC
            """)
            
            columns = [column[0] for column in cursor.description]
            departments = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Update table
            self.comparison_table.setRowCount(0)
            
            # Create chart
            if self.show_chart.isChecked():
                self.create_chart(departments, "department")
            else:
                self.chart_view.setChart(QChart())
                
            # Populate table
            for i, dept in enumerate(departments):
                self.comparison_table.insertRow(i)
                
                # Department name
                name_item = QTableWidgetItem(dept['name'])
                name_item.setIcon(qta.icon('fa5s.building', color='#3498db'))
                
                # Employee count
                count_item = QTableWidgetItem(str(dept['employee_count']))
                count_item.setTextAlignment(Qt.AlignCenter)
                
                # Average salary
                avg_salary = float(dept['avg_salary']) if dept['avg_salary'] else 0
                avg_item = QTableWidgetItem(f"{avg_salary:,.2f}")
                avg_item.setTextAlignment(Qt.AlignCenter)
                
                # Min salary
                min_salary = float(dept['min_salary']) if dept['min_salary'] else 0
                min_item = QTableWidgetItem(f"{min_salary:,.2f}")
                min_item.setTextAlignment(Qt.AlignCenter)
                
                # Max salary
                max_salary = float(dept['max_salary']) if dept['max_salary'] else 0
                max_item = QTableWidgetItem(f"{max_salary:,.2f}")
                max_item.setTextAlignment(Qt.AlignCenter)
                
                # Add items to row
                self.comparison_table.setItem(i, 0, name_item)
                self.comparison_table.setItem(i, 1, count_item)
                self.comparison_table.setItem(i, 2, avg_item)
                self.comparison_table.setItem(i, 3, min_item)
                self.comparison_table.setItem(i, 4, max_item)
                
            self.comparison_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل بيانات المقارنة: {str(e)}")
        finally:
            conn.close()
            
    def load_position_comparison(self, department_id=None):
        """Load salary comparison by position"""
        try:
            conn = self.employee_controller.db.get_connection()
            cursor = conn.cursor()
            
            # Get salary data by position
            query = """
                SELECT 
                    p.id,
                    p.name,
                    COUNT(e.id) as employee_count,
                    AVG(e.basic_salary) as avg_salary,
                    MIN(e.basic_salary) as min_salary,
                    MAX(e.basic_salary) as max_salary
                FROM positions p
                LEFT JOIN employees e ON p.id = e.position_id
                WHERE e.is_active = 1
            """
            
            params = []
            
            if department_id:
                query += " AND e.department_id = ?"
                params.append(department_id)
                
            query += """
                GROUP BY p.id, p.name
                ORDER BY avg_salary DESC
            """
            
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            positions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Update table
            self.comparison_table.setRowCount(0)
            
            # Create chart
            if self.show_chart.isChecked():
                self.create_chart(positions, "position")
            else:
                self.chart_view.setChart(QChart())
                
            # Populate table
            for i, pos in enumerate(positions):
                self.comparison_table.insertRow(i)
                
                # Position name
                name_item = QTableWidgetItem(pos['name'])
                name_item.setIcon(qta.icon('fa5s.user-tie', color='#3498db'))
                
                # Employee count
                count_item = QTableWidgetItem(str(pos['employee_count']))
                count_item.setTextAlignment(Qt.AlignCenter)
                
                # Average salary
                avg_salary = float(pos['avg_salary']) if pos['avg_salary'] else 0
                avg_item = QTableWidgetItem(f"{avg_salary:,.2f}")
                avg_item.setTextAlignment(Qt.AlignCenter)
                
                # Min salary
                min_salary = float(pos['min_salary']) if pos['min_salary'] else 0
                min_item = QTableWidgetItem(f"{min_salary:,.2f}")
                min_item.setTextAlignment(Qt.AlignCenter)
                
                # Max salary
                max_salary = float(pos['max_salary']) if pos['max_salary'] else 0
                max_item = QTableWidgetItem(f"{max_salary:,.2f}")
                max_item.setTextAlignment(Qt.AlignCenter)
                
                # Add items to row
                self.comparison_table.setItem(i, 0, name_item)
                self.comparison_table.setItem(i, 1, count_item)
                self.comparison_table.setItem(i, 2, avg_item)
                self.comparison_table.setItem(i, 3, min_item)
                self.comparison_table.setItem(i, 4, max_item)
                
            self.comparison_table.resizeColumnsToContents()
            
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل بيانات المقارنة: {str(e)}")
        finally:
            conn.close()
            
    def create_chart(self, data, data_type):
        """Create bar chart for comparison"""
        # Create chart
        chart = QChart()
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setTitle("مقارنة متوسط الرواتب")
        chart.setTheme(QChart.ChartThemeLight)
        
        # Create bar series
        series = QBarSeries()
        
        # Create bar set for average salaries
        avg_set = QBarSet("متوسط الراتب")
        avg_set.setColor(QColor('#3498db'))
        
        # Add data to bar set
        categories = []
        for item in data:
            avg_salary = float(item['avg_salary']) if item['avg_salary'] else 0
            avg_set.append(avg_salary)
            categories.append(item['name'])
            
        series.append(avg_set)
        chart.addSeries(series)
        
        # Create axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        # Set chart to view
        self.chart_view.setChart(chart)
        
    def print_comparison(self):
        """Print comparison report"""
        # Implementation for printing would go here
        QMessageBox.information(self, "طباعة", "جاري إعداد التقرير للطباعة...")
        
    def export_comparison(self):
        """Export comparison to Excel or CSV"""
        # Implementation for exporting would go here
        QMessageBox.information(self, "تصدير", "جاري تصدير البيانات...")
