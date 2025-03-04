from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox,
                             QFormLayout, QGroupBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
import qtawesome as qta
from datetime import datetime

class LicenseDialog(QDialog):
    """Dialog for license activation and management"""
    
    def __init__(self, license_manager, parent=None):
        super().__init__(parent)
        self.license_manager = license_manager
        self.init_ui()
        self.load_license_info()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("إدارة الترخيص")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Create header
        header = QFrame()
        header.setObjectName("licenseHeader")
        header.setStyleSheet("""
            QFrame#licenseHeader {
                background-color: #3498db;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        
        # Add icon
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon('fa5s.key', color='white').pixmap(32, 32))
        header_layout.addWidget(icon_label)
        
        # Add title
        title_label = QLabel("إدارة ترخيص البرنامج")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # License information group
        info_group = QGroupBox("معلومات الترخيص")
        info_layout = QFormLayout(info_group)
        info_layout.setLabelAlignment(Qt.AlignRight)
        info_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        
        self.status_label = QLabel()
        self.key_label = QLabel()
        self.activation_date_label = QLabel()
        self.expiration_date_label = QLabel()
        self.days_remaining_label = QLabel()
        
        info_layout.addRow("الحالة:", self.status_label)
        info_layout.addRow("مفتاح الترخيص:", self.key_label)
        info_layout.addRow("تاريخ التفعيل:", self.activation_date_label)
        info_layout.addRow("تاريخ الانتهاء:", self.expiration_date_label)
        info_layout.addRow("الأيام المتبقية:", self.days_remaining_label)
        
        main_layout.addWidget(info_group)
        
        # License activation group
        activation_group = QGroupBox("تفعيل الترخيص")
        activation_layout = QVBoxLayout(activation_group)
        
        # License key input
        key_layout = QHBoxLayout()
        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText("أدخل مفتاح الترخيص هنا")
        self.license_key_input.setMinimumHeight(30)
        
        activate_button = QPushButton("تفعيل")
        activate_button.setMinimumHeight(30)
        activate_button.clicked.connect(self.activate_license)
        
        key_layout.addWidget(self.license_key_input)
        key_layout.addWidget(activate_button)
        
        activation_layout.addLayout(key_layout)
        
        # Help text
        help_text = QLabel("لتفعيل البرنامج، يرجى إدخال مفتاح الترخيص الذي تلقيته عند شراء البرنامج. "
                           "إذا لم يكن لديك مفتاح ترخيص، يرجى الاتصال بفريق الدعم.")
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        activation_layout.addWidget(help_text)
        
        main_layout.addWidget(activation_group)
        
        # Add spacer
        main_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Add buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.refresh_button = QPushButton("تحديث")
        self.refresh_button.clicked.connect(self.load_license_info)
        
        self.close_button = QPushButton("إغلاق")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
    def load_license_info(self):
        """Load and display license information"""
        license_info = self.license_manager.get_license_info()
        
        # Update UI with license information
        self.status_label.setText(license_info["status"])
        self.key_label.setText(license_info["license_key"] or "غير مفعل")
        self.activation_date_label.setText(license_info["activation_date"] or "غير متوفر")
        self.expiration_date_label.setText(license_info["expiration_date"] or "غير متوفر")
        self.days_remaining_label.setText(str(license_info["days_remaining"]) if license_info["days_remaining"] > 0 else "غير متوفر")
        
        # Set status color
        status = license_info["status"]
        if status == "Active":
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status == "Expired":
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        elif "Expiring Soon" in status:
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: gray; font-weight: bold;")
    
    def activate_license(self):
        """Activate the license with the entered key"""
        license_key = self.license_key_input.text().strip()
        
        if not license_key:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال مفتاح الترخيص")
            return
        
        success, message = self.license_manager.activate_license(license_key)
        
        if success:
            QMessageBox.information(self, "نجاح", "تم تفعيل الترخيص بنجاح")
            self.load_license_info()
            self.license_key_input.clear()
        else:
            QMessageBox.critical(self, "خطأ", f"فشل تفعيل الترخيص: {message}")
