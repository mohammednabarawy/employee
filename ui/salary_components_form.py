from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QSpinBox, QDoubleSpinBox,
                             QFormLayout, QDialogButtonBox, QLineEdit, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import qtawesome as qta
from ui.styles import Styles

class AddComponentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("إضافة عنصر راتب جديد")
        self.setStyleSheet(Styles.LIGHT_THEME)
        
        layout = QFormLayout()
        self.setLayout(layout)
        
        # Name fields
        self.name_ar = QLineEdit()
        self.name_en = QLineEdit()
        layout.addRow("الاسم (عربي):", self.name_ar)
        layout.addRow("Name (English):", self.name_en)
        
        # Type selection
        self.type_combo = QComboBox()
        self.type_combo.addItems(["بدل", "خصم"])
        layout.addRow("النوع:", self.type_combo)
        
        # Value type
        self.is_percentage = QCheckBox("نسبة مئوية")
        self.is_percentage.stateChanged.connect(self.toggle_value_type)
        layout.addRow("نوع القيمة:", self.is_percentage)
        
        # Value/Percentage
        self.value = QDoubleSpinBox()
        self.value.setMaximum(1000000)
        self.value.setMinimum(0)
        self.value.setDecimals(2)
        layout.addRow("القيمة:", self.value)
        
        # Taxable
        self.is_taxable = QCheckBox("خاضع للضريبة")
        self.is_taxable.setChecked(True)
        layout.addRow("الضريبة:", self.is_taxable)
        
        # Description
        self.description = QLineEdit()
        layout.addRow("الوصف:", self.description)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        
    def toggle_value_type(self, state):
        if state == Qt.Checked:
            self.value.setMaximum(100)
            self.value.setPrefix("")
            self.value.setSuffix("%")
        else:
            self.value.setMaximum(1000000)
            self.value.setPrefix("ر.س ")
            self.value.setSuffix("")
            
    def get_data(self):
        return {
            'name': self.name_en.text(),
            'name_ar': self.name_ar.text(),
            'type': 'allowance' if self.type_combo.currentText() == "بدل" else 'deduction',
            'is_percentage': self.is_percentage.isChecked(),
            'value': self.value.value(),
            'is_taxable': self.is_taxable.isChecked(),
            'description': self.description.text()
        }

