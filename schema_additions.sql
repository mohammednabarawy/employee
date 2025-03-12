
-- Departments
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ar TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positions
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    name_ar TEXT,
    department_id INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Modify employees table to include department and position
DROP TABLE IF EXISTS employees;
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    employee_type_id INTEGER NOT NULL,
    department_id INTEGER,
    position_id INTEGER,
    status TEXT NOT NULL CHECK(status IN ('active', 'terminated')),
    FOREIGN KEY (employee_type_id) REFERENCES employee_types(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE SET NULL
);