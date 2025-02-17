from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QTableWidget,
                             QTableWidgetItem, QDateEdit, QFileDialog,
                             QMessageBox)
from PyQt5.QtCore import Qt, QDate
import pandas as pd

class ReportsForm(QWidget):
    def __init__(self, employee_controller, salary_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.salary_controller = salary_controller
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Reports")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Report type selector
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Employee List",
            "Salary Report",
            "Attendance Summary",
            "Department Summary"
        ])
        self.report_type_combo.currentTextChanged.connect(self.report_type_changed)
        header_layout.addWidget(QLabel("Report Type:"))
        header_layout.addWidget(self.report_type_combo)
        
        # Date range
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        
        header_layout.addWidget(QLabel("From:"))
        header_layout.addWidget(self.start_date)
        header_layout.addWidget(QLabel("To:"))
        header_layout.addWidget(self.end_date)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generate_report)
        header_layout.addWidget(self.generate_btn)
        
        # Export button
        self.export_btn = QPushButton("Export to Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # Report table
        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.report_table)
    
    def report_type_changed(self, report_type):
        """Handle report type change."""
        # Update table headers and content based on report type
        if report_type == "Employee List":
            self.report_table.setColumnCount(7)
            self.report_table.setHorizontalHeaderLabels([
                "ID", "Name", "Department", "Position",
                "Phone", "Email", "Hire Date"
            ])
        elif report_type == "Salary Report":
            self.report_table.setColumnCount(6)
            self.report_table.setHorizontalHeaderLabels([
                "ID", "Name", "Department", "Salary Type",
                "Basic Salary", "Currency"
            ])
        elif report_type == "Attendance Summary":
            self.report_table.setColumnCount(5)
            self.report_table.setHorizontalHeaderLabels([
                "ID", "Name", "Present Days", "Absent Days",
                "Late Days"
            ])
        elif report_type == "Department Summary":
            self.report_table.setColumnCount(4)
            self.report_table.setHorizontalHeaderLabels([
                "Department", "Employee Count", "Total Salary",
                "Average Salary"
            ])
    
    def generate_report(self):
        """Generate the selected report."""
        report_type = self.report_type_combo.currentText()
        
        if report_type == "Employee List":
            success, employees = self.employee_controller.get_all_employees()
            if success:
                self.report_table.setRowCount(len(employees))
                for i, emp in enumerate(employees):
                    self.report_table.setItem(i, 0, QTableWidgetItem(str(emp['id'])))
                    self.report_table.setItem(i, 1, QTableWidgetItem(emp['name']))
                    self.report_table.setItem(i, 2, QTableWidgetItem(emp['department']))
                    self.report_table.setItem(i, 3, QTableWidgetItem(emp['position']))
                    self.report_table.setItem(i, 4, QTableWidgetItem(emp['phone']))
                    self.report_table.setItem(i, 5, QTableWidgetItem(emp['email']))
                    self.report_table.setItem(i, 6, QTableWidgetItem(emp['hire_date']))
        
        # TODO: Implement other report types
    
    def export_to_excel(self):
        """Export the current report to Excel."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            "",
            "Excel Files (*.xlsx)"
        )
        
        if file_name:
            try:
                # Convert table data to pandas DataFrame
                headers = []
                for i in range(self.report_table.columnCount()):
                    headers.append(self.report_table.horizontalHeaderItem(i).text())
                
                data = []
                for row in range(self.report_table.rowCount()):
                    row_data = []
                    for col in range(self.report_table.columnCount()):
                        item = self.report_table.item(row, col)
                        row_data.append(item.text() if item else '')
                    data.append(row_data)
                
                df = pd.DataFrame(data, columns=headers)
                df.to_excel(file_name, index=False)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Report exported successfully to {file_name}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to export report: {str(e)}"
                )
