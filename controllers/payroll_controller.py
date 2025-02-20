from datetime import datetime, date
from PyQt5.QtCore import QObject, pyqtSignal
from decimal import Decimal

class PayrollController(QObject):
    payroll_generated = pyqtSignal(dict)
    payroll_approved = pyqtSignal(dict)
    payment_processed = pyqtSignal(dict)

    def __init__(self, database):
        super().__init__()
        self.db = database

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

    def create_period(self, year, month):
        """Create a new payroll period"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check if period already exists
            cursor.execute("""
                SELECT id, status FROM payroll_periods 
                WHERE year = ? AND month = ?
            """, (year, month))
            
            existing = cursor.fetchone()
            if existing:
                if existing[1] == 'draft':
                    return True, existing[0]
                return False, "فترة الرواتب موجودة بالفعل"
            
            # Create new period
            cursor.execute("""
                INSERT INTO payroll_periods (year, month, status)
                VALUES (?, ?, 'draft')
            """, (year, month))
            
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
            
            # Get all active employees
            cursor.execute("""
                SELECT e.id, e.name, ed.basic_salary, ed.salary_currency
                FROM employees e
                JOIN employment_details ed ON e.id = ed.employee_id
                WHERE ed.employee_status = 'نشط'
                  AND ed.basic_salary IS NOT NULL
                  AND ed.basic_salary > 0
            """)
            
            employees = cursor.fetchall()
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                for emp_id, name, basic_salary, currency in employees:
                    # Calculate allowances
                    cursor.execute("""
                        SELECT SUM(CASE 
                            WHEN sc.is_percentage = 1 THEN ? * (sc.percentage / 100)
                            ELSE COALESCE(esc.value, sc.value)
                        END) as total_allowances
                        FROM salary_components sc
                        LEFT JOIN employee_salary_components esc ON 
                            sc.id = esc.component_id AND 
                            esc.employee_id = ? AND 
                            esc.is_active = 1
                        WHERE sc.type = 'allowance' AND sc.is_active = 1
                    """, (basic_salary, emp_id))
                    
                    total_allowances = cursor.fetchone()[0] or 0
                    
                    # Calculate deductions
                    cursor.execute("""
                        SELECT SUM(CASE 
                            WHEN sc.is_percentage = 1 THEN ? * (sc.percentage / 100)
                            ELSE COALESCE(esc.value, sc.value)
                        END) as total_deductions
                        FROM salary_components sc
                        LEFT JOIN employee_salary_components esc ON 
                            sc.id = esc.component_id AND 
                            esc.employee_id = ? AND 
                            esc.is_active = 1
                        WHERE sc.type = 'deduction' AND sc.is_active = 1
                    """, (basic_salary, emp_id))
                    
                    total_deductions = cursor.fetchone()[0] or 0
                    
                    # Calculate net salary
                    net_salary = basic_salary + total_allowances - total_deductions
                    
                    # Insert payroll entry
                    cursor.execute("""
                        INSERT INTO payroll_entries (
                            payroll_period_id, employee_id, basic_salary,
                            total_allowances, total_deductions, net_salary,
                            payment_status
                        ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
                    """, (period_id, emp_id, basic_salary, total_allowances,
                          total_deductions, net_salary))
                    
                    entry_id = cursor.lastrowid
                    
                    # Insert component details
                    cursor.execute("""
                        INSERT INTO payroll_entry_details (
                            payroll_entry_id, component_id, amount, type
                        )
                        SELECT 
                            ?, sc.id,
                            CASE 
                                WHEN sc.is_percentage = 1 THEN ? * (sc.percentage / 100)
                                ELSE COALESCE(esc.value, sc.value)
                            END,
                            sc.type
                        FROM salary_components sc
                        LEFT JOIN employee_salary_components esc ON 
                            sc.id = esc.component_id AND 
                            esc.employee_id = ? AND 
                            esc.is_active = 1
                        WHERE sc.is_active = 1
                    """, (entry_id, basic_salary, emp_id))
                
                # Update period totals
                cursor.execute("""
                    UPDATE payroll_periods SET
                        total_amount = (
                            SELECT SUM(net_salary) 
                            FROM payroll_entries 
                            WHERE payroll_period_id = ?
                        ),
                        total_employees = (
                            SELECT COUNT(*) 
                            FROM payroll_entries 
                            WHERE payroll_period_id = ?
                        ),
                        status = 'processing'
                    WHERE id = ?
                """, (period_id, period_id, period_id))
                
                conn.commit()
                return True, "Payroll generated successfully"
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
                
        except Exception as e:
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
                    pe.*,
                    e.name as employee_name,
                    pm.name_ar as payment_method_name
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
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
            
            # Check if period exists and is in processing state
            cursor.execute("""
                SELECT status FROM payroll_periods WHERE id = ?
            """, (period_id,))
            
            period = cursor.fetchone()
            if not period:
                return False, "فترة الرواتب غير موجودة"
            if period[0] != 'processing':
                return False, "لا يمكن اعتماد فترة الرواتب في هذه الحالة"
            
            # Update period status
            cursor.execute("""
                UPDATE payroll_periods 
                SET status = 'approved',
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (approved_by, period_id))
            
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
            
            # Update period status and entries
            cursor.execute("""
                UPDATE payroll_periods 
                SET status = 'processed',
                    processed_by = ?,
                    processed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (processed_by, period_id))
            
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
            
            cursor.execute("""
                SELECT 
                    pe.*,
                    e.name as employee_name,
                    e.name_ar as employee_name_ar,
                    pp.period_year,
                    pp.period_month,
                    pp.start_date,
                    pp.end_date,
                    d.name as department_name,
                    p.title as position_title,
                    ed.bank_name,
                    ed.bank_account,
                    ed.iban
                FROM payroll_entries pe
                JOIN employees e ON pe.employee_id = e.id
                JOIN payroll_periods pp ON pe.payroll_period_id = pp.id
                JOIN employment_details ed ON e.id = ed.employee_id
                JOIN departments d ON ed.department_id = d.id
                JOIN positions p ON ed.position_id = p.id
                WHERE pe.id = ?
            """, (entry_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, "Entry not found"
                
            columns = [description[0] for description in cursor.description]
            payslip = dict(zip(columns, row))
            
            # Get component details
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
            
            payslip['components'] = []
            for amount, type_, name, name_ar in cursor.fetchall():
                payslip['components'].append({
                    'amount': amount,
                    'type': type_,
                    'name': name,
                    'name_ar': name_ar
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
            
            # Get list of employees already in this period
            cursor.execute("""
                SELECT employee_id FROM payroll_entries 
                WHERE payroll_period_id = ?
            """, (period_id,))
            existing_employees = {row[0] for row in cursor.fetchall()}
            
            # Filter out employees that are already in the payroll
            new_employees = [emp_id for emp_id in employee_ids if emp_id not in existing_employees]
            
            if not new_employees:
                return False, "جميع الموظفين المحددين موجودين بالفعل في كشف الرواتب"
            
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
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Check period status
            cursor.execute("""
                SELECT status FROM payroll_periods
                WHERE id = ?
            """, (period_id,))
            
            period = cursor.fetchone()
            if not period:
                return False, "فترة الرواتب غير موجودة"
                
            if period[0] not in ['draft', 'processing']:
                return False, "لا يمكن تعديل فترة معتمدة"
            
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # Update basic salary and payment method
                cursor.execute("""
                    UPDATE payroll_entries 
                    SET basic_salary = ?,
                        payment_method = ?,
                        notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE payroll_period_id = ? AND employee_id = ?
                """, (
                    values['basic_salary'],
                    values['payment_method'],
                    values['notes'],
                    period_id,
                    employee_id
                ))
                
                # Update allowances
                for comp_id, value in values['allowances'].items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO payroll_entry_components (
                            payroll_entry_id, component_id, value
                        ) VALUES (
                            (SELECT id FROM payroll_entries 
                             WHERE payroll_period_id = ? AND employee_id = ?),
                            ?, ?
                        )
                    """, (period_id, employee_id, comp_id, value))
                
                # Update deductions
                for comp_id, value in values['deductions'].items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO payroll_entry_components (
                            payroll_entry_id, component_id, value
                        ) VALUES (
                            (SELECT id FROM payroll_entries 
                             WHERE payroll_period_id = ? AND employee_id = ?),
                            ?, ?
                        )
                    """, (period_id, employee_id, comp_id, value))
                
                # Recalculate totals
                cursor.execute("""
                    UPDATE payroll_entries 
                    SET total_allowances = (
                        SELECT COALESCE(SUM(pec.value), 0)
                        FROM payroll_entry_components pec
                        JOIN salary_components sc ON pec.component_id = sc.id
                        WHERE pec.payroll_entry_id = payroll_entries.id
                        AND sc.type = 'allowance'
                    ),
                    total_deductions = (
                        SELECT COALESCE(SUM(pec.value), 0)
                        FROM payroll_entry_components pec
                        JOIN salary_components sc ON pec.component_id = sc.id
                        WHERE pec.payroll_entry_id = payroll_entries.id
                        AND sc.type = 'deduction'
                    ),
                    net_salary = basic_salary + (
                        SELECT COALESCE(SUM(CASE WHEN sc.type = 'allowance' THEN pec.value ELSE -pec.value END), 0)
                        FROM payroll_entry_components pec
                        JOIN salary_components sc ON pec.component_id = sc.id
                        WHERE pec.payroll_entry_id = payroll_entries.id
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE payroll_period_id = ? AND employee_id = ?
                """, (period_id, employee_id))
                
                conn.commit()
                return True, "تم تحديث البيانات بنجاح"
                
            except Exception as e:
                cursor.execute("ROLLBACK")
                raise e
            
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()
