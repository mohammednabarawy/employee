class Styles:
    LIGHT_THEME = """
        /* Global Styles */
        QMainWindow, QDialog {
            background-color: #f5f6fa;
        }
        
        QWidget {
            font-family: 'Segoe UI', Arial;
            font-size: 12px;
        }
        
        /* Sidebar Styles */
        QFrame#sidebar {
            background-color: #2c3e50;
            border-radius: 10px;
            margin: 5px;
        }
        
        QFrame#sidebar QPushButton {
            color: white;
            border: none;
            text-align: left;
            padding: 12px 15px;
            margin: 3px 5px;
            border-radius: 5px;
            font-size: 13px;
        }
        
        QFrame#sidebar QPushButton:hover {
            background-color: #34495e;
        }
        
        QFrame#sidebar QPushButton:checked {
            background-color: #3498db;
            font-weight: bold;
        }
        
        /* Form Styles */
        QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 8px;
            border: 1px solid #dcdde1;
            border-radius: 5px;
            background-color: white;
        }
        
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
            border: 2px solid #3498db;
        }
        
        QLineEdit:disabled {
            background-color: #f1f2f6;
        }
        
        /* Button Styles */
        QPushButton {
            padding: 8px 15px;
            border-radius: 5px;
            border: none;
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #2475a7;
        }
        
        QPushButton:disabled {
            background-color: #bdc3c7;
        }
        
        QPushButton#deleteButton {
            background-color: #e74c3c;
        }
        
        QPushButton#deleteButton:hover {
            background-color: #c0392b;
        }
        
        /* Table Styles */
        QTableWidget {
            background-color: white;
            alternate-background-color: #f8f9fa;
            border: 1px solid #dcdde1;
            border-radius: 5px;
            gridline-color: #ecf0f1;
        }
        
        QTableWidget::item {
            padding: 5px;
        }
        
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #2c3e50;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        
        /* Scroll Bar Styles */
        QScrollBar:vertical {
            border: none;
            background-color: #f1f2f6;
            width: 10px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #bdc3c7;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #95a5a6;
        }
        
        /* Card Styles */
        QFrame#card {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
        }
        
        QFrame#card QLabel {
            color: #2c3e50;
        }
        
        /* Search Box Styles */
        QLineEdit#searchBox {
            padding: 10px;
            padding-left: 35px;
            border: 2px solid #dcdde1;
            border-radius: 20px;
            background-color: white;
            font-size: 13px;
        }
        
        QLineEdit#searchBox:focus {
            border: 2px solid #3498db;
        }
        
        /* Tab Styles */
        QTabWidget::pane {
            border: 1px solid #dcdde1;
            border-radius: 5px;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #f1f2f6;
            padding: 8px 15px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
        }
        
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
        
        /* Group Box Styles */
        QGroupBox {
            border: 1px solid #dcdde1;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
            background-color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            color: #2c3e50;
        }
    """
    
    DARK_THEME = """
        /* Global Styles */
        QMainWindow, QDialog {
            background-color: #1e272e;
        }
        
        QWidget {
            font-family: 'Segoe UI', Arial;
            font-size: 12px;
            color: #ecf0f1;
        }
        
        /* Sidebar Styles */
        QFrame#sidebar {
            background-color: #2c3e50;
            border-radius: 10px;
            margin: 5px;
        }
        
        QFrame#sidebar QPushButton {
            color: white;
            border: none;
            text-align: left;
            padding: 12px 15px;
            margin: 3px 5px;
            border-radius: 5px;
            font-size: 13px;
        }
        
        QFrame#sidebar QPushButton:hover {
            background-color: #34495e;
        }
        
        QFrame#sidebar QPushButton:checked {
            background-color: #3498db;
            font-weight: bold;
        }
        
        /* Form Styles */
        QLineEdit, QDateEdit, QComboBox, QSpinBox, QDoubleSpinBox {
            padding: 8px;
            border: 1px solid #34495e;
            border-radius: 5px;
            background-color: #2c3e50;
            color: white;
        }
        
        QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
            border: 2px solid #3498db;
        }
        
        QLineEdit:disabled {
            background-color: #2c3e50;
            color: #7f8c8d;
        }
        
        /* Button Styles */
        QPushButton {
            padding: 8px 15px;
            border-radius: 5px;
            border: none;
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #2475a7;
        }
        
        QPushButton:disabled {
            background-color: #34495e;
            color: #7f8c8d;
        }
        
        QPushButton#deleteButton {
            background-color: #c0392b;
        }
        
        QPushButton#deleteButton:hover {
            background-color: #a93226;
        }
        
        /* Table Styles */
        QTableWidget {
            background-color: #2c3e50;
            alternate-background-color: #34495e;
            border: 1px solid #34495e;
            border-radius: 5px;
            gridline-color: #2c3e50;
            color: white;
        }
        
        QTableWidget::item {
            padding: 5px;
        }
        
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #1e272e;
            color: white;
            padding: 8px;
            border: none;
            font-weight: bold;
        }
        
        /* Scroll Bar Styles */
        QScrollBar:vertical {
            border: none;
            background-color: #2c3e50;
            width: 10px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: #34495e;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #3498db;
        }
        
        /* Card Styles */
        QFrame#card {
            background-color: #2c3e50;
            border-radius: 10px;
            padding: 15px;
        }
        
        QFrame#card QLabel {
            color: white;
        }
        
        /* Search Box Styles */
        QLineEdit#searchBox {
            padding: 10px;
            padding-left: 35px;
            border: 2px solid #34495e;
            border-radius: 20px;
            background-color: #2c3e50;
            color: white;
            font-size: 13px;
        }
        
        QLineEdit#searchBox:focus {
            border: 2px solid #3498db;
        }
        
        /* Tab Styles */
        QTabWidget::pane {
            border: 1px solid #34495e;
            border-radius: 5px;
            background-color: #2c3e50;
        }
        
        QTabBar::tab {
            background-color: #1e272e;
            padding: 8px 15px;
            margin-right: 2px;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            color: white;
        }
        
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
        
        /* Group Box Styles */
        QGroupBox {
            border: 1px solid #34495e;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
            background-color: #2c3e50;
            color: white;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 5px 10px;
            color: white;
        }
    """
