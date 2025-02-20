import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QFrame, QStackedWidget,
                           QLabel, QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
import qtawesome as qta

from ui.employee_form import EmployeeForm
from ui.payroll_form import PayrollForm
from ui.reports_form import ReportsForm
from ui.styles import Styles

from controllers.employee_controller import EmployeeController
from controllers.payroll_controller import PayrollController
from database.database import Database

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.employee_controller = EmployeeController(self.db)
        self.payroll_controller = PayrollController(self.db)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('نظام إدارة الموظفين')
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(Styles.LIGHT_THEME)
        
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
        self.employee_btn = self.create_nav_button('إدارة الموظفين', 'fa5s.user-tie')
        self.payroll_btn = self.create_nav_button('إدارة الرواتب', 'fa5s.money-check-alt')
        self.reports_btn = self.create_nav_button('التقارير', 'fa5s.chart-bar')
        
        # Add buttons to sidebar
        sidebar_layout.addWidget(self.employee_btn)
        sidebar_layout.addWidget(self.payroll_btn)
        sidebar_layout.addWidget(self.reports_btn)
        
        # Add spacer at the bottom
        sidebar_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Create stacked widget for main content
        self.stack = QStackedWidget()
        self.stack.addWidget(EmployeeForm(self.employee_controller))
        self.stack.addWidget(PayrollForm(self.payroll_controller, self.employee_controller))
        self.stack.addWidget(ReportsForm(self.employee_controller, self.payroll_controller))
        
        # Add sidebar and stack to main layout
        layout.addWidget(sidebar)
        layout.addWidget(self.stack)
        
        # Connect buttons
        self.employee_btn.clicked.connect(lambda: self.switch_page(0))
        self.payroll_btn.clicked.connect(lambda: self.switch_page(1))
        self.reports_btn.clicked.connect(lambda: self.switch_page(2))
        
        # Set initial page
        self.employee_btn.setChecked(True)
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
    main()
