from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QFileDialog, QInputDialog, 
                             QMessageBox, QLineEdit, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
import os
import shutil
import sqlite3
from ui.company_info_dialog import CompanyInfoDialog

class DatabaseManagerDialog(QDialog):
    """Dialog for managing database files"""
    
    # Signal emitted when a database is selected
    database_changed = pyqtSignal(str)
    
    def __init__(self, current_db_file, parent=None):
        super().__init__(parent)
        self.current_db_file = current_db_file
        self.db_dir = os.path.dirname(os.path.abspath(current_db_file))
        self.init_ui()
        self.load_database_list()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("إدارة قواعد البيانات")
        self.setMinimumSize(500, 400)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Add header label
        header_label = QLabel("إدارة قواعد البيانات")
        header_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Add current database label
        current_db_layout = QHBoxLayout()
        current_db_label = QLabel("قاعدة البيانات الحالية:")
        current_db_label.setStyleSheet("font-weight: bold;")
        self.current_db_value = QLabel(self.current_db_file)
        current_db_layout.addWidget(current_db_label)
        current_db_layout.addWidget(self.current_db_value)
        main_layout.addLayout(current_db_layout)
        
        # Add list of databases
        list_label = QLabel("قواعد البيانات المتاحة:")
        list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(list_label)
        
        self.db_list = QListWidget()
        self.db_list.setMinimumHeight(200)
        self.db_list.itemDoubleClicked.connect(self.select_database)
        main_layout.addWidget(self.db_list)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.open_db_btn = QPushButton("فتح قاعدة البيانات")
        self.open_db_btn.clicked.connect(self.open_database)
        button_layout.addWidget(self.open_db_btn)
        
        self.new_db_btn = QPushButton("إنشاء قاعدة بيانات جديدة")
        self.new_db_btn.clicked.connect(self.create_new_database)
        button_layout.addWidget(self.new_db_btn)
        
        self.import_db_btn = QPushButton("استيراد قاعدة بيانات")
        self.import_db_btn.clicked.connect(self.import_database)
        button_layout.addWidget(self.import_db_btn)
        
        self.delete_db_btn = QPushButton("حذف قاعدة البيانات")
        self.delete_db_btn.clicked.connect(self.delete_database)
        button_layout.addWidget(self.delete_db_btn)
        
        main_layout.addLayout(button_layout)
        
        # Add company info button
        company_info_layout = QHBoxLayout()
        self.company_info_btn = QPushButton("إدارة معلومات الشركة")
        self.company_info_btn.clicked.connect(self.manage_company_info)
        company_info_layout.addWidget(self.company_info_btn)
        company_info_layout.addStretch()
        
        main_layout.addLayout(company_info_layout)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def load_database_list(self):
        """Load the list of database files"""
        self.db_list.clear()
        
        # Get all .db files in the directory
        db_files = [f for f in os.listdir(self.db_dir) if f.endswith('.db')]
        
        # Add them to the list
        for db_file in db_files:
            self.db_list.addItem(db_file)
            
            # Select the current database
            if db_file == os.path.basename(self.current_db_file):
                self.db_list.setCurrentRow(self.db_list.count() - 1)
    
    def select_database(self, item=None):
        """Select a database from the list"""
        if not item:
            item = self.db_list.currentItem()
            if not item:
                return
        
        db_file = item.text()
        full_path = os.path.join(self.db_dir, db_file)
        
        # Check if the file exists
        if not os.path.exists(full_path):
            QMessageBox.warning(self, "خطأ", "ملف قاعدة البيانات غير موجود")
            return
        
        # Check if it's a valid SQLite database
        try:
            conn = sqlite3.connect(full_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            
            if result[0] != "ok":
                QMessageBox.warning(self, "خطأ", "ملف قاعدة البيانات تالف")
                return
        except:
            QMessageBox.warning(self, "خطأ", "ملف قاعدة البيانات غير صالح")
            return
        
        # Update current database
        self.current_db_file = full_path
        self.current_db_value.setText(full_path)
        
        # Emit signal
        self.database_changed.emit(full_path)
    
    def create_new_database(self):
        """Create a new database file"""
        # Show dialog to get database name
        name, ok = QInputDialog.getText(self, "إنشاء قاعدة بيانات جديدة", 
                                        "اسم قاعدة البيانات:", QLineEdit.Normal)
        
        if not ok or not name:
            return
        
        # Add .db extension if not present
        if not name.endswith('.db'):
            name += '.db'
        
        # Check if file already exists
        full_path = os.path.join(self.db_dir, name)
        if os.path.exists(full_path):
            QMessageBox.warning(self, "خطأ", "قاعدة البيانات موجودة بالفعل")
            return
        
        # Create empty database file
        try:
            conn = sqlite3.connect(full_path)
            conn.close()
            
            # Reload the list
            self.load_database_list()
            
            # Ask if user wants to switch to the new database
            reply = QMessageBox.question(self, "تبديل قاعدة البيانات", 
                                        "هل تريد التبديل إلى قاعدة البيانات الجديدة؟",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # Find the new database in the list
                for i in range(self.db_list.count()):
                    if self.db_list.item(i).text() == name:
                        self.db_list.setCurrentRow(i)
                        self.select_database(self.db_list.item(i))
                        break
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنشاء قاعدة البيانات: {str(e)}")
    
    def import_database(self):
        """Import a database file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "استيراد قاعدة بيانات", 
                                                 "", "SQLite Database (*.db)")
        
        if not file_path:
            return
        
        # Get the filename
        filename = os.path.basename(file_path)
        
        # Check if file already exists
        target_path = os.path.join(self.db_dir, filename)
        if os.path.exists(target_path):
            # Ask for a new name
            new_name, ok = QInputDialog.getText(self, "تغيير اسم قاعدة البيانات", 
                                             "اسم قاعدة البيانات:", QLineEdit.Normal, 
                                             filename)
            
            if not ok or not new_name:
                return
            
            # Add .db extension if not present
            if not new_name.endswith('.db'):
                new_name += '.db'
            
            target_path = os.path.join(self.db_dir, new_name)
            
            # Check again
            if os.path.exists(target_path):
                QMessageBox.warning(self, "خطأ", "قاعدة البيانات موجودة بالفعل")
                return
        
        # Copy the file
        try:
            shutil.copy2(file_path, target_path)
            
            # Reload the list
            self.load_database_list()
            
            # Ask if user wants to switch to the imported database
            reply = QMessageBox.question(self, "تبديل قاعدة البيانات", 
                                        "هل تريد التبديل إلى قاعدة البيانات المستوردة؟",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                # Find the imported database in the list
                imported_name = os.path.basename(target_path)
                for i in range(self.db_list.count()):
                    if self.db_list.item(i).text() == imported_name:
                        self.db_list.setCurrentRow(i)
                        self.select_database(self.db_list.item(i))
                        break
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء استيراد قاعدة البيانات: {str(e)}")
    
    def delete_database(self):
        """Delete a database file"""
        item = self.db_list.currentItem()
        if not item:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد قاعدة بيانات للحذف")
            return
        
        db_file = item.text()
        full_path = os.path.join(self.db_dir, db_file)
        
        # Check if it's the current database
        if full_path == self.current_db_file:
            QMessageBox.warning(self, "تحذير", "لا يمكن حذف قاعدة البيانات الحالية")
            return
        
        # Confirm deletion
        reply = QMessageBox.question(self, "تأكيد الحذف", 
                                    f"هل أنت متأكد من حذف قاعدة البيانات '{db_file}'؟\n\nهذا الإجراء لا يمكن التراجع عنه.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        # Delete the file
        try:
            os.remove(full_path)
            
            # Reload the list
            self.load_database_list()
            
            QMessageBox.information(self, "نجاح", "تم حذف قاعدة البيانات بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حذف قاعدة البيانات: {str(e)}")
    
    def open_database(self):
        """Open the selected database"""
        item = self.db_list.currentItem()
        if not item:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد قاعدة بيانات للفتح")
            return
        
        db_file = item.text()
        full_path = os.path.join(self.db_dir, db_file)
        
        # Check if the file exists
        if not os.path.exists(full_path):
            QMessageBox.warning(self, "خطأ", "ملف قاعدة البيانات غير موجود")
            return
        
        # Check if it's already the current database
        if full_path == self.current_db_file:
            QMessageBox.information(self, "معلومات", "قاعدة البيانات مفتوحة بالفعل")
            return
        
        # Open the database
        self.select_database(item)
        self.accept()
    
    def manage_company_info(self):
        """Open the company info dialog"""
        item = self.db_list.currentItem()
        if not item:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد قاعدة بيانات لإدارة معلومات الشركة")
            return
        
        db_file = item.text()
        full_path = os.path.join(self.db_dir, db_file)
        
        # Check if the file exists
        if not os.path.exists(full_path):
            QMessageBox.warning(self, "خطأ", "ملف قاعدة البيانات غير موجود")
            return
        
        # Open the company info dialog
        dialog = CompanyInfoDialog(full_path, self)
        dialog.exec_()
