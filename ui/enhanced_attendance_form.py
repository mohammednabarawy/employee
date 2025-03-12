from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QPushButton, QCheckBox, QScrollArea,
                           QGroupBox, QMessageBox, QFrame)
from PyQt5.QtCore import Qt, QDate
from datetime import datetime, timedelta
import calendar

class EnhancedAttendanceForm(QWidget):
    def __init__(self, attendance_controller, employee_controller):
        super().__init__()
        self.attendance_controller = attendance_controller
        self.employee_controller = employee_controller
        self.selected_employee_id = None
        self.checkboxes = []  # Store checkboxes for easy access
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Employee selection
        employee_layout = QHBoxLayout()
        employee_label = QLabel("الموظف:")
        self.employee_combo = QComboBox()
        employee_layout.addWidget(self.employee_combo)
        employee_layout.addWidget(employee_label)
        layout.addLayout(employee_layout)
        
        # Month selection
        month_layout = QHBoxLayout()
        month_label = QLabel("الشهر:")
        self.month_combo = QComboBox()
        
        # Add Arabic month names
        arabic_months = [
            "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ]
        
        current_month = datetime.now().month
        for i, month in enumerate(arabic_months, 1):
            self.month_combo.addItem(month, i)
            
        # Set current month
        self.month_combo.setCurrentIndex(current_month - 1)
        
        month_layout.addWidget(self.month_combo)
        month_layout.addWidget(month_label)
        layout.addLayout(month_layout)
        
        # Attendance group
        attendance_group = QGroupBox("الحضور")
        attendance_layout = QVBoxLayout()
        
        # Add buttons layout
        buttons_layout = QHBoxLayout()
        
        # Check All button
        self.check_all_btn = QPushButton("تحديد الكل")
        self.check_all_btn.clicked.connect(self.check_all)
        buttons_layout.addWidget(self.check_all_btn)
        
        # Uncheck All button
        self.uncheck_all_btn = QPushButton("إلغاء تحديد الكل")
        self.uncheck_all_btn.clicked.connect(self.uncheck_all)
        buttons_layout.addWidget(self.uncheck_all_btn)
        
        attendance_layout.addLayout(buttons_layout)
        
        # Create scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.checkboxes_layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        attendance_layout.addWidget(scroll)
        
        attendance_group.setLayout(attendance_layout)
        layout.addWidget(attendance_group)
        
        # Save button
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_attendance)
        layout.addWidget(self.save_btn)
        
        self.setLayout(layout)
        
        # Connect signals
        self.employee_combo.currentIndexChanged.connect(self.employee_selected)
        self.month_combo.currentIndexChanged.connect(self.month_selected)
        
        # Populate the employee combo box
        self.populate_employee_combo()
        
    def populate_employee_combo(self):
        """Populate the employee combo box with all employees"""
        employees = self.employee_controller.get_all_employees()
        self.employee_combo.clear()
        
        if employees:
            for employee in employees:
                self.employee_combo.addItem(
                    f"{employee['name']} ({employee['id']})", 
                    employee['id']
                )
            # Set the first employee as selected
            self.selected_employee_id = self.employee_combo.currentData()
            self.update_attendance()
        else:
            QMessageBox.warning(self, "خطأ", "فشل في تحميل قائمة الموظفين")
            
    def employee_selected(self):
        """Handle employee selection change"""
        self.selected_employee_id = self.employee_combo.currentData()
        if self.selected_employee_id:
            self.update_attendance()
        else:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار موظف")
            
    def month_selected(self):
        """Handle month selection change"""
        if self.selected_employee_id:
            self.update_attendance()
            
    def update_attendance(self):
        """Update attendance checkboxes based on selected employee and month"""
        if not self.selected_employee_id:
            return
            
        # Clear existing checkboxes
        while self.checkboxes_layout.count():
            child = self.checkboxes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.checkboxes.clear()
        
        # Get selected month
        month = self.month_combo.currentData()
        year = datetime.now().year
        
        # Get number of days in the month
        num_days = calendar.monthrange(year, month)[1]
        
        # Create checkbox for each day
        for day in range(1, num_days + 1):
            date = datetime(year, month, day)
            checkbox = QCheckBox(date.strftime("%Y-%m-%d"))
            
            # Check if employee was present on this day
            attendance = self.attendance_controller.get_attendance_status_for_date(
                self.selected_employee_id,
                date.strftime("%Y-%m-%d")
            )
            checkbox.setChecked(attendance == "present")
            
            self.checkboxes_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)
            
    def check_all(self):
        """Mark all days as present"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)
            
    def uncheck_all(self):
        """Mark all days as absent"""
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)
            
    def save_attendance(self):
        """Save attendance records for the selected employee"""
        if not self.selected_employee_id:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار موظف")
            return
            
        try:
            for checkbox in self.checkboxes:
                date = checkbox.text()
                status = "present" if checkbox.isChecked() else "absent"
                self.attendance_controller.mark_attendance_for_date(
                    self.selected_employee_id,
                    date,
                    status
                )
            QMessageBox.information(self, "نجاح", "تم حفظ سجلات الحضور بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ سجلات الحضور: {str(e)}")
