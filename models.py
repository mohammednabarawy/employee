from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Employee:
    id: Optional[int]
    name: str
    dob: datetime
    gender: str
    phone: str
    email: str
    position: str
    department: str
    hire_date: datetime
    salary_type: str
    basic_salary: float
    bank_account: str
    photo_path: Optional[str] = None

@dataclass
class Salary:
    id: Optional[int]
    employee_id: int
    base_salary: float
    bonuses: float
    deductions: float
    overtime_pay: float
    total_salary: float

@dataclass
class SalaryPayment:
    id: Optional[int]
    employee_id: int
    amount_paid: float
    payment_date: datetime
    payment_mode: str
    status: str = 'Pending'

@dataclass
class User:
    id: Optional[int]
    username: str
    password: str
    role: str
    created_at: Optional[datetime] = None
