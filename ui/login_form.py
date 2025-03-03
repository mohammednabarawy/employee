from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox,
                             QCheckBox, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
import qtawesome as qta
from .styles import Styles

class LoginForm(QWidget):
    """Login form for the application"""
    
    # Signals
    login_successful = pyqtSignal(dict)
    
    def __init__(self, auth_controller):
        super().__init__()
        self.auth_controller = auth_controller
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        # Set window properties
        self.setWindowTitle("تسجيل الدخول - نظام إدارة الموظفين")
        self.setMinimumSize(400, 500)
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header
        header = QFrame()
        header.setObjectName("loginHeader")
        header.setMinimumHeight(150)
        header.setStyleSheet("""
            QFrame#loginHeader {
                background-color: #3498db;
                border-bottom: 1px solid #2980b9;
            }
        """)
        
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Add logo
        logo_label = QLabel()
        logo_icon = qta.icon('fa5s.users', color='white')
        logo_label.setPixmap(logo_icon.pixmap(64, 64))
        logo_label.setAlignment(Qt.AlignCenter)
        
        # Add title
        title_label = QLabel("نظام إدارة الموظفين")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Add subtitle
        subtitle_label = QLabel("تسجيل الدخول للنظام")
        subtitle_label.setStyleSheet("color: white; font-size: 16px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        
        # Create content
        content = QFrame()
        content.setObjectName("loginContent")
        content.setStyleSheet("""
            QFrame#loginContent {
                background-color: white;
            }
        """)
        
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(15)
        
        # Username field
        username_label = QLabel("اسم المستخدم")
        username_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setMinimumHeight(40)
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        
        # Password field
        password_label = QLabel("كلمة المرور")
        password_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
            }
        """)
        
        # Remember me checkbox
        remember_layout = QHBoxLayout()
        
        self.remember_checkbox = QCheckBox("تذكرني")
        self.remember_checkbox.setStyleSheet("font-size: 14px;")
        
        forgot_button = QPushButton("نسيت كلمة المرور؟")
        forgot_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #3498db;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                color: #2980b9;
                text-decoration: underline;
            }
        """)
        forgot_button.setCursor(Qt.PointingHandCursor)
        forgot_button.clicked.connect(self.forgot_password)
        
        remember_layout.addWidget(self.remember_checkbox)
        remember_layout.addStretch()
        remember_layout.addWidget(forgot_button)
        
        # Login button
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setMinimumHeight(45)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.login)
        
        # Add widgets to content layout
        content_layout.addWidget(username_label)
        content_layout.addWidget(self.username_input)
        content_layout.addWidget(password_label)
        content_layout.addWidget(self.password_input)
        content_layout.addLayout(remember_layout)
        content_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        content_layout.addWidget(self.login_button)
        content_layout.addStretch()
        
        # Add footer
        footer = QFrame()
        footer.setObjectName("loginFooter")
        footer.setMinimumHeight(50)
        footer.setStyleSheet("""
            QFrame#loginFooter {
                background-color: #f8f9fa;
                border-top: 1px solid #e0e0e0;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        
        copyright_label = QLabel("© 2025 نظام إدارة الموظفين. جميع الحقوق محفوظة.")
        copyright_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        footer_layout.addWidget(copyright_label)
        footer_layout.addStretch()
        
        # Add all sections to main layout
        main_layout.addWidget(header)
        main_layout.addWidget(content, 1)
        main_layout.addWidget(footer)
        
        # Set focus on username input
        self.username_input.setFocus()
        
        # Connect enter key to login
        self.username_input.returnPressed.connect(self.login)
        self.password_input.returnPressed.connect(self.login)
    
    def login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال اسم المستخدم")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال كلمة المرور")
            self.password_input.setFocus()
            return
        
        # Disable login button and show loading state
        self.login_button.setEnabled(False)
        self.login_button.setText("جاري تسجيل الدخول...")
        
        # Attempt login
        success, result = self.auth_controller.login(username, password)
        
        # Reset login button
        self.login_button.setEnabled(True)
        self.login_button.setText("تسجيل الدخول")
        
        if success:
            # Save remember me preference
            # In a real app, you'd store this in settings
            
            # Emit signal
            self.login_successful.emit(result)
            
            # Clear fields
            self.username_input.clear()
            self.password_input.clear()
            
        else:
            # Show error message
            QMessageBox.warning(self, "خطأ في تسجيل الدخول", result)
    
    def forgot_password(self):
        """Handle forgot password button click"""
        QMessageBox.information(
            self, 
            "استعادة كلمة المرور", 
            "يرجى الاتصال بمسؤول النظام لاستعادة كلمة المرور الخاصة بك."
        )
