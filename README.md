# Employee Management System

A comprehensive desktop application for managing employees, salaries, payroll, and attendance using Python, PyQt5, and SQLite3. The system is designed for small to medium-sized businesses with a focus on ease of use and comprehensive reporting.

## Features

### Employee Management
- Complete employee information management (personal details, contact information, job details)
- Employee document management (contracts, certificates, IDs)
- Employee status tracking (active, inactive, on leave)
- Department and position management
- Employee search and filtering capabilities

### Salary and Payroll Management
- Flexible salary structure configuration (basic salary, allowances, deductions)
- Monthly payroll processing with automatic calculations
- Payroll approval workflow
- Salary payment tracking and history
- Bank transfer and cash payment support
- Payslip generation and printing

### Attendance Tracking
- Daily attendance recording
- Absence and leave management
- Attendance reports and statistics
- Attendance visualization with charts

### Financial Management
- Salary budget tracking
- Department cost analysis
- Payroll expense reports
- Financial forecasting

### Reporting System
- Comprehensive reporting module with various report types:
  - Employee reports (active, by department, by position)
  - Payroll reports (monthly, quarterly, annual)
  - Attendance reports
  - Financial reports
- Export capabilities to multiple formats (Excel, CSV, PDF)
- Customizable report parameters

### System Administration
- User management with role-based access control
- Database backup and restore functionality
- Company information management
- System settings and preferences
- Data import/export utilities

### User Interface
- Modern, intuitive Arabic interface
- Dashboard with key metrics and visualizations
- Responsive design for different screen sizes
- Dark/light theme support

## Technical Details

### Architecture
- Model-View-Controller (MVC) architecture
- Modular design for easy maintenance and extension
- SQLite database for data storage
- PyQt5 for the graphical user interface

### Database Schema
- Employees table: Stores employee personal and professional information
- Departments table: Manages department structure
- Positions table: Tracks job positions and titles
- Salary_structures table: Defines salary components
- Payroll_entries table: Records monthly payroll calculations
- Payments table: Tracks salary payments
- Attendance table: Records daily attendance
- Users table: Manages system users and permissions
- Company_info table: Stores company details for reports and payslips

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/employee-management-system.git
cd employee-management-system
```

2. Create a virtual environment:
```bash
python -m venv venv
```

3. Activate the virtual environment:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Project Structure

```
employee/
│── main.py                      # Main entry point
│── requirements.txt             # Project dependencies
│── employee.db                  # SQLite database file
│
├── database/                    # Database related files
│   ├── database.py              # Database connection and management
│   └── schema.py                # Database schema definitions
│
├── controllers/                 # Business logic controllers
│   ├── employee_controller.py   # Employee management logic
│   ├── payroll_controller.py    # Payroll processing logic
│   ├── attendance_controller.py # Attendance tracking logic
│   └── user_controller.py       # User management logic
│
├── ui/                          # User interface components
│   ├── dashboard.py             # Main dashboard
│   ├── employee_form.py         # Employee management forms
│   ├── payroll_form.py          # Payroll processing interface
│   ├── reports_form.py          # Reporting interface
│   ├── payslip_template.py      # Payslip generation templates
│   └── login_dialog.py          # Authentication interface
│
└── utils/                       # Utility functions and helpers
    ├── export_utils.py          # Data export utilities
    ├── date_utils.py            # Date handling utilities
    ├── company_info.py          # Company information management
    ├── backup_manager.py        # Database backup utilities
    └── licensing.py             # License management
```

## User Guide

### First-time Setup
1. Launch the application
2. Set up company information (name, commercial register, tax number)
3. Create departments and positions
4. Add employees and their details
5. Configure salary structures

### Regular Operations
1. Record daily attendance
2. Process monthly payroll
3. Generate and print payslips
4. Create and export reports

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact [your-email@example.com](mailto:your-email@example.com)
