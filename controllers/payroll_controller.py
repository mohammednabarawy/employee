from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Union
from decimal import Decimal
from PyQt5.QtCore import QObject, pyqtSignal
from .employee_details_controller import EmployeeDetailsController

class PayrollController(QObject):
    payroll_generated = pyqtSignal(dict)
    payroll_approved = pyqtSignal(dict)
    payment_processed = pyqtSignal(dict)

    def __init__(self, database):
        super().__init__()
        self.db = database
        self.employee_details = EmployeeDetailsController(database)

    def create_payroll_period(self, year, month):
        """Create a new payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if period already exists
            cursor.execute("""
                SELECT id, status 
                FROM payroll_periods 
                WHERE period_year = ? AND period_month = ?
            """, (year, month))
            
            existing_period = cursor.fetchone()
            
            if existing_period:
                period_id, status = existing_period
                if status in ['draft', 'processing']:
                    # Period exists but is not finalized, we can use it
                    return True, period_id
                else:
                    # Period exists and is finalized
                    return False, "فترة الرواتب لهذا الشهر موجودة بالفعل وتم اعتمادها"
            
            # Calculate period dates
            import calendar
            from datetime import date
            
            # Get the first and last day of the month
            _, last_day = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            
            # Create new period
            cursor.execute("""
                INSERT INTO payroll_periods (
                    period_year, period_month,
                    start_date, end_date,
                    status
                ) VALUES (?, ?, ?, ?, 'draft')
            """, (year, month, start_date, end_date))
            
            period_id = cursor.lastrowid
            conn.commit()
            
            return True, period_id
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def generate_payroll(self, period_id):
        """Generate payroll entries for all active employees"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get period details
            cursor.execute("""
                SELECT period_year, period_month, start_date, end_date
                FROM payroll_periods
                WHERE id = ?
            """, (period_id,))

            period = cursor.fetchone()
            if not period:
                return False, "فترة الرواتب غير موجودة"

            period_year, period_month, start_date, end_date = period

            # Get active employees
            cursor.execute("""
                SELECT id 
                FROM employees 
                WHERE is_active = 1
            """)

            employees = cursor.fetchall()
            entries = []

            for (employee_id,) in employees:
                # Get employee salary details
                success, salary_info = self.employee_details.get_employee_details(employee_id)
                if not success:
                    continue

                basic_salary = salary_info['basic_salary']
                total_allowances = sum(
                    comp['value'] if not comp['is_percentage']
                    else basic_salary * comp['percentage'] / 100
                    for comp in salary_info['salary_components']
                    if comp['type'] == 'allowance'
                )

                total_deductions = sum(
                    comp['value'] if not comp['is_percentage']
                    else basic_salary * comp['percentage'] / 100
                    for comp in salary_info['salary_components']
                    if comp['type'] == 'deduction'
                )

                # Calculate working days
                working_days = self._calculate_working_days(
                    employee_id, 
                    start_date, 
                    end_date
                )

                # Apply any adjustments effective in this period
                adjustments = [
                    adj for adj in salary_info['salary_adjustments']
                    if (
                        adj['status'] == 'approved' and
                        adj['effective_date'] <= end_date and
                        (not adj['end_date'] or adj['end_date'] >= start_date)
                    )
                ]

                total_adjustments = sum(adj['amount'] for adj in adjustments)

                # Calculate net salary
                net_salary = (
                    basic_salary + 
                    total_allowances - 
                    total_deductions +
                    total_adjustments
                )

                # Prorate salary if needed
                if working_days < self._get_period_working_days(period_year, period_month):
                    net_salary = (net_salary / self._get_period_working_days(period_year, period_month)) * working_days

                # Insert payroll entry
                cursor.execute("""
                    INSERT INTO payroll_entries (
                        payroll_period_id, employee_id,
                        basic_salary, total_allowances,
                        total_deductions, total_adjustments,
                        working_days, net_salary,
                        payment_status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
                """, (
                    period_id, employee_id,
                    basic_salary, total_allowances,
                    total_deductions, total_adjustments,
                    working_days, net_salary
                ))

                entry_id = cursor.lastrowid

                # Add payroll components
                for comp in salary_info['salary_components']:
                    value = (
                        comp['value'] if not comp['is_percentage']
                        else basic_salary * comp['percentage'] / 100
                    )

                    cursor.execute("""
                        INSERT INTO payroll_entry_components (
                            entry_id, component_id,
                            amount, created_at
                        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (entry_id, comp['id'], value))

                entries.append({
                    'id': entry_id,
                    'employee_id': employee_id,
                    'basic_salary': basic_salary,
                    'total_allowances': total_allowances,
                    'total_deductions': total_deductions,
                    'total_adjustments': total_adjustments,
                    'working_days': working_days,
                    'net_salary': net_salary
                })

            conn.commit()
            return True, entries

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    def get_payroll_entries(self, period_id):
        """Get all payroll entries for a specific period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pe.id,
                    pe.employee_id,
                    e.name as employee_name,
                    d.name as department_name,
                    pe.basic_salary,
                    pe.total_allowances,
                    pe.total_deductions,
                    pe.net_salary,
                    pe.payment_method,
                    pm.name_ar as payment_method_name,
                    pe.payment_status,
                    pe.payment_date,
                    pe.notes
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                LEFT JOIN employment_details ed ON e.id = ed.employee_id
                LEFT JOIN departments d ON ed.department_id = d.id
                LEFT JOIN payment_methods pm ON pe.payment_method = pm.id
                WHERE pe.payroll_period_id = ?
                ORDER BY e.name
            """, (period_id,))
            
            columns = [description[0] for description in cursor.description]
            entries = []
            
            for row in cursor.fetchall():
                entry = dict(zip(columns, row))
                entries.append(entry)
            
            return True, entries
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_payroll_entries_new(self, period_id):
        """Get all entries for a payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pe.id,
                    pe.employee_id,
                    e.name as employee_name,
                    d.name as department_name,
                    pe.basic_salary,
                    pe.total_allowances,
                    pe.total_deductions,
                    pe.net_salary,
                    pe.payment_method,
                    pm.name as payment_method_name,
                    pe.payment_status,
                    pe.payment_date,
                    pe.notes
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN payment_methods pm ON pe.payment_method = pm.id
                WHERE pe.payroll_period_id = ?
                ORDER BY e.name
            """, (period_id,))
            
            entries = []
            for row in cursor.fetchall():
                entry = {
                    'id': row[0],
                    'employee_id': row[1],
                    'employee_name': row[2],
                    'department_name': row[3],
                    'basic_salary': row[4],
                    'total_allowances': row[5],
                    'total_deductions': row[6],
                    'net_salary': row[7],
                    'payment_method': row[8],
                    'payment_method_name': row[9],
                    'payment_status': row[10],
                    'payment_date': row[11],
                    'notes': row[12]
                }
                entries.append(entry)
            
            return True, entries
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_period_status(self, period_id):
        """Get the status of a payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT status FROM payroll_periods
                WHERE id = ?
            """, (period_id,))
            
            result = cursor.fetchone()
            if result:
                return True, result[0]
            return False, "فترة الرواتب غير موجودة"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_entry_components(self, entry_id):
        """Get all components for a payroll entry"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pec.id,
                    pec.component_id,
                    sc.name,
                    sc.type,
                    pec.value
                FROM payroll_entry_components pec
                JOIN salary_components sc ON pec.component_id = sc.id
                WHERE pec.payroll_entry_id = ?
                ORDER BY sc.type, sc.name
            """, (entry_id,))
            
            components = {
                'allowances': [],
                'deductions': []
            }
            
            for row in cursor.fetchall():
                component = {
                    'id': row[0],
                    'component_id': row[1],
                    'name': row[2],
                    'value': row[4]
                }
                if row[3] == 'allowance':
                    components['allowances'].append(component)
                else:
                    components['deductions'].append(component)
            
            return True, components
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def update_entry_component(self, entry_id, component_id, value):
        """Update a component value for a payroll entry"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Update component value
            cursor.execute("""
                UPDATE payroll_entry_components
                SET value = ?
                WHERE payroll_entry_id = ? AND component_id = ?
            """, (value, entry_id, component_id))
            
            # Recalculate totals
            cursor.execute("""
                UPDATE payroll_entries 
                SET total_allowances = (
                    SELECT COALESCE(SUM(pec.value), 0)
                    FROM payroll_entry_components pec
                    JOIN salary_components sc ON pec.component_id = sc.id
                    WHERE pec.payroll_entry_id = ? AND sc.type = 'allowance'
                ),
                total_deductions = (
                    SELECT COALESCE(SUM(pec.value), 0)
                    FROM payroll_entry_components pec
                    JOIN salary_components sc ON pec.component_id = sc.id
                    WHERE pec.payroll_entry_id = ? AND sc.type = 'deduction'
                )
                WHERE id = ?
            """, (entry_id, entry_id, entry_id))
            
            # Update net salary
            cursor.execute("""
                UPDATE payroll_entries 
                SET net_salary = basic_salary + total_allowances - total_deductions
                WHERE id = ?
            """, (entry_id,))
            
            conn.commit()
            return True, "تم تحديث المكون بنجاح"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def approve_payroll(self, period_id, approved_by):
        """Approve a payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if period exists and is in draft state
            cursor.execute("""
                SELECT status, 
                       (SELECT COUNT(*) FROM payroll_entries WHERE payroll_period_id = ?) as entry_count
                FROM payroll_periods 
                WHERE id = ?
            """, (period_id, period_id))
            
            result = cursor.fetchone()
            if not result:
                return False, "فترة الرواتب غير موجودة"
                
            status, entry_count = result
            
            if status != 'draft':
                return False, "لا يمكن اعتماد فترة الرواتب في هذه الحالة"
                
            if entry_count == 0:
                return False, "لا يمكن اعتماد فترة رواتب فارغة. يرجى إضافة موظفين أولاً"
            
            # Check if approved_at column exists
            cursor.execute("PRAGMA table_info(payroll_periods)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Prepare SQL based on available columns
            if 'approved_at' in columns:
                # Update period status with approved_at timestamp
                cursor.execute("""
                    UPDATE payroll_periods 
                    SET status = 'approved',
                        approved_by = ?,
                        approved_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (approved_by, period_id))
            else:
                # Update period status without approved_at timestamp
                cursor.execute("""
                    UPDATE payroll_periods 
                    SET status = 'approved',
                        approved_by = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (approved_by, period_id))
            
            # Update all entries to approved status
            cursor.execute("""
                UPDATE payroll_entries 
                SET payment_status = 'approved',
                    updated_at = CURRENT_TIMESTAMP
                WHERE payroll_period_id = ?
            """, (period_id,))
            
            conn.commit()
            return True, "تم اعتماد كشف الرواتب بنجاح"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def process_payroll(self, period_id, processed_by):
        """Process (pay) a payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if period exists and is approved
            cursor.execute("""
                SELECT status FROM payroll_periods WHERE id = ?
            """, (period_id,))
            
            period = cursor.fetchone()
            if not period:
                return False, "فترة الرواتب غير موجودة"
            if period[0] != 'approved':
                return False, "يجب اعتماد كشف الرواتب أولاً"
            
            # Check if processed_at and processed_by columns exist
            cursor.execute("PRAGMA table_info(payroll_periods)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Prepare SQL based on available columns
            if 'processed_at' in columns and 'processed_by' in columns:
                # Update with processed_at and processed_by
                cursor.execute("""
                    UPDATE payroll_periods 
                    SET status = 'processed',
                        processed_by = ?,
                        processed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (processed_by, period_id))
            else:
                # Update without processed_at and processed_by
                cursor.execute("""
                    UPDATE payroll_periods 
                    SET status = 'processed',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (period_id,))
            
            cursor.execute("""
                UPDATE payroll_entries 
                SET payment_status = 'paid',
                    payment_date = CURRENT_TIMESTAMP
                WHERE payroll_period_id = ?
            """, (period_id,))
            
            conn.commit()
            return True, "تم صرف الرواتب بنجاح"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_period_summary(self, period_id):
        """Get summary statistics for a payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_employees,
                    SUM(basic_salary) as total_basic,
                    SUM(total_allowances) as total_allowances,
                    SUM(total_deductions) as total_deductions,
                    SUM(net_salary) as total_net
                FROM payroll_entries
                WHERE payroll_period_id = ?
            """, (period_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, "فترة الرواتب غير موجودة"
                
            summary = {
                'total_employees': row[0],
                'total_basic': row[1],
                'total_allowances': row[2],
                'total_deductions': row[3],
                'total_net': row[4]
            }
            
            # Get payment method breakdown
            cursor.execute("""
                SELECT 
                    COALESCE(pm.name, 'غير محدد') as method,
                    COUNT(*) as count,
                    SUM(pe.net_salary) as total
                FROM payroll_entries pe
                LEFT JOIN payment_methods pm ON pe.payment_method = pm.id
                WHERE pe.payroll_period_id = ?
                GROUP BY pe.payment_method
            """, (period_id,))
            
            summary['payment_methods'] = [
                {'method': row[0], 'count': row[1], 'total': row[2]}
                for row in cursor.fetchall()
            ]
            
            return True, summary
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_employee_history(self, employee_id, limit=12):
        """Get payroll history for an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pp.year,
                    pp.month,
                    pe.basic_salary,
                    pe.total_allowances,
                    pe.total_deductions,
                    pe.net_salary,
                    pe.payment_status,
                    pe.payment_date
                FROM payroll_entries pe
                JOIN payroll_periods pp ON pe.payroll_period_id = pp.id
                WHERE pe.employee_id = ?
                ORDER BY pp.year DESC, pp.month DESC
                LIMIT ?
            """, (employee_id, limit))
            
            history = [
                {
                    'year': row[0],
                    'month': row[1],
                    'basic_salary': row[2],
                    'total_allowances': row[3],
                    'total_deductions': row[4],
                    'net_salary': row[5],
                    'payment_status': row[6],
                    'payment_date': row[7]
                }
                for row in cursor.fetchall()
            ]
            
            return True, history
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_period_id(self, year, month):
        """Get payroll period ID for a specific year and month"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id FROM payroll_periods
                WHERE period_year = ? AND period_month = ?
            """, (year, month))
            
            result = cursor.fetchone()
            if result:
                return True, result[0]
            return False, "فترة الرواتب غير موجودة"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_employee_payslip(self, entry_id):
        """Get detailed payslip for an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # First get the basic entry data
            cursor.execute("""
                SELECT 
                    pe.*,
                    e.name as employee_name,
                    e.name_ar as employee_name_ar,
                    pp.period_year,
                    pp.period_month,
                    pp.start_date,
                    pp.end_date,
                    pm.name_ar as payment_method_name
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                JOIN payroll_periods pp ON pe.payroll_period_id = pp.id
                LEFT JOIN payment_methods pm ON pe.payment_method = pm.id
                WHERE pe.id = ?
            """, (entry_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, "Entry not found"
                
            columns = [description[0] for description in cursor.description]
            payslip = dict(zip(columns, row))
            
            # Try to get department and position info if available
            try:
                cursor.execute("""
                    SELECT 
                        d.name as department_name,
                        p.title as position_title
                    FROM employees e
                    LEFT JOIN employment_details ed ON e.id = ed.employee_id
                    LEFT JOIN departments d ON ed.department_id = d.id
                    LEFT JOIN positions p ON ed.position_id = p.id
                    WHERE e.id = ?
                """, (payslip.get('employee_id'),))
                
                dept_row = cursor.fetchone()
                if dept_row:
                    payslip['department_name'] = dept_row[0]
                    payslip['position_title'] = dept_row[1]
            except Exception:
                # If this query fails, we'll just continue without this info
                payslip['department_name'] = ''
                payslip['position_title'] = ''
            
            # Try to get bank details if available
            try:
                cursor.execute("""
                    SELECT 
                        bank_name,
                        bank_account,
                        iban
                    FROM employment_details
                    WHERE employee_id = ?
                """, (payslip.get('employee_id'),))
                
                bank_row = cursor.fetchone()
                if bank_row:
                    payslip['bank_name'] = bank_row[0]
                    payslip['bank_account'] = bank_row[1]
                    payslip['iban'] = bank_row[2]
            except Exception:
                # If this query fails, we'll just continue without this info
                payslip['bank_name'] = ''
                payslip['bank_account'] = ''
                payslip['iban'] = ''
            
            # Get component details - first try payroll_entry_details
            payslip['components'] = []
            try:
                cursor.execute("""
                    SELECT 
                        ped.amount,
                        ped.type,
                        sc.name,
                        sc.name_ar
                    FROM payroll_entry_details ped
                    JOIN salary_components sc ON ped.component_id = sc.id
                    WHERE ped.payroll_entry_id = ?
                    ORDER BY ped.type, sc.name
                """, (entry_id,))
                
                for amount, type_, name, name_ar in cursor.fetchall():
                    payslip['components'].append({
                        'amount': amount,
                        'type': type_,
                        'name': name,
                        'name_ar': name_ar
                    })
            except Exception:
                # If this fails, try payroll_entry_components instead
                try:
                    cursor.execute("""
                        SELECT 
                            pec.value as amount,
                            sc.type,
                            sc.name,
                            sc.name_ar
                        FROM payroll_entry_components pec
                        JOIN salary_components sc ON pec.component_id = sc.id
                        WHERE pec.payroll_entry_id = ?
                        ORDER BY sc.type, sc.name
                    """, (entry_id,))
                    
                    for amount, type_, name, name_ar in cursor.fetchall():
                        payslip['components'].append({
                            'amount': amount,
                            'type': type_,
                            'name': name,
                            'name_ar': name_ar
                        })
                except Exception:
                    # If both fail, we'll just use the totals from the payroll_entries table
                    if float(payslip.get('total_allowances', 0)) > 0:
                        payslip['components'].append({
                            'amount': payslip.get('total_allowances', 0),
                            'type': 'allowance',
                            'name': 'Total Allowances',
                            'name_ar': 'إجمالي البدلات'
                        })
                    
                    if float(payslip.get('total_deductions', 0)) > 0:
                        payslip['components'].append({
                            'amount': payslip.get('total_deductions', 0),
                            'type': 'deduction',
                            'name': 'Total Deductions',
                            'name_ar': 'إجمالي الاستقطاعات'
                        })
            
            return True, payslip
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_salary_components(self, component_type=None):
        """Get all salary components or filter by type"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, name, name_ar, type, is_taxable,
                       is_percentage, value, percentage,
                       description, is_active
                FROM salary_components
                WHERE is_active = 1
            """
            
            params = []
            if component_type:
                query += " AND type = ?"
                params.append(component_type)
                
            query += " ORDER BY type, name_ar"
            
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            components = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            return True, components
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def add_salary_component(self, data):
        """Add a new salary component"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO salary_components (
                    name, name_ar, type, is_taxable,
                    is_percentage, value, percentage,
                    description, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data['name'], data['name_ar'], data['type'],
                data['is_taxable'], data['is_percentage'],
                None if data['is_percentage'] else data['value'],
                data['value'] if data['is_percentage'] else None,
                data.get('description', '')
            ))
            
            conn.commit()
            return True, cursor.lastrowid
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def update_salary_component(self, component_id, data):
        """Update an existing salary component"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE salary_components SET
                    name = ?, name_ar = ?, type = ?,
                    is_taxable = ?, is_percentage = ?,
                    value = ?, percentage = ?,
                    description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data['name'], data['name_ar'], data['type'],
                data['is_taxable'], data['is_percentage'],
                None if data['is_percentage'] else data['value'],
                data['value'] if data['is_percentage'] else None,
                data.get('description', ''), component_id
            ))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def delete_salary_component(self, component_id):
        """Soft delete a salary component"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if component is in use
            cursor.execute("""
                SELECT COUNT(*) FROM employee_salary_components
                WHERE component_id = ? AND is_active = 1
            """, (component_id,))
            
            if cursor.fetchone()[0] > 0:
                return False, "لا يمكن حذف هذا العنصر لأنه مستخدم في رواتب الموظفين"
            
            cursor.execute("""
                UPDATE salary_components SET
                    is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (component_id,))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_employee_salary(self, employee_id):
        """Get employee's basic salary"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT basic_salary
                FROM employees
                WHERE id = ?
            """, (employee_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, "الموظف غير موجود"
                
            return True, {'basic_salary': row[0] or 0}
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def update_employee_basic_salary(self, employee_id, basic_salary):
        """Update employee's basic salary"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE employees SET
                    basic_salary = ?
                WHERE id = ?
            """, (basic_salary, employee_id))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_employee_components(self, employee_id, component_type=None):
        """Get all salary components for an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    esc.id, sc.name, sc.name_ar, sc.type,
                    sc.is_taxable, sc.is_percentage,
                    COALESCE(esc.value, sc.value) as value,
                    COALESCE(esc.percentage, sc.percentage) as percentage,
                    esc.start_date, esc.end_date, esc.is_active
                FROM employee_salary_components esc
                JOIN salary_components sc ON esc.component_id = sc.id
                WHERE esc.employee_id = ? AND sc.is_active = 1
            """
            
            params = [employee_id]
            if component_type:
                query += " AND sc.type = ?"
                params.append(component_type)
                
            query += " ORDER BY sc.type, sc.name_ar"
            
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            components = []
            for row in cursor.fetchall():
                component = dict(zip(columns, row))
                component['start_date'] = datetime.strptime(
                    component['start_date'], '%Y-%m-%d'
                ).date()
                if component['end_date']:
                    component['end_date'] = datetime.strptime(
                        component['end_date'], '%Y-%m-%d'
                    ).date()
                components.append(component)
            
            return True, components
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def add_employee_component(self, data):
        """Add a salary component to an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get component details
            cursor.execute("""
                SELECT is_percentage FROM salary_components
                WHERE id = ?
            """, (data['component_id'],))
            
            row = cursor.fetchone()
            if not row:
                return False, "عنصر الراتب غير موجود"
                
            is_percentage = row[0]
            
            cursor.execute("""
                INSERT INTO employee_salary_components (
                    employee_id, component_id,
                    value, percentage, start_date, end_date,
                    is_active
                ) VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (
                data['employee_id'], data['component_id'],
                None if is_percentage else data['value'],
                data['value'] if is_percentage else None,
                data['start_date'],
                data.get('end_date')
            ))
            
            conn.commit()
            return True, cursor.lastrowid
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def update_employee_component(self, component_id, data):
        """Update an employee's salary component"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get component details
            cursor.execute("""
                SELECT is_percentage FROM salary_components
                WHERE id = ?
            """, (data['component_id'],))
            
            row = cursor.fetchone()
            if not row:
                return False, "عنصر الراتب غير موجود"
                
            is_percentage = row[0]
            
            cursor.execute("""
                UPDATE employee_salary_components SET
                    value = ?, percentage = ?,
                    start_date = ?, end_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                None if is_percentage else data['value'],
                data['value'] if is_percentage else None,
                data['start_date'],
                data.get('end_date'),
                component_id
            ))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def delete_employee_component(self, component_id):
        """Remove a salary component from an employee"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE employee_salary_components SET
                    is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (component_id,))
            
            conn.commit()
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
            
    def get_employee_salary_summary(self, employee_id):
        """Get summary of employee's salary including all components"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get basic salary
            cursor.execute("""
                SELECT basic_salary
                FROM employees
                WHERE id = ?
            """, (employee_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, "الموظف غير موجود"
                
            basic_salary = row[0] or 0
            
            # Calculate total allowances
            cursor.execute("""
                SELECT SUM(
                    CASE 
                        WHEN sc.is_percentage = 1 
                        THEN ? * COALESCE(esc.percentage, sc.percentage) / 100
                        ELSE COALESCE(esc.value, sc.value)
                    END
                )
                FROM employee_salary_components esc
                JOIN salary_components sc ON esc.component_id = sc.id
                WHERE esc.employee_id = ?
                  AND esc.is_active = 1
                  AND sc.type = 'allowance'
                  AND sc.is_active = 1
                  AND (esc.end_date IS NULL OR esc.end_date >= CURRENT_DATE)
                  AND esc.start_date <= CURRENT_DATE
            """, (basic_salary, employee_id))
            
            total_allowances = cursor.fetchone()[0] or 0
            
            # Calculate total deductions
            cursor.execute("""
                SELECT SUM(
                    CASE 
                        WHEN sc.is_percentage = 1 
                        THEN ? * COALESCE(esc.percentage, sc.percentage) / 100
                        ELSE COALESCE(esc.value, sc.value)
                    END
                )
                FROM employee_salary_components esc
                JOIN salary_components sc ON esc.component_id = sc.id
                WHERE esc.employee_id = ?
                  AND esc.is_active = 1
                  AND sc.type = 'deduction'
                  AND sc.is_active = 1
                  AND (esc.end_date IS NULL OR esc.end_date >= CURRENT_DATE)
                  AND esc.start_date <= CURRENT_DATE
            """, (basic_salary, employee_id))
            
            total_deductions = cursor.fetchone()[0] or 0
            
            return True, {
                'basic_salary': basic_salary,
                'total_allowances': total_allowances,
                'total_deductions': total_deductions,
                'net_salary': basic_salary + total_allowances - total_deductions
            }
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_payment_methods(self):
        """Get all payment methods"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM payment_methods
                ORDER BY name_ar
            """)
            
            columns = [description[0] for description in cursor.description]
            methods = []
            
            for row in cursor.fetchall():
                method = dict(zip(columns, row))
                methods.append(method)
            
            return True, methods
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def add_employees_to_payroll(self, period_id, employee_ids):
        """Add employees to a payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if period exists and is editable
            cursor.execute("""
                SELECT status FROM payroll_periods WHERE id = ?
            """, (period_id,))
            period = cursor.fetchone()
            if not period:
                return False, "فترة الرواتب غير موجودة"
            if period[0] not in ['draft', 'processing']:
                return False, "لا يمكن إضافة موظفين لفترة رواتب معتمدة"
            
            # Get list of employees already in this period with their names
            cursor.execute("""
                SELECT pe.employee_id, e.name 
                FROM payroll_entries pe
                JOIN employees e ON e.id = pe.employee_id
                WHERE pe.payroll_period_id = ?
            """, (period_id,))
            existing_employees = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Filter out employees that are already in the payroll
            new_employees = []
            existing_names = []
            for emp_id in employee_ids:
                if emp_id in existing_employees:
                    existing_names.append(existing_employees[emp_id])
                else:
                    new_employees.append(emp_id)
            
            if not new_employees:
                existing_str = "، ".join(existing_names)
                return False, f"الموظفين التاليين موجودين بالفعل في كشف الرواتب: {existing_str}"
            
            # Add new employees
            for emp_id in new_employees:
                # Get employee basic salary and active components
                cursor.execute("""
                    SELECT basic_salary FROM employees WHERE id = ?
                """, (emp_id,))
                emp = cursor.fetchone()
                if not emp:
                    continue
                
                basic_salary = emp[0] or 0
                
                # Insert payroll entry
                cursor.execute("""
                    INSERT INTO payroll_entries (
                        payroll_period_id, employee_id, basic_salary,
                        total_allowances, total_deductions, net_salary,
                        payment_status
                    ) VALUES (?, ?, ?, 0, 0, ?, 'pending')
                """, (period_id, emp_id, basic_salary, basic_salary))
                
                entry_id = cursor.lastrowid
                
                # Calculate and insert allowances
                cursor.execute("""
                    SELECT sc.id, sc.is_percentage, sc.percentage, 
                           COALESCE(esc.value, sc.value) as value
                    FROM salary_components sc
                    LEFT JOIN employee_salary_components esc ON 
                        sc.id = esc.component_id AND 
                        esc.employee_id = ? AND 
                        esc.is_active = 1
                    WHERE sc.type = 'allowance' AND sc.is_active = 1
                """, (emp_id,))
                
                allowances = cursor.fetchall()
                total_allowances = 0
                
                for comp_id, is_percentage, percentage, value in allowances:
                    amount = (basic_salary * (percentage / 100)) if is_percentage else value
                    total_allowances += amount
                    
                    cursor.execute("""
                        INSERT INTO payroll_entry_components (
                            payroll_entry_id, component_id, value
                        ) VALUES (?, ?, ?)
                    """, (entry_id, comp_id, amount))
                
                # Calculate and insert deductions
                cursor.execute("""
                    SELECT sc.id, sc.is_percentage, sc.percentage, 
                           COALESCE(esc.value, sc.value) as value
                    FROM salary_components sc
                    LEFT JOIN employee_salary_components esc ON 
                        sc.id = esc.component_id AND 
                        esc.employee_id = ? AND 
                        esc.is_active = 1
                    WHERE sc.type = 'deduction' AND sc.is_active = 1
                """, (emp_id,))
                
                deductions = cursor.fetchall()
                total_deductions = 0
                
                for comp_id, is_percentage, percentage, value in deductions:
                    amount = (basic_salary * (percentage / 100)) if is_percentage else value
                    total_deductions += amount
                    
                    cursor.execute("""
                        INSERT INTO payroll_entry_components (
                            payroll_entry_id, component_id, value
                        ) VALUES (?, ?, ?)
                    """, (entry_id, comp_id, amount))
                
                # Update totals
                net_salary = basic_salary + total_allowances - total_deductions
                cursor.execute("""
                    UPDATE payroll_entries 
                    SET total_allowances = ?,
                        total_deductions = ?,
                        net_salary = ?
                    WHERE id = ?
                """, (total_allowances, total_deductions, net_salary, entry_id))
            
            conn.commit()
            return True, f"تم إضافة {len(new_employees)} موظف بنجاح"
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def update_payroll_entry(self, period_id, employee_id, values):
        """Update a payroll entry with new values"""
        try:
            # Validate inputs
            validation_result, message = self.validate_salary_transaction(values)
            if not validation_result:
                return False, message
            
            # Get current entry
            query = """
                SELECT pe.*, e.employee_type_id, et.name as employee_type
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                JOIN employee_types et ON e.employee_type_id = et.id
                WHERE pe.id = ?
            """
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (values['id'],))
                entry = cursor.fetchone()
                
                if not entry:
                    return False, "Payroll entry not found"
                
                if entry['payment_status'] == 'paid':
                    return False, "Cannot modify a paid entry"
                
                # Calculate new values
                new_values = {}
                for key, value in values.items():
                    if key in entry:
                        new_values[key] = float(entry[key]) + value
                
                # Update entry
                set_clause = ', '.join([f"{k} = ?" for k in new_values.keys()])
                values = list(new_values.values())
                values.extend([
                    values['notes'],
                    values['updated_by'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    values['id']
                ])
                
                update_query = f"""
                    UPDATE payroll_entries 
                    SET {set_clause},
                        adjustment_reason = ?,
                        updated_by = ?,
                        updated_at = ?
                    WHERE id = ?
                """
                
                cursor.execute(update_query, values)
                conn.commit()
                
                return True, "Payroll entry updated successfully"
                
        except Exception as e:
            return False, f"Error updating payroll entry: {str(e)}"

    def update_payroll_entry(
            self, 
            entry_id: int,
            adjustments: Dict[str, float],
            reason: str,
            updated_by: int
        ) -> Tuple[bool, str]:
        """Update a payroll entry with adjustments and sync with employee details"""
        try:
            # Validate adjustments
            validation_result, message = self.validate_salary_transaction(adjustments)
            if not validation_result:
                return False, message
            
            # Get current entry
            query = """
                SELECT pe.*, e.employee_type_id, et.name as employee_type
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                JOIN employee_types et ON e.employee_type_id = et.id
                WHERE pe.id = ?
            """
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (entry_id,))
                entry = cursor.fetchone()
                
                if not entry:
                    return False, "Payroll entry not found"
                
                if entry['payment_status'] == 'paid':
                    return False, "Cannot modify a paid entry"
                
                # Calculate new values
                new_values = {}
                for key, value in adjustments.items():
                    if key in entry:
                        new_values[key] = float(entry[key]) + value
                
                # Update entry
                set_clause = ', '.join([f"{k} = ?" for k in new_values.keys()])
                values = list(new_values.values())
                values.extend([
                    reason,
                    updated_by,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    entry_id
                ])
                
                update_query = f"""
                    UPDATE payroll_entries 
                    SET {set_clause},
                        adjustment_reason = ?,
                        updated_by = ?,
                        updated_at = ?
                    WHERE id = ?
                """
                
                cursor.execute(update_query, values)
                conn.commit()
                
                return True, "Payroll entry updated successfully"
                
        except Exception as e:
            return False, f"Error updating payroll entry: {str(e)}"

    def validate_salary_transaction(self, adjustments: Dict[str, float]) -> Tuple[bool, str]:
        """Validate salary adjustments before applying them"""
        try:
            # Check for negative values
            for key, value in adjustments.items():
                if value < 0 and key not in ['deductions', 'tax_deductions', 'social_insurance']:
                    return False, f"Invalid negative value for {key}"
            
            # Validate allowance types
            allowance_types = ['transportation', 'housing', 'medical']
            for key in adjustments.keys():
                if 'allowance' in key.lower() and key.split('_')[0] not in allowance_types:
                    return False, f"Invalid allowance type: {key}"
            
            return True, "Validation successful"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def get_employee_salary_history(self, employee_id, start_date=None, end_date=None):
        """Get salary history for an employee with optional date range"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    pe.id,
                    pp.period_year,
                    pp.period_month,
                    pe.basic_salary,
                    pe.total_allowances,
                    pe.total_deductions,
                    pe.total_adjustments,
                    pe.working_days,
                    pe.net_salary,
                    pe.payment_method,
                    pe.payment_status,
                    pe.payment_date,
                    pe.payment_reference,
                    pp.start_date,
                    pp.end_date
                FROM payroll_entries pe
                JOIN payroll_periods pp ON pe.payroll_period_id = pp.id
                WHERE pe.employee_id = ?
            """
            
            params = [employee_id]
            
            if start_date:
                query += " AND pp.start_date >= ?"
                params.append(start_date)
                
            if end_date:
                query += " AND pp.end_date <= ?"
                params.append(end_date)
                
            query += " ORDER BY pp.period_year DESC, pp.period_month DESC"
            
            cursor.execute(query, params)
            
            columns = [column[0] for column in cursor.description]
            history = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Get components for each entry
            for entry in history:
                cursor.execute("""
                    SELECT 
                        pec.id,
                        pec.component_id,
                        sc.name,
                        sc.name_ar,
                        sc.type,
                        pec.value
                    FROM payroll_entry_components pec
                    JOIN salary_components sc ON pec.component_id = sc.id
                    WHERE pec.payroll_entry_id = ?
                """, (entry['id'],))
                
                columns = [column[0] for column in cursor.description]
                components = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                entry['components'] = components
            
            return True, history
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def _calculate_working_days(
        self, 
        employee_id: int,
        start_date: date,
        end_date: date
    ) -> int:
        """Calculate actual working days for an employee in a period"""
        try:
            # Get attendance data from attendance controller
            from .attendance_controller import AttendanceController
            attendance_ctrl = AttendanceController(self.db)
            
            attendance_data = attendance_ctrl.get_attendance_data_for_period(
                employee_id,
                start_date,
                end_date
            )
            
            if attendance_data:
                return attendance_data.get('present_days', 0)
            
            # If no attendance data, return total working days minus weekends
            total_days = (end_date - start_date).days + 1
            weekend_days = self._count_weekends(start_date, end_date)
            return total_days - weekend_days
            
        except Exception:
            # In case of error, return full month working days
            return self._get_period_working_days(
                start_date.year,
                start_date.month
            )
        
    def _count_weekends(self, start_date, end_date):
        """Count weekend days between two dates"""
        from datetime import timedelta
        
        # Define weekend days (5=Saturday, 6=Sunday in Python's datetime)
        weekend_days = [5, 6]  # Adjust based on your country's weekend days
        
        count = 0
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() in weekend_days:
                count += 1
            current_date = current_date.replace(day=current_date.day + 1)
            
        return count
        
    def _get_period_working_days(self, year, month):
        """Get standard working days in a month (excluding weekends)"""
        import calendar
        from datetime import date, timedelta
        
        # Get the first and last day of the month
        _, last_day = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        # Count total days excluding weekends
        return (last_day - self._count_weekends(start_date, end_date))
        
    def get_payroll_periods(self):
        """Get all payroll periods ordered by year and month"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    period_year,
                    period_month,
                    start_date,
                    end_date,
                    status,
                    created_at
                FROM payroll_periods
                ORDER BY period_year DESC, period_month DESC
            """)
            
            periods = []
            for row in cursor.fetchall():
                period = {
                    'id': row[0],
                    'year': row[1],
                    'month': row[2],
                    'start_date': row[3],
                    'end_date': row[4],
                    'status': row[5],
                    'created_at': row[6]
                }
                periods.append(period)
            
            return True, periods
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def get_recent_entries(self, limit=5):
        """Get the most recent payroll entries across all periods
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent payroll entries with employee names
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    pe.id,
                    e.name as employee_name,
                    pe.basic_salary,
                    pe.net_salary,
                    pe.payment_date,
                    pe.payment_status
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                ORDER BY pe.payment_date DESC
                LIMIT ?
            """, (limit,))
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'id': row[0],
                    'employee_name': row[1],
                    'gross_salary': row[2],  # Using basic_salary as gross_salary
                    'net_salary': row[3],
                    'payment_date': row[4] if row[4] else '',
                    'payment_status': row[5] if row[5] else 'pending'
                })
                
            return entries
            
        except Exception as e:
            print(f"Error getting recent payroll entries: {str(e)}")
            return []
        finally:
            conn.close()

    def calculate_tax_deductions(self, gross_salary: Decimal) -> Decimal:
        """Calculate tax deductions using progressive tax brackets"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get tax brackets for current year
            current_year = date.today().year
            cursor.execute("""
                SELECT min_income, max_income, rate
                FROM tax_brackets
                WHERE tax_year = ?
                ORDER BY min_income
            """, (current_year,))
            
            brackets = cursor.fetchall()
            if not brackets:
                return Decimal('0')
                
            total_tax = Decimal('0')
            remaining_income = gross_salary
            
            for min_income, max_income, rate in brackets:
                if remaining_income <= 0:
                    break
                    
                # Calculate taxable amount in this bracket
                if max_income is None:
                    taxable_amount = remaining_income
                else:
                    taxable_amount = min(remaining_income, max_income - min_income)
                
                # Calculate tax for this bracket
                tax = taxable_amount * Decimal(str(rate))
                total_tax += tax
                
                # Update remaining income
                remaining_income -= taxable_amount
            
            return total_tax
            
        except Exception as e:
            self.log_error(f"Tax calculation error: {str(e)}")
            return Decimal('0')
        finally:
            conn.close()

    def calculate_social_insurance(self, basic_salary: Decimal) -> Decimal:
        """Calculate social insurance deductions"""
        try:
            # Get social insurance rates from configuration
            employee_rate = Decimal('0.11')  # 11% employee contribution
            max_insurable = Decimal('9000')  # Maximum insurable salary
            
            # Calculate insurable salary
            insurable_salary = min(basic_salary, max_insurable)
            
            # Calculate social insurance deduction
            return insurable_salary * employee_rate
            
        except Exception as e:
            self.log_error(f"Social insurance calculation error: {str(e)}")
            return Decimal('0')

    def calculate_overtime_pay(self, employee_id: int, period_id: int) -> Decimal:
        """Calculate overtime pay for the period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get period dates
            cursor.execute("""
                SELECT start_date, end_date
                FROM payroll_periods
                WHERE id = ?
            """, (period_id,))
            
            period = cursor.fetchone()
            if not period:
                return Decimal('0')
                
            start_date, end_date = period
            
            # Get overtime hours and rate
            cursor.execute("""
                SELECT SUM(hours), overtime_rate
                FROM overtime_records
                WHERE employee_id = ? 
                AND date BETWEEN ? AND ?
                AND status = 'approved'
            """, (employee_id, start_date, end_date))
            
            result = cursor.fetchone()
            if not result or not result[0]:
                return Decimal('0')
                
            total_hours, rate = result
            
            # Get hourly rate (assuming 22 working days per month, 8 hours per day)
            success, salary_info = self.get_employee_salary(employee_id)
            if not success:
                return Decimal('0')
                
            hourly_rate = Decimal(str(salary_info['basic_salary'])) / Decimal('176')  # 22 * 8
            
            # Calculate overtime pay
            return hourly_rate * Decimal(str(rate)) * Decimal(str(total_hours))
            
        except Exception as e:
            self.log_error(f"Overtime calculation error: {str(e)}")
            return Decimal('0')
        finally:
            conn.close()

    def calculate_salary_by_employee_type(
            self,
            employee_id: int,
            basic_salary: Decimal,
            period_id: int
        ) -> Tuple[Decimal, Dict[str, Decimal]]:
        """Calculate salary based on employee type with appropriate adjustments"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get employee type
            cursor.execute("""
                SELECT et.* 
                FROM employee_types et
                JOIN employees e ON e.employee_type_id = et.id
                WHERE e.id = ?
            """, (employee_id,))
            
            emp_type = cursor.fetchone()
            if not emp_type:
                return basic_salary, {}
                
            type_id, _, _, working_hours, overtime_mult, holiday_mult, prorated = emp_type
            
            # Get period dates
            cursor.execute("""
                SELECT start_date, end_date
                FROM payroll_periods
                WHERE id = ?
            """, (period_id,))
            
            period = cursor.fetchone()
            if not period:
                return basic_salary, {}
                
            start_date, end_date = period
            
            adjustments = {}
            
            # Calculate prorated salary for part-time
            if working_hours < 40:
                proration_factor = Decimal(str(working_hours)) / Decimal('40')
                basic_salary = basic_salary * proration_factor
                adjustments['proration'] = basic_salary * (Decimal('1') - proration_factor)
            
            # Calculate holiday pay
            cursor.execute("""
                SELECT COUNT(*) 
                FROM public_holidays 
                WHERE date BETWEEN ? AND ?
            """, (start_date, end_date))
            
            holiday_count = cursor.fetchone()[0]
            if holiday_count > 0 and holiday_mult > 1:
                daily_rate = basic_salary / Decimal('22')  # Assuming 22 working days
                holiday_pay = daily_rate * Decimal(str(holiday_count)) * (Decimal(str(holiday_mult)) - Decimal('1'))
                adjustments['holiday_pay'] = holiday_pay
            
            # Calculate leave deductions
            cursor.execute("""
                SELECT lt.paid, COUNT(*) as days
                FROM leave_requests lr
                JOIN leave_types lt ON lr.leave_type_id = lt.id
                WHERE lr.employee_id = ?
                AND lr.status = 'approved'
                AND lr.start_date BETWEEN ? AND ?
                GROUP BY lt.paid
            """, (employee_id, start_date, end_date))
            
            for paid, days in cursor.fetchall():
                if not paid:
                    daily_rate = basic_salary / Decimal('22')
                    leave_deduction = daily_rate * Decimal(str(days))
                    adjustments['unpaid_leave'] = leave_deduction
            
            # Calculate overtime with type-specific multiplier
            cursor.execute("""
                SELECT SUM(hours)
                FROM overtime_records
                WHERE employee_id = ?
                AND date BETWEEN ? AND ?
                AND status = 'approved'
            """, (employee_id, start_date, end_date))
            
            total_overtime = cursor.fetchone()[0] or 0
            if total_overtime > 0:
                hourly_rate = basic_salary / Decimal('176')  # 22 days * 8 hours
                overtime_pay = hourly_rate * Decimal(str(total_overtime)) * Decimal(str(overtime_mult))
                adjustments['overtime'] = overtime_pay
            
            return basic_salary, adjustments
            
        except Exception as e:
            self.log_error(f"Error calculating type-based salary: {str(e)}")
            return basic_salary, {}
        finally:
            conn.close()

    def calculate_tax_exempt_allowances(
            self,
            employee_id: int,
            basic_salary: Decimal
        ) -> Tuple[Decimal, Decimal]:
        """Calculate tax-exempt and taxable portions of allowances"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    sc.value,
                    sc.percentage,
                    tea.max_amount,
                    tea.max_percentage
                FROM salary_components sc
                LEFT JOIN tax_exempt_allowances tea ON sc.name = tea.name
                WHERE sc.type = 'allowance'
                AND sc.id IN (
                    SELECT component_id 
                    FROM employee_salary_components 
                    WHERE employee_id = ?
                    AND is_active = 1
                )
            """, (employee_id,))
            
            total_allowances = Decimal('0')
            tax_exempt_amount = Decimal('0')
            
            for value, percentage, max_amount, max_percentage in cursor.fetchall():
                # Calculate actual allowance amount
                if percentage:
                    allowance = basic_salary * Decimal(str(percentage)) / Decimal('100')
                else:
                    allowance = Decimal(str(value))
                
                total_allowances += allowance
                
                # Calculate tax exempt portion
                if max_amount and max_percentage:
                    # Use whichever gives the lower exempt amount
                    percent_exempt = allowance * Decimal(str(max_percentage)) / Decimal('100')
                    tax_exempt_amount += min(Decimal(str(max_amount)), percent_exempt)
                elif max_amount:
                    tax_exempt_amount += min(allowance, Decimal(str(max_amount)))
                elif max_percentage:
                    tax_exempt_amount += allowance * Decimal(str(max_percentage)) / Decimal('100')
            
            return total_allowances, tax_exempt_amount
            
        except Exception as e:
            self.log_error(f"Error calculating tax-exempt allowances: {str(e)}")
            return Decimal('0'), Decimal('0')
        finally:
            conn.close()
