# Employee Management System

## Project Structure

The project has been organized into the following structure:

```
employee/
├── assets/              # Images and other static assets
├── backups/             # Database backups
├── controllers/         # Business logic controllers
├── database/            # Database schema and connection management
│   └── migrations/      # Database migration scripts
├── docs/                # Documentation files
├── logs/                # Log files
├── temp/                # Temporary files
├── tests/               # Test scripts and test databases
├── ui/                  # User interface components
├── utils/               # Utility scripts for maintenance
└── main.py              # Main application entry point
```

## Key Components

- **Main Application**: `main.py` - The entry point for the application
- **Database**: `database/database.py` - Database connection and management
- **Controllers**: Various controllers in the `controllers/` directory that handle business logic
- **UI Components**: UI forms and dialogs in the `ui/` directory
- **Utilities**: Maintenance and helper scripts in the `utils/` directory

## Testing

Test scripts are located in the `tests/` directory:

- `test_salary_attendance.py` - Tests for salary and attendance functionality
- `test_schema.py` - Tests for database schema validation
- `stress_test.py` - Performance and stress testing

Run tests using:
```
python tests/run_tests.py
```

## Maintenance

Utility scripts for database maintenance are in the `utils/` directory:

- `database_maintenance.py` - Check and fix database schema issues
- `fix_database_schema.py` - Fix specific schema issues
- `check_database_schema.py` - Validate database schema

## Backup and Restore

The system automatically maintains backups in the `backups/` directory. Only the 5 most recent backups are kept.

To create a manual backup:
```
utils/create_backup.bat
```