class SalaryComponentsForm(QWidget):
    def __init__(self, payroll_controller, parent=None):
        super().__init__(parent)
        self.payroll_controller = payroll_controller
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(Styles.LIGHT_THEME)
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add toolbar
        toolbar = QHBoxLayout()
        
        # Add component button
        add_btn = QPushButton()
        add_btn.setIcon(qta.icon('fa5s.plus', color='white'))
        add_btn.setText("إضافة عنصر جديد")
        add_btn.clicked.connect(self.add_component)
        toolbar.addWidget(add_btn)
        
        # Filter by type
        self.type_filter = QComboBox()
        self.type_filter.addItems(["الكل", "البدلات", "الخصومات"])
        self.type_filter.currentIndexChanged.connect(self.load_components)
        toolbar.addWidget(QLabel("تصفية:"))
        toolbar.addWidget(self.type_filter)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Components table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "الاسم", "Name", "النوع", "القيمة",
            "نسبة", "ضريبة", "الوصف", ""
        ])
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Load initial data
        self.load_components()
        
    def load_components(self):
        filter_type = self.type_filter.currentText()
        component_type = None
        if filter_type == "البدلات":
            component_type = "allowance"
        elif filter_type == "الخصومات":
            component_type = "deduction"
            
        success, components = self.payroll_controller.get_salary_components(component_type)
        
        if not success:
            QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء تحميل عناصر الراتب: {components}")
            return
            
        self.table.setRowCount(len(components))
        for i, comp in enumerate(components):
            # Name (Arabic)
            self.table.setItem(i, 0, QTableWidgetItem(comp['name_ar']))
            
            # Name (English)
            self.table.setItem(i, 1, QTableWidgetItem(comp['name']))
            
            # Type
            type_text = "بدل" if comp['type'] == 'allowance' else "خصم"
            type_item = QTableWidgetItem(type_text)
            type_item.setIcon(
                qta.icon('fa5s.plus-circle', color='#27ae60')
                if comp['type'] == 'allowance'
                else qta.icon('fa5s.minus-circle', color='#c0392b')
            )
            self.table.setItem(i, 2, type_item)
            
            # Value
            if comp['is_percentage']:
                value_text = f"{comp['percentage']}%"
            else:
                value_text = f"{comp['value']:,.2f} ر.س"
            self.table.setItem(i, 3, QTableWidgetItem(value_text))
            
            # Is Percentage
            is_percentage = QTableWidgetItem()
            is_percentage.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            is_percentage.setCheckState(
                Qt.Checked if comp['is_percentage'] else Qt.Unchecked
            )
            self.table.setItem(i, 4, is_percentage)
            
            # Is Taxable
            is_taxable = QTableWidgetItem()
            is_taxable.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            is_taxable.setCheckState(
                Qt.Checked if comp['is_taxable'] else Qt.Unchecked
            )
            self.table.setItem(i, 5, is_taxable)
            
            # Description
            self.table.setItem(i, 6, QTableWidgetItem(comp.get('description', '')))
            
            # Actions
            actions_layout = QHBoxLayout()
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            
            edit_btn = QPushButton()
            edit_btn.setIcon(qta.icon('fa5s.edit', color='white'))
            edit_btn.clicked.connect(lambda checked, row=i: self.edit_component(row))
            
            delete_btn = QPushButton()
            delete_btn.setIcon(qta.icon('fa5s.trash-alt', color='white'))
            delete_btn.setProperty('class', 'danger')
            delete_btn.clicked.connect(lambda checked, row=i: self.delete_component(row))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            self.table.setCellWidget(i, 7, actions_widget)
            
        self.table.resizeColumnsToContents()
        
    def add_component(self):
        dialog = AddComponentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            success, message = self.payroll_controller.add_salary_component(data)
            
            if success:
                self.load_components()
            else:
                QMessageBox.warning(self, "خطأ", f"حدث خطأ أثناء إضافة عنصر الراتب: {message}")
                
    def edit_component(self, row):
        component_id = self.table.item(row, 0).data(Qt.UserRole)
        dialog = AddComponentDialog(self)
        
        # Load current data
        name_ar = self.table.item(row, 0).text()
        name_en = self.table.item(row, 1).text()
        comp_type = self.table.item(row, 2).text()
        value_text = self.table.item(row, 3).text()
        is_percentage = self.table.item(row, 4).checkState() == Qt.Checked
        is_taxable = self.table.item(row, 5).checkState() == Qt.Checked
        description = self.table.item(row, 6).text()
        
        dialog.name_ar.setText(name_ar)
        dialog.name_en.setText(name_en)
        dialog.type_combo.setCurrentText("بدل" if comp_type == "بدل" else "خصم")
        dialog.is_percentage.setChecked(is_percentage)
        dialog.is_taxable.setChecked(is_taxable)
        dialog.description.setText(description)
        
        if is_percentage:
            dialog.value.setValue(float(value_text.strip('%')))
        else:
            dialog.value.setValue(float(value_text.split()[0].replace(',', '')))
        
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            success, message = self.payroll_controller.update_salary_component(
                component_id, data
            )
            
            if success:
                self.load_components()
            else:
                QMessageBox.warning(
                    self, "خطأ",
                    f"حدث خطأ أثناء تحديث عنصر الراتب: {message}"
                )
                
    def delete_component(self, row):
        component_id = self.table.item(row, 0).data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذا العنصر؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = self.payroll_controller.delete_salary_component(component_id)
            
            if success:
                self.load_components()
            else:
                QMessageBox.warning(
                    self, "خطأ",
                    f"حدث خطأ أثناء حذف عنصر الراتب: {message}"
                )
