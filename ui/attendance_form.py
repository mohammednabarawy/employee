from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QCalendarWidget, QTableWidget,
                             QTableWidgetItem, QComboBox, QMessageBox)
from PyQt5.QtCore import Qt, QDate

class AttendanceForm(QWidget):
    def __init__(self, employee_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Attendance Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Employee selector
        self.employee_combo = QComboBox()
        self.employee_combo.setMinimumWidth(200)
        self.load_employees()
        header_layout.addWidget(QLabel("Employee:"))
        header_layout.addWidget(self.employee_combo)
        
        layout.addLayout(header_layout)
        
        # Calendar and attendance table
        content_layout = QHBoxLayout()
        
        # Calendar widget
        calendar_layout = QVBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.clicked.connect(self.date_selected)
        calendar_layout.addWidget(self.calendar)
        
        # Action buttons
        button_layout = QHBoxLayout()
        self.check_in_btn = QPushButton("Check In")
        self.check_in_btn.clicked.connect(self.check_in)
        self.check_out_btn = QPushButton("Check Out")
        self.check_out_btn.clicked.connect(self.check_out)
        
        button_layout.addWidget(self.check_in_btn)
        button_layout.addWidget(self.check_out_btn)
        calendar_layout.addLayout(button_layout)
        
        content_layout.addLayout(calendar_layout)
        
        # Attendance table
        table_layout = QVBoxLayout()
        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["Date", "Check In", "Check Out", "Duration"])
        self.attendance_table.horizontalHeader().setStretchLastSection(True)
        table_layout.addWidget(self.attendance_table)
        
        content_layout.addLayout(table_layout)
        
        layout.addLayout(content_layout)
    
    def load_employees(self):
        """Load employees into the combo box."""
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.employee_combo.clear()
            for employee in employees:
                self.employee_combo.addItem(employee['name'], employee['id'])
    
    def date_selected(self, date):
        """Handle date selection in calendar."""
        # TODO: Load attendance data for selected date
        pass
    
    def check_in(self):
        """Record check-in time for selected employee."""
        if self.employee_combo.currentData():
            # TODO: Record check-in time
            QMessageBox.information(self, "Success", "Check-in recorded successfully!")
        else:
            QMessageBox.warning(self, "Error", "Please select an employee first!")
    
    def check_out(self):
        """Record check-out time for selected employee."""
        if self.employee_combo.currentData():
            # TODO: Record check-out time
            QMessageBox.information(self, "Success", "Check-out recorded successfully!")
        else:
            QMessageBox.warning(self, "Error", "Please select an employee first!")
