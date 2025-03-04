from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFormLayout, QDialogButtonBox,
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
import os
import sqlite3

class CompanyInfoDialog(QDialog):
    """Dialog for managing company information"""
    
    # Signal emitted when company info is updated
    info_updated = pyqtSignal()
    
    def __init__(self, db_file, parent=None):
        super().__init__(parent)
        self.db_file = db_file
        self.init_ui()
        self.load_company_info()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("معلومات الشركة")
        self.setMinimumSize(500, 400)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Add header label
        header_label = QLabel("معلومات الشركة")
        header_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Create form layout
        form_layout = QFormLayout()
        
        # Add form fields
        self.company_name_edit = QLineEdit()
        form_layout.addRow("اسم الشركة:", self.company_name_edit)
        
        self.commercial_register_edit = QLineEdit()
        form_layout.addRow("رقم السجل التجاري:", self.commercial_register_edit)
        
        self.social_insurance_edit = QLineEdit()
        form_layout.addRow("رقم التأمينات الاجتماعية:", self.social_insurance_edit)
        
        self.tax_number_edit = QLineEdit()
        form_layout.addRow("الرقم الضريبي:", self.tax_number_edit)
        
        self.address_edit = QLineEdit()
        form_layout.addRow("العنوان:", self.address_edit)
        
        self.phone_edit = QLineEdit()
        form_layout.addRow("رقم الهاتف:", self.phone_edit)
        
        self.email_edit = QLineEdit()
        form_layout.addRow("البريد الإلكتروني:", self.email_edit)
        
        self.website_edit = QLineEdit()
        form_layout.addRow("الموقع الإلكتروني:", self.website_edit)
        
        main_layout.addLayout(form_layout)
        
        # Add logo section
        logo_layout = QHBoxLayout()
        
        self.logo_label = QLabel("شعار الشركة:")
        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(100, 100)
        self.logo_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        
        self.select_logo_btn = QPushButton("اختيار شعار")
        self.select_logo_btn.clicked.connect(self.select_logo)
        
        logo_layout.addWidget(self.logo_label)
        logo_layout.addWidget(self.logo_preview)
        logo_layout.addWidget(self.select_logo_btn)
        logo_layout.addStretch()
        
        main_layout.addLayout(logo_layout)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_company_info)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Initialize logo data
        self.logo_data = None
        self.logo_mime_type = None
    
    def load_company_info(self):
        """Load company information from the database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if company_info table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_info'")
            if not cursor.fetchone():
                conn.close()
                return
            
            # Get company info
            cursor.execute("SELECT * FROM company_info LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                company_info = dict(zip(column_names, row))
                
                # Set form values
                self.company_name_edit.setText(company_info.get('company_name', ''))
                self.commercial_register_edit.setText(company_info.get('commercial_register_number', ''))
                self.social_insurance_edit.setText(company_info.get('social_insurance_number', ''))
                self.tax_number_edit.setText(company_info.get('tax_number', ''))
                self.address_edit.setText(company_info.get('address', ''))
                self.phone_edit.setText(company_info.get('phone', ''))
                self.email_edit.setText(company_info.get('email', ''))
                self.website_edit.setText(company_info.get('website', ''))
                
                # Set logo data
                self.logo_data = company_info.get('logo_data')
                self.logo_mime_type = company_info.get('logo_mime_type')
                
                # Display logo if available
                if self.logo_data:
                    pixmap = QPixmap()
                    pixmap.loadFromData(self.logo_data)
                    self.logo_preview.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل معلومات الشركة: {str(e)}")
    
    def select_logo(self):
        """Select a logo file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "اختيار شعار الشركة", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if not file_path:
            return
        
        try:
            # Load the image
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "تحذير", "فشل تحميل الصورة")
                return
            
            # Display the image
            self.logo_preview.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # Read the file data
            with open(file_path, 'rb') as f:
                self.logo_data = f.read()
            
            # Set the mime type
            if file_path.lower().endswith('.png'):
                self.logo_mime_type = 'image/png'
            elif file_path.lower().endswith(('.jpg', '.jpeg')):
                self.logo_mime_type = 'image/jpeg'
            elif file_path.lower().endswith('.bmp'):
                self.logo_mime_type = 'image/bmp'
            else:
                self.logo_mime_type = 'image/unknown'
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تحميل الصورة: {str(e)}")
    
    def save_company_info(self):
        """Save company information to the database"""
        # Validate required fields
        if not self.company_name_edit.text().strip():
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال اسم الشركة")
            return
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if company_info table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_info'")
            if not cursor.fetchone():
                # Create the table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS company_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_name TEXT NOT NULL,
                        commercial_register_number TEXT,
                        social_insurance_number TEXT,
                        tax_number TEXT,
                        address TEXT,
                        phone TEXT,
                        email TEXT,
                        website TEXT,
                        logo_data BLOB,
                        logo_mime_type TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # Check if a record already exists
            cursor.execute("SELECT COUNT(*) FROM company_info")
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Update existing record
                cursor.execute('''
                    UPDATE company_info SET
                        company_name = ?,
                        commercial_register_number = ?,
                        social_insurance_number = ?,
                        tax_number = ?,
                        address = ?,
                        phone = ?,
                        email = ?,
                        website = ?,
                        logo_data = ?,
                        logo_mime_type = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                ''', (
                    self.company_name_edit.text(),
                    self.commercial_register_edit.text(),
                    self.social_insurance_edit.text(),
                    self.tax_number_edit.text(),
                    self.address_edit.text(),
                    self.phone_edit.text(),
                    self.email_edit.text(),
                    self.website_edit.text(),
                    self.logo_data,
                    self.logo_mime_type
                ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO company_info (
                        company_name,
                        commercial_register_number,
                        social_insurance_number,
                        tax_number,
                        address,
                        phone,
                        email,
                        website,
                        logo_data,
                        logo_mime_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.company_name_edit.text(),
                    self.commercial_register_edit.text(),
                    self.social_insurance_edit.text(),
                    self.tax_number_edit.text(),
                    self.address_edit.text(),
                    self.phone_edit.text(),
                    self.email_edit.text(),
                    self.website_edit.text(),
                    self.logo_data,
                    self.logo_mime_type
                ))
            
            conn.commit()
            conn.close()
            
            # Emit signal to notify that company info has been updated
            self.info_updated.emit()
            
            QMessageBox.information(self, "نجاح", "تم حفظ معلومات الشركة بنجاح")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ معلومات الشركة: {str(e)}")
