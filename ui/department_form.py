from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QLineEdit, QTextEdit, QFormLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal

class DepartmentForm(QDialog):
    """Dialog for managing departments"""
    
    department_added = pyqtSignal(dict)
    department_updated = pyqtSignal(dict)
    department_deleted = pyqtSignal(int)
    
    def __init__(self, employee_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.current_department_id = None
        self.departments = []
        
        self.setWindowTitle("إدارة الأقسام")
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.load_departments()
        
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Form section
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم القسم")
        form_layout.addRow("اسم القسم:", self.name_edit)
        
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("اسم القسم بالعربية")
        form_layout.addRow("اسم القسم بالعربية:", self.name_ar_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("وصف القسم")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("الوصف:", self.description_edit)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("جديد")
        self.new_btn.clicked.connect(self.new_department)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_department)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.clicked.connect(self.delete_department)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.new_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        
        # Table
        self.departments_table = QTableWidget()
        self.departments_table.setColumnCount(3)
        self.departments_table.setHorizontalHeaderLabels(["الاسم", "الاسم بالعربية", "الوصف"])
        self.departments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.departments_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.departments_table.setSelectionMode(QTableWidget.SingleSelection)
        self.departments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.departments_table.clicked.connect(self.department_selected)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(QLabel("قائمة الأقسام:"))
        layout.addWidget(self.departments_table)
        
    def load_departments(self):
        """Load departments from database"""
        success, departments = self.employee_controller.get_departments()
        if success:
            self.departments = departments
            self.update_departments_table()
        else:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل الأقسام: {departments}")
    
    def update_departments_table(self):
        """Update the departments table with current data"""
        self.departments_table.setRowCount(0)
        
        for dept in self.departments:
            row = self.departments_table.rowCount()
            self.departments_table.insertRow(row)
            
            self.departments_table.setItem(row, 0, QTableWidgetItem(dept.get('name', '')))
            self.departments_table.setItem(row, 1, QTableWidgetItem(dept.get('name_ar', '')))
            self.departments_table.setItem(row, 2, QTableWidgetItem(dept.get('description', '')))
            
            # Store department ID as hidden data
            self.departments_table.item(row, 0).setData(Qt.UserRole, dept.get('id'))
    
    def department_selected(self):
        """Handle department selection from table"""
        selected_rows = self.departments_table.selectedItems()
        if selected_rows:
            # Get the department ID from the first cell of the selected row
            department_id = self.departments_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
            
            # Find the department in our list
            for dept in self.departments:
                if dept.get('id') == department_id:
                    self.current_department_id = department_id
                    self.name_edit.setText(dept.get('name', ''))
                    self.name_ar_edit.setText(dept.get('name_ar', ''))
                    self.description_edit.setText(dept.get('description', ''))
                    self.delete_btn.setEnabled(True)
                    break
    
    def new_department(self):
        """Clear form for new department"""
        self.current_department_id = None
        self.name_edit.clear()
        self.name_ar_edit.clear()
        self.description_edit.clear()
        self.delete_btn.setEnabled(False)
        self.departments_table.clearSelection()
    
    def get_form_data(self):
        """Get department data from form"""
        return {
            'name': self.name_edit.text().strip(),
            'name_ar': self.name_ar_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'is_active': 1
        }
    
    def validate_form(self):
        """Validate form data"""
        data = self.get_form_data()
        
        if not data['name']:
            QMessageBox.warning(self, "خطأ", "يجب إدخال اسم القسم")
            return False
        
        return True
    
    def save_department(self):
        """Save department data"""
        if not self.validate_form():
            return
        
        data = self.get_form_data()
        
        if self.current_department_id:  # Update existing
            success, result = self.employee_controller.update_department(self.current_department_id, data)
            if success:
                QMessageBox.information(self, "تم", "تم تحديث القسم بنجاح")
                data['id'] = self.current_department_id
                self.department_updated.emit(data)
                self.load_departments()
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحديث القسم: {result}")
        else:  # Add new
            success, result = self.employee_controller.add_department(data)
            if success:
                QMessageBox.information(self, "تم", "تم إضافة القسم بنجاح")
                data['id'] = result
                self.department_added.emit(data)
                self.load_departments()
                self.new_department()  # Clear form for next entry
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء إضافة القسم: {result}")
    
    def delete_department(self):
        """Delete the current department"""
        if not self.current_department_id:
            QMessageBox.warning(self, "خطأ", "لم يتم تحديد قسم للحذف")
            return
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            "هل أنت متأكد من حذف هذا القسم؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, result = self.employee_controller.delete_department(self.current_department_id)
            if success:
                QMessageBox.information(self, "تم", "تم حذف القسم بنجاح")
                self.department_deleted.emit(self.current_department_id)
                self.load_departments()
                self.new_department()  # Clear form
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء حذف القسم: {result}")
