from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QMessageBox, QLineEdit, QTextEdit, QFormLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal

class PositionForm(QDialog):
    """Dialog for managing positions"""
    
    position_added = pyqtSignal(dict)
    position_updated = pyqtSignal(dict)
    position_deleted = pyqtSignal(int)
    
    def __init__(self, employee_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.current_position_id = None
        self.positions = []
        self.departments = []
        
        self.setWindowTitle("إدارة المسميات الوظيفية")
        self.setMinimumSize(700, 500)
        
        self.setup_ui()
        self.load_departments()
        self.load_positions()
        
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Form section
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("اسم المسمى الوظيفي")
        form_layout.addRow("اسم المسمى الوظيفي:", self.name_edit)
        
        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setPlaceholderText("اسم المسمى الوظيفي بالعربية")
        form_layout.addRow("اسم المسمى الوظيفي بالعربية:", self.name_ar_edit)
        
        self.department_combo = QComboBox()
        self.department_combo.setPlaceholderText("اختر القسم")
        form_layout.addRow("القسم:", self.department_combo)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("وصف المسمى الوظيفي")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("الوصف:", self.description_edit)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("جديد")
        self.new_btn.clicked.connect(self.new_position)
        
        self.save_btn = QPushButton("حفظ")
        self.save_btn.clicked.connect(self.save_position)
        
        self.delete_btn = QPushButton("حذف")
        self.delete_btn.clicked.connect(self.delete_position)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.new_btn)
        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        
        # Table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(4)
        self.positions_table.setHorizontalHeaderLabels(["الاسم", "الاسم بالعربية", "القسم", "الوصف"])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.positions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.positions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.positions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.positions_table.clicked.connect(self.position_selected)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addLayout(buttons_layout)
        layout.addWidget(QLabel("قائمة المسميات الوظيفية:"))
        layout.addWidget(self.positions_table)
        
    def load_departments(self):
        """Load departments for the dropdown"""
        success, departments = self.employee_controller.get_departments()
        if success:
            self.departments = departments
            self.department_combo.clear()
            self.department_combo.addItem("", None)  # Empty option
            
            for dept in departments:
                self.department_combo.addItem(dept.get('name', ''), dept.get('id'))
        else:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل الأقسام: {departments}")
    
    def load_positions(self):
        """Load positions from database"""
        success, positions = self.employee_controller.get_positions()
        if success:
            self.positions = positions
            self.update_positions_table()
        else:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل المسميات الوظيفية: {positions}")
    
    def update_positions_table(self):
        """Update the positions table with current data"""
        self.positions_table.setRowCount(0)
        
        for pos in self.positions:
            row = self.positions_table.rowCount()
            self.positions_table.insertRow(row)
            
            # Find department name
            department_name = ""
            department_id = pos.get('department_id')
            if department_id:
                for dept in self.departments:
                    if dept.get('id') == department_id:
                        department_name = dept.get('name', '')
                        break
            
            self.positions_table.setItem(row, 0, QTableWidgetItem(pos.get('name', '')))
            self.positions_table.setItem(row, 1, QTableWidgetItem(pos.get('name_ar', '')))
            self.positions_table.setItem(row, 2, QTableWidgetItem(department_name))
            self.positions_table.setItem(row, 3, QTableWidgetItem(pos.get('description', '')))
            
            # Store position ID as hidden data
            self.positions_table.item(row, 0).setData(Qt.UserRole, pos.get('id'))
    
    def position_selected(self):
        """Handle position selection from table"""
        selected_rows = self.positions_table.selectedItems()
        if selected_rows:
            # Get the position ID from the first cell of the selected row
            position_id = self.positions_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
            
            # Find the position in our list
            for pos in self.positions:
                if pos.get('id') == position_id:
                    self.current_position_id = position_id
                    self.name_edit.setText(pos.get('name', ''))
                    self.name_ar_edit.setText(pos.get('name_ar', ''))
                    self.description_edit.setText(pos.get('description', ''))
                    
                    # Set department
                    department_id = pos.get('department_id')
                    if department_id:
                        index = self.department_combo.findData(department_id)
                        if index >= 0:
                            self.department_combo.setCurrentIndex(index)
                    else:
                        self.department_combo.setCurrentIndex(0)
                    
                    self.delete_btn.setEnabled(True)
                    break
    
    def new_position(self):
        """Clear form for new position"""
        self.current_position_id = None
        self.name_edit.clear()
        self.name_ar_edit.clear()
        self.description_edit.clear()
        self.department_combo.setCurrentIndex(0)
        self.delete_btn.setEnabled(False)
        self.positions_table.clearSelection()
    
    def get_form_data(self):
        """Get position data from form"""
        return {
            'name': self.name_edit.text().strip(),
            'name_ar': self.name_ar_edit.text().strip(),
            'department_id': self.department_combo.currentData(),
            'description': self.description_edit.toPlainText().strip(),
            'is_active': 1
        }
    
    def validate_form(self):
        """Validate form data"""
        data = self.get_form_data()
        
        if not data['name']:
            QMessageBox.warning(self, "خطأ", "يجب إدخال اسم المسمى الوظيفي")
            return False
        
        return True
    
    def save_position(self):
        """Save position data"""
        if not self.validate_form():
            return
        
        data = self.get_form_data()
        
        if self.current_position_id:  # Update existing
            success, result = self.employee_controller.update_position(self.current_position_id, data)
            if success:
                QMessageBox.information(self, "تم", "تم تحديث المسمى الوظيفي بنجاح")
                data['id'] = self.current_position_id
                self.position_updated.emit(data)
                self.load_positions()
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحديث المسمى الوظيفي: {result}")
        else:  # Add new
            success, result = self.employee_controller.add_position(data)
            if success:
                QMessageBox.information(self, "تم", "تم إضافة المسمى الوظيفي بنجاح")
                data['id'] = result
                self.position_added.emit(data)
                self.load_positions()
                self.new_position()  # Clear form for next entry
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء إضافة المسمى الوظيفي: {result}")
    
    def delete_position(self):
        """Delete the current position"""
        if not self.current_position_id:
            QMessageBox.warning(self, "خطأ", "لم يتم تحديد مسمى وظيفي للحذف")
            return
        
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف", 
            "هل أنت متأكد من حذف هذا المسمى الوظيفي؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, result = self.employee_controller.delete_position(self.current_position_id)
            if success:
                QMessageBox.information(self, "تم", "تم حذف المسمى الوظيفي بنجاح")
                self.position_deleted.emit(self.current_position_id)
                self.load_positions()
                self.new_position()  # Clear form
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء حذف المسمى الوظيفي: {result}")
