import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QFrame, QStackedWidget,
                           QLabel, QSpacerItem, QSizePolicy, QToolButton, 
                           QMenu, QAction, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QIcon, QFont
import qtawesome as qta

from ui.employee_form import EmployeeForm
from ui.payroll_form import PayrollForm
from ui.reports_form import ReportsForm
from ui.dashboard import Dashboard
from ui.styles import Styles

from controllers.employee_controller import EmployeeController
from controllers.payroll_controller import PayrollController
from database.database import Database
from database.migration_runner import run_migrations

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize settings
        self.settings = QSettings("EmployeeApp", "Settings")
        
        # Initialize database and controllers
        self.db = Database()
        
        # Run database migrations
        self.run_migrations()
        
        self.employee_controller = EmployeeController(self.db)
        self.payroll_controller = PayrollController(self.db)
        
        # Initialize UI
        self.current_theme = self.settings.value("theme", "light")
        self.init_ui()
        
        # Apply saved theme
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
        backup_action = QAction("نسخ احتياطي", db_menu)
        restore_action = QAction("استعادة", db_menu)
        recreate_action = QAction("إعادة إنشاء الجداول", db_menu)
        
        backup_action.triggered.connect(self.backup_database)
        restore_action.triggered.connect(self.restore_database)
        recreate_action.triggered.connect(self.recreate_tables)
        
        db_menu.addAction(backup_action)
        db_menu.addAction(restore_action)
        db_menu.addAction(recreate_action)
        
        # Add menus to settings menu
        settings_menu.addMenu(theme_menu)
        settings_menu.addMenu(db_menu)
        
        # Connect settings button to show menu
        settings_btn.clicked.connect(lambda: settings_menu.exec_(settings_btn.mapToGlobal(settings_btn.rect().bottomLeft())))
        
        sidebar_layout.addWidget(settings_btn)
        
        # Create stacked widget for main content
        self.stack = QStackedWidget()
        self.stack.addWidget(Dashboard(self.employee_controller, self.payroll_controller, self.db))
        self.stack.addWidget(EmployeeForm(self.employee_controller))
        self.stack.addWidget(PayrollForm(self.payroll_controller, self.employee_controller))
        self.stack.addWidget(ReportsForm(self.employee_controller, self.payroll_controller))
        
        # Add sidebar and stack to main layout
        layout.addWidget(sidebar)
        layout.addWidget(self.stack)
        
        # Connect buttons
        self.dashboard_btn.clicked.connect(lambda: self.switch_page(0))
        self.employee_btn.clicked.connect(lambda: self.switch_page(1))
        self.payroll_btn.clicked.connect(lambda: self.switch_page(2))
        self.reports_btn.clicked.connect(lambda: self.switch_page(3))
        
        # Set initial page
        self.dashboard_btn.setChecked(True)
        self.stack.setCurrentIndex(0)
        
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
        
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        
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
            self.db.backup_database()
            QMessageBox.information(self, "نجاح", "تم إنشاء نسخة احتياطية من قاعدة البيانات بنجاح")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إنشاء النسخة الاحتياطية: {str(e)}")
            
    def restore_database(self):
        """Restore the database from backup"""
        reply = QMessageBox.question(self, "تأكيد", 
                                    "هل أنت متأكد من استعادة قاعدة البيانات من النسخة الاحتياطية؟ سيتم فقدان أي تغييرات غير محفوظة.",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.restore_database()
                QMessageBox.information(self, "نجاح", "تم استعادة قاعدة البيانات بنجاح")
                # Refresh all views
                self.refresh_all_views()
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
        if isinstance(self.stack.widget(0), Dashboard):
            self.stack.widget(0).refresh_data()
            
        # Refresh employee form
        if isinstance(self.stack.widget(1), EmployeeForm):
            self.stack.widget(1).load_employees()
            
        # Refresh payroll form
        if isinstance(self.stack.widget(2), PayrollForm):
            self.stack.widget(2).load_periods()
            
        # Refresh reports form
        if isinstance(self.stack.widget(3), ReportsForm):
            if hasattr(self.stack.widget(3), 'refresh_data'):
                self.stack.widget(3).refresh_data()

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
