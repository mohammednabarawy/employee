from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                           QTableWidgetItem, QPushButton, QLineEdit, QLabel,
                           QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

class EmployeeList(QWidget):
    employee_selected = pyqtSignal(dict)
    employee_deleted = pyqtSignal(int)

    def __init__(self, employee_controller, parent=None):
        super().__init__(parent)
        self.employee_controller = employee_controller
        self.init_ui()
        self.load_employees()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search employees...")
        self.search_input.textChanged.connect(self.search_employees)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Employee table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Name", "Department", "Position",
            "Phone", "Email", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Refresh button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.load_employees)
        layout.addWidget(refresh_btn)

    def load_employees(self):
        success, employees = self.employee_controller.get_all_employees()
        if success:
            self.populate_table(employees)
        else:
            QMessageBox.warning(self, "Error", "Failed to load employees")

    def populate_table(self, employees):
        self.table.setRowCount(0)
        for employee in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Add employee data
            self.table.setItem(row, 0, QTableWidgetItem(str(employee['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(employee['name']))
            self.table.setItem(row, 2, QTableWidgetItem(employee['department']))
            self.table.setItem(row, 3, QTableWidgetItem(employee['position']))
            self.table.setItem(row, 4, QTableWidgetItem(employee['phone']))
            self.table.setItem(row, 5, QTableWidgetItem(employee['email']))

            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda checked, e=employee: self.employee_selected.emit(e))
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, e=employee: self.delete_employee(e['id']))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            self.table.setCellWidget(row, 6, actions_widget)

    def search_employees(self, search_term):
        if not search_term:
            self.load_employees()
            return

        success, employees = self.employee_controller.search_employees(search_term)
        if success:
            self.populate_table(employees)

    def delete_employee(self, employee_id):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this employee?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success, error = self.employee_controller.delete_employee(employee_id)
            if success:
                self.employee_deleted.emit(employee_id)
                self.load_employees()
                QMessageBox.information(self, "Success", "Employee deleted successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete employee: {error}")
