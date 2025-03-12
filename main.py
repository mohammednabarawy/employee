import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QFrame, QStackedWidget,
                           QLabel, QSpacerItem, QSizePolicy, QToolButton, 
                           QMessageBox, QMenu, QAction, QFileDialog, QInputDialog,
                           QDialog)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QFont
import qtawesome as qta
from datetime import datetime

from database.database import Database
from database.migration_runner import run_migrations
from controllers.employee_controller import EmployeeController
from controllers.payroll_controller import PayrollController
from controllers.auth_controller import AuthController
from controllers.attendance_controller import AttendanceController
from ui.dashboard import Dashboard
from ui.employee_form import EmployeeForm
from ui.payroll_form import PayrollForm
from ui.reports_form import ReportsForm
from ui.login_form import LoginForm
from ui.license_dialog import LicenseDialog
from ui.database_manager_dialog import DatabaseManagerDialog
from ui.styles import Styles
from utils.licensing import LicenseManager
from utils.backup_manager import BackupManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize settings
        self.settings = QSettings("EmployeeApp", "Settings")
        
        # Initialize licensing
        self.license_manager = LicenseManager()
        self.license_manager.license_invalid.connect(self.handle_invalid_license)
        self.license_manager.license_expiring_soon.connect(self.handle_expiring_license)
        
        # Initialize database and controllers
        self.db = Database()
        
        # Initialize backup manager
        self.backup_manager = BackupManager(self.db.db_file)
        
        # Run database migrations
        self.run_migrations()
        
        # Initialize controllers
        self.employee_controller = EmployeeController(self.db)
        self.payroll_controller = PayrollController(self.db)
        self.auth_controller = AuthController(self.db)
        self.attendance_controller = AttendanceController(self.db)
        
        # Check if user is logged in
        self.current_user = None
        
        # Initialize UI
        self.current_theme = self.settings.value("theme", "light")
        
        # Check license before showing UI
        if not self.license_manager.validate_license():
            self.show_login_screen()
        else:
            self.init_ui()
            self.apply_theme(self.current_theme)
        
        # Auto-save timer (every 5 minutes)
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(300000)  # 5 minutes in milliseconds
        
    def init_ui(self):
        self.setWindowTitle('نظام إدارة الموظفين')
        self.setMinimumSize(1280, 800)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(250)
        sidebar.setMaximumWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(5)
        
        # Add logo/title to sidebar
        title_frame = QFrame()
        title_frame.setObjectName("titleFrame")
        title_layout = QHBoxLayout(title_frame)
        logo_label = QLabel()
        logo_label.setPixmap(qta.icon('fa5s.users', color='white').pixmap(32, 32))
        title_label = QLabel('نظام إدارة الموظفين')
        title_label.setObjectName("titleLabel")
        title_layout.addWidget(logo_label)
        title_layout.addWidget(title_label)
        sidebar_layout.addWidget(title_frame)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        sidebar_layout.addWidget(separator)
        
        # Create navigation buttons
        self.dashboard_btn = self.create_nav_button('لوحة المعلومات', 'fa5s.tachometer-alt')
        self.employee_btn = self.create_nav_button('إدارة الموظفين', 'fa5s.user-tie')
        self.payroll_btn = self.create_nav_button('إدارة الرواتب', 'fa5s.money-check-alt')
        self.reports_btn = self.create_nav_button('التقارير', 'fa5s.chart-bar')
        
        # Add buttons to sidebar
        sidebar_layout.addWidget(self.dashboard_btn)
        sidebar_layout.addWidget(self.employee_btn)
        sidebar_layout.addWidget(self.payroll_btn)
        sidebar_layout.addWidget(self.reports_btn)
        
        # Add spacer
        sidebar_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Add settings button
        settings_btn = QPushButton()
        settings_btn.setIcon(qta.icon('fa5s.cog', color='white'))
        settings_btn.setText("الإعدادات")
        settings_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                text-align: left;
                padding: 12px 15px;
                margin: 3px 5px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        
        # Create settings menu
        settings_menu = QMenu(self)
        
        # Theme actions
        theme_menu = QMenu("السمة", settings_menu)
        light_theme_action = QAction("فاتح", theme_menu)
        dark_theme_action = QAction("داكن", theme_menu)
        
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        
        theme_menu.addAction(light_theme_action)
        theme_menu.addAction(dark_theme_action)
        
        # Database actions
        db_menu = QMenu("قاعدة البيانات", settings_menu)
        
        # Add database management action
        manage_db_action = QAction("إدارة قواعد البيانات", db_menu)
        manage_db_action.triggered.connect(self.show_database_manager)
        db_menu.addAction(manage_db_action)
        
        db_menu.addSeparator()
        
        # Add database actions
        backup_action = QAction("إنشاء نسخة احتياطية", db_menu)
        backup_action.triggered.connect(self.backup_database)
        db_menu.addAction(backup_action)
        
        restore_action = QAction("استعادة من نسخة احتياطية", db_menu)
        restore_action.triggered.connect(self.restore_database)
        db_menu.addAction(restore_action)
        
        export_action = QAction("تصدير البيانات", db_menu)
        export_action.triggered.connect(self.export_data)
        db_menu.addAction(export_action)
        
        recreate_action = QAction("إعادة إنشاء الجداول", db_menu)
        recreate_action.triggered.connect(self.recreate_tables)
        db_menu.addAction(recreate_action)
        
        # Add menus to settings menu
        settings_menu.addMenu(theme_menu)
        settings_menu.addMenu(db_menu)
        
        # Add license menu
        license_action = QAction("إدارة الترخيص", settings_menu)
        license_action.triggered.connect(self.show_license_dialog)
        settings_menu.addAction(license_action)
        
        # Add logout action
        settings_menu.addSeparator()
        logout_action = QAction("تسجيل الخروج", settings_menu)
        logout_action.triggered.connect(self.logout)
        settings_menu.addAction(logout_action)
        
        # Connect settings button to show menu
        settings_btn.clicked.connect(lambda: settings_menu.exec_(settings_btn.mapToGlobal(settings_btn.rect().bottomLeft())))
        
        sidebar_layout.addWidget(settings_btn)
        
        # Create stacked widget for content
        self.stacked_widget = QStackedWidget()
        
        # Initialize forms
        self.dashboard = Dashboard(self.employee_controller, self.payroll_controller, self.db)
        self.dashboard.update_db_info(self.db.db_file)  # Set initial database info
        self.employee_form = EmployeeForm(self.employee_controller)
        self.payroll_form = PayrollForm(self.payroll_controller, self.employee_controller, self.attendance_controller)
        self.reports_form = ReportsForm(self.employee_controller, self.payroll_controller, self.attendance_controller)
        
        # Add widgets to stacked widget
        self.stacked_widget.addWidget(self.dashboard)
        self.stacked_widget.addWidget(self.employee_form)
        self.stacked_widget.addWidget(self.payroll_form)
        self.stacked_widget.addWidget(self.reports_form)
        
        # Add sidebar and stack to main layout
        layout.addWidget(sidebar)
        layout.addWidget(self.stacked_widget)
        
        # Connect buttons
        self.dashboard_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.dashboard))
        self.employee_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.employee_form))
        self.payroll_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.payroll_form))
        self.reports_btn.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.reports_form))
        
        # Set initial page
        self.dashboard_btn.setChecked(True)
        self.stacked_widget.setCurrentWidget(self.dashboard)
        
        # Create status bar
        self.statusBar().showMessage(f"قاعدة البيانات الحالية: {self.db.db_file}")
        
    def create_nav_button(self, text, icon_name):
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setAutoExclusive(True)
        
        # Create layout for button content
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(10)
        
        # Add icon
        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon_name, color='white').pixmap(20, 20))
        layout.addWidget(icon_label)
        
        # Add text
        text_label = QLabel(text)
        text_label.setStyleSheet("color: white;")
        layout.addWidget(text_label)
        
        # Add spacer
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        return btn
        
    def apply_theme(self, theme):
        """Apply the selected theme to the application"""
        if theme == "light":
            self.setStyleSheet(Styles.LIGHT_THEME)
        else:
            self.setStyleSheet(Styles.DARK_THEME)
            
        self.current_theme = theme
        self.settings.setValue("theme", theme)
        
    def auto_save(self):
        """Auto-save functionality"""
        # This would typically save any unsaved changes
        # For now, we'll just backup the database
        self.db.backup_database()
        
    def backup_database(self):
        """Backup the database"""
        try:
            success, message = self.backup_manager.create_backup(self)
            if success:
                QMessageBox.information(self, "نجاح", "تم إنشاء نسخة احتياطية من قاعدة البيانات بنجاح")
            else:
                QMessageBox.warning(self, "تحذير", message)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}")
            
    def restore_database(self):
        """Restore the database from backup"""
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من استعادة قاعدة البيانات من النسخة الاحتياطية؟ سيتم فقدان أي تغييرات غير محفوظة.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                success, message = self.backup_manager.restore_backup(self)
                if success:
                    QMessageBox.information(self, "نجاح", "تم استعادة قاعدة البيانات بنجاح")
                    # Refresh all views
                    self.refresh_all_views()
                else:
                    QMessageBox.warning(self, "تحذير", message)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء استعادة قاعدة البيانات: {str(e)}")
                
    def recreate_tables(self):
        """Recreate all database tables"""
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من إعادة إنشاء جميع الجداول؟ سيتم حذف جميع البيانات الحالية.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.recreate_tables()
                QMessageBox.information(self, "نجاح", "تم إعادة إنشاء الجداول بنجاح")
                # Refresh all views
                self.refresh_all_views()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إعادة إنشاء الجداول: {str(e)}")
                
    def refresh_all_views(self):
        """Refresh all views in the application"""
        # Refresh dashboard
        if isinstance(self.stacked_widget.widget(0), Dashboard):
            self.stacked_widget.widget(0).refresh_data()
            
        # Refresh employee form
        if isinstance(self.stacked_widget.widget(1), EmployeeForm):
            self.stacked_widget.widget(1).load_employees()
            
        # Refresh payroll form
        if isinstance(self.stacked_widget.widget(2), PayrollForm):
            self.stacked_widget.widget(2).load_periods()
            
        # Refresh reports form
        if isinstance(self.stacked_widget.widget(3), ReportsForm):
            if hasattr(self.stacked_widget.widget(3), 'refresh_data'):
                self.stacked_widget.widget(3).refresh_data()

    def run_migrations(self):
        """Run database migrations and show results if there are any issues"""
        migration_results = run_migrations(self.db)
        
        # Check for any failed migrations
        failed_migrations = [result for result in migration_results if not result[1]]
        
        if failed_migrations:
            error_message = "فشل تنفيذ بعض ترحيلات قاعدة البيانات:\n\n"
            for migration, _, message in failed_migrations:
                error_message += f"• {migration}: {message}\n"
            
            QMessageBox.warning(self, "خطأ في ترحيل قاعدة البيانات", error_message)
    
    def show_login_screen(self):
        """Show the login screen"""
        login_form = LoginForm(self.auth_controller)
        login_form.login_successful.connect(self.handle_login_successful)
        login_form.show()
    
    def handle_login_successful(self, user_data):
        """Handle successful login"""
        self.current_user = user_data
        self.init_ui()
        self.apply_theme(self.current_theme)
        self.show()
    
    def handle_invalid_license(self, message):
        """Handle invalid license"""
        QMessageBox.warning(
            self, 
            "ترخيص غير صالح", 
            f"الترخيص غير صالح أو منتهي الصلاحية: {message}\n\nيرجى تفعيل البرنامج للاستمرار."
        )
        self.show_license_dialog()
    
    def handle_expiring_license(self, days_remaining):
        """Handle expiring license"""
        QMessageBox.information(
            self, 
            "ترخيص على وشك الانتهاء", 
            f"ترخيصك سينتهي خلال {days_remaining} يوم.\n\nيرجى تجديد الترخيص لتجنب انقطاع الخدمة."
        )
    
    def show_license_dialog(self):
        """Show the license dialog"""
        dialog = LicenseDialog(self.license_manager, self)
        dialog.exec_()
        
        # Check license again after dialog closes
        if not self.license_manager.validate_license():
            # If still invalid, exit application
            QMessageBox.critical(
                self, 
                "ترخيص غير صالح", 
                "لا يمكن استخدام البرنامج بدون ترخيص صالح.\n\nسيتم إغلاق البرنامج."
            )
            sys.exit(0)
            
    def logout(self):
        """Log out the current user"""
        reply = QMessageBox.question(
            self, 
            "تأكيد تسجيل الخروج", 
            "هل أنت متأكد من رغبتك في تسجيل الخروج؟",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Hide main window
            self.hide()
            
            # Reset current user
            self.current_user = None
            
            # Show login screen
            self.show_login_screen()
            
    def export_data(self):
        """Export data to Excel or CSV"""
        try:
            success, message = self.backup_manager.export_data(self)
            if success:
                QMessageBox.information(self, "نجاح", "تم تصدير البيانات بنجاح")
            else:
                QMessageBox.warning(self, "تحذير", message)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تصدير البيانات: {str(e)}")

    def show_database_manager(self):
        """Show the database manager dialog"""
        dialog = DatabaseManagerDialog(self.db.db_file, self)
        dialog.database_changed.connect(self.change_database)
        dialog.exec_()
    
    def change_database(self, db_file):
        """Change the current database file"""
        try:
            # Update the backup manager
            self.backup_manager = BackupManager(db_file)
            
            # Update the database
            success = self.db.change_database(db_file)
            
            if success:
                # Refresh controllers
                self.employee_controller = EmployeeController(self.db)
                self.payroll_controller = PayrollController(self.db)
                self.auth_controller = AuthController(self.db)
                self.attendance_controller = AttendanceController(self.db)
                
                # Refresh all views
                self.refresh_all_views()
                
                # Update status bar
                self.statusBar().showMessage(f"قاعدة البيانات الحالية: {db_file}", 5000)
                
                # Update dashboard
                if hasattr(self, 'dashboard'):
                    self.dashboard.update_db_info(db_file)
                
                QMessageBox.information(self, "نجاح", "تم تغيير قاعدة البيانات بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تغيير قاعدة البيانات: {str(e)}")

def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    
    # Set application-wide font
    font = QFont('Segoe UI', 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )
        from main import main
        main()
    else:
        main()
