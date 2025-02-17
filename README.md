# Employee Management System

A comprehensive desktop application for managing employees, salaries, and payroll using Python, PyQt5, and SQLite3.

## Features

- Employee Management (CRUD operations)
- Salary Structure & Payment Management
- Payroll Management & Salary Payment History
- Reports & Data Export (Excel/PDF)
- User Authentication & Role Management

## Installation

1. Clone the repository
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
EmployeeManagement/
│── main.py               # Main entry point
│── database.py          # Database connection and queries
│── models.py            # Database models
│── ui/                  # UI files
│── controllers/         # Business logic
│── utils/              # Utility functions
│── assets/             # Images and icons
└── config.py           # Configuration settings
```

## License

MIT License
