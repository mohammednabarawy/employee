import sqlite3
from datetime import datetime, timedelta, date
import calendar

class AttendanceController:
    """Controller for managing employee attendance records"""
    
    def __init__(self, db):
        """Initialize with database connection"""
        self.db = db
        
    def record_check_in(self, employee_id):
        """Record employee check-in time
        
        Args:
            employee_id (int): ID of the employee checking in
            
        Returns:
            dict: Check-in record details
            
        Raises:
            Exception: If employee already checked in for the day
        """
        # Check if employee exists
        employee = self.db.fetch_query(
            f"SELECT id FROM employees WHERE id = {employee_id}"
        )
        if not employee:
            raise Exception(f"Employee with ID {employee_id} not found")
        
        # Check if employee already checked in today
        today = datetime.now().strftime('%Y-%m-%d')
        existing_record = self.db.fetch_query(
            f"""
            SELECT id FROM attendance_records 
            WHERE employee_id = {employee_id} 
            AND DATE(check_in) = '{today}'
            """
        )
        
        if existing_record:
            raise Exception(f"Employee already checked in today")
        
        # Record check-in time
        check_in_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get employee's shift
        shift_query = f"""
            SELECT s.id, s.shift_name, s.start_time, s.end_time, s.max_regular_hours
            FROM shifts s
            JOIN employees e ON e.shift_id = s.id
            WHERE e.id = {employee_id}
        """
        shift = self.db.fetch_query(shift_query)
        
        # Determine status (on time or late)
        status = "present"
        if shift:
            shift_start = shift[0][2]  # start_time from shifts table
            
            # Parse times for comparison
            current_time = datetime.now().time()
            shift_start_time = datetime.strptime(shift_start, '%H:%M').time()
            
            # If more than 15 minutes late, mark as late
            if current_time > datetime.combine(datetime.today(), shift_start_time).time():
                status = "late"
        
        # Insert attendance record
        self.db.execute_query(
            f"""
            INSERT INTO attendance_records 
            (employee_id, check_in, status) 
            VALUES ({employee_id}, '{check_in_time}', '{status}')
            """
        )
        
        record_id = self.db.execute_query("SELECT last_insert_rowid()").fetchone()[0]
        
        # Return the record
        return {
            "id": record_id,
            "employee_id": employee_id,
            "check_in": check_in_time,
            "status": status
        }
        
    def record_check_out(self, employee_id):
        """Record employee check-out time
        
        Args:
            employee_id (int): ID of the employee checking out
            
        Returns:
            dict: Updated attendance record
            
        Raises:
            Exception: If employee hasn't checked in or already checked out
        """
        # Check if employee checked in today
        today = datetime.now().strftime('%Y-%m-%d')
        record = self.db.fetch_query(
            f"""
            SELECT id, check_in, check_out 
            FROM attendance_records 
            WHERE employee_id = {employee_id} 
            AND DATE(check_in) = '{today}'
            """
        )
        
        if not record:
            raise Exception(f"Employee has not checked in today")
            
        if record[0][2]:  # check_out is not None
            raise Exception(f"Employee already checked out today")
            
        # Record check-out time
        record_id = record[0][0]
        check_in_time = record[0][1]
        check_out_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate total hours worked
        check_in_dt = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S')
        check_out_dt = datetime.now()
        total_hours = (check_out_dt - check_in_dt).total_seconds() / 3600  # Convert to hours
        
        # Update attendance record
        self.db.execute_query(
            f"""
            UPDATE attendance_records 
            SET check_out = '{check_out_time}', total_hours = {total_hours:.2f}
            WHERE id = {record_id}
            """
        )
        
        # Return the updated record
        return {
            "id": record_id,
            "employee_id": employee_id,
            "check_in": check_in_time,
            "check_out": check_out_time,
            "total_hours": round(total_hours, 2)
        }
        
    def get_attendance_records(self, employee_id, start_date, end_date):
        """Get attendance records for an employee within a date range
        
        Args:
            employee_id (int): ID of the employee
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            list: List of attendance records
        """
        query = f"""
            SELECT id, employee_id, check_in, check_out, total_hours, status
            FROM attendance_records
            WHERE employee_id = {employee_id}
            AND DATE(check_in) BETWEEN '{start_date}' AND '{end_date}'
            ORDER BY check_in DESC
        """
        
        records = self.db.fetch_query(query)
        
        # Format records as dictionaries
        formatted_records = []
        for record in records:
            formatted_records.append({
                "id": record[0],
                "employee_id": record[1],
                "check_in": record[2],
                "check_out": record[3],
                "total_hours": record[4],
                "status": record[5]
            })
            
        return formatted_records
        
    def calculate_overtime(self, employee_id, start_date, end_date):
        """Calculate overtime hours for an employee within a date range
        
        Args:
            employee_id (int): ID of the employee
            start_date (str): Start date in format 'YYYY-MM-DD'
            end_date (str): End date in format 'YYYY-MM-DD'
            
        Returns:
            dict: Dictionary with regular_hours, overtime_hours, and total_hours
        """
        # Get employee's shift to determine regular hours
        shift_query = f"""
            SELECT s.max_regular_hours
            FROM shifts s
            JOIN employees e ON e.shift_id = s.id
            WHERE e.id = {employee_id}
        """
        shift = self.db.fetch_query(shift_query)
        
        # Default to 8 hours if no shift defined
        max_regular_hours = 8
        if shift and shift[0][0]:
            max_regular_hours = shift[0][0]
            
        # Get attendance records
        records = self.get_attendance_records(employee_id, start_date, end_date)
        
        # Calculate hours
        total_hours = 0
        overtime_hours = 0
        
        for record in records:
            if record["total_hours"]:
                daily_hours = record["total_hours"]
                total_hours += daily_hours
                
                # Calculate daily overtime
                if daily_hours > max_regular_hours:
                    overtime_hours += (daily_hours - max_regular_hours)
        
        return {
            "regular_hours": round(total_hours - overtime_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "total_hours": round(total_hours, 2)
        }
        
    def get_monthly_attendance_summary(self, employee_id, year, month):
        """Get monthly attendance summary for an employee
        
        Args:
            employee_id (int): ID of the employee
            year (int): Year
            month (int): Month (1-12)
            
        Returns:
            dict: Monthly attendance summary
        """
        # Calculate start and end dates for the month
        start_date = f"{year}-{month:02d}-01"
        
        # Calculate last day of month
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
            
        end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
        end_date = end_date.strftime('%Y-%m-%d')
        
        # Get attendance records
        records = self.get_attendance_records(employee_id, start_date, end_date)
        
        # Calculate summary
        total_days = len(records)
        present_days = sum(1 for r in records if r["status"] == "present")
        late_days = sum(1 for r in records if r["status"] == "late")
        absent_days = sum(1 for r in records if r["status"] == "absent")
        
        # Calculate hours
        hours_data = self.calculate_overtime(employee_id, start_date, end_date)
        
        return {
            "employee_id": employee_id,
            "year": year,
            "month": month,
            "total_days": total_days,
            "present_days": present_days,
            "late_days": late_days,
            "absent_days": absent_days,
            "regular_hours": hours_data["regular_hours"],
            "overtime_hours": hours_data["overtime_hours"],
            "total_hours": hours_data["total_hours"]
        }

    def get_monthly_calendar_data(self, employee_id, year, month):
        """Get attendance data for a month in calendar format
        
        Args:
            employee_id (int): ID of the employee
            year (int): Year
            month (int): Month (1-12)
            
        Returns:
            dict: Calendar data with attendance status for each day
        """
        # Calculate start and end dates for the month
        start_date = f"{year}-{month:02d}-01"
        
        # Get last day of month
        _, last_day = calendar.monthrange(year, month)
        end_date = f"{year}-{month:02d}-{last_day}"
        
        # Get attendance records for the month
        query = f"""
            SELECT DATE(check_in) as date, status
            FROM attendance_records
            WHERE employee_id = {employee_id}
            AND DATE(check_in) BETWEEN '{start_date}' AND '{end_date}'
        """
        records = self.db.fetch_query(query)
        
        # Create a dictionary with dates as keys and status as values
        attendance_data = {}
        for record in records:
            attendance_data[record[0]] = record[1]
        
        # Create calendar data with status for each day
        calendar_data = {}
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        
        while current_date <= end_datetime:
            date_str = current_date.strftime('%Y-%m-%d')
            day = current_date.day
            
            # Check if it's a weekend
            is_weekend = current_date.weekday() >= 5  # 5 is Saturday, 6 is Sunday
            
            if date_str in attendance_data:
                status = attendance_data[date_str]
            elif is_weekend:
                status = "weekend"
            elif current_date > datetime.now():
                status = "future"
            else:
                status = "absent"
            
            calendar_data[day] = status
            current_date += timedelta(days=1)
        
        return calendar_data

    def mark_attendance_for_date(self, employee_id, date_str, status="present", hours=8.0):
        """Mark attendance for a specific date
        
        Args:
            employee_id (int): ID of the employee
            date_str (str): Date in format 'YYYY-MM-DD'
            status (str): Attendance status (present, absent, late, etc.)
            hours (float): Total hours worked
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if employee exists
            employee = self.db.fetch_query(
                f"SELECT id FROM employees WHERE id = {employee_id}"
            )
            if not employee:
                raise Exception(f"Employee with ID {employee_id} not found")
            
            # Check if there's already an attendance record for this date
            existing_record = self.db.fetch_query(
                f"""
                SELECT id FROM attendance_records 
                WHERE employee_id = {employee_id} 
                AND DATE(check_in) = '{date_str}'
                """
            )
            
            if existing_record:
                # Update existing record
                record_id = existing_record[0][0]
                
                if status == "absent":
                    # If marking as absent, delete the record
                    self.db.execute_query(
                        f"DELETE FROM attendance_records WHERE id = {record_id}"
                    )
                else:
                    # Update the status and hours
                    check_in_time = f"{date_str} 09:00:00"
                    check_out_time = f"{date_str} {9 + hours}:00:00"
                    
                    self.db.execute_query(
                        f"""
                        UPDATE attendance_records 
                        SET status = '{status}', 
                            total_hours = {hours},
                            check_in = '{check_in_time}',
                            check_out = '{check_out_time}'
                        WHERE id = {record_id}
                        """
                    )
            else:
                # If status is absent, no need to create a record
                if status == "absent":
                    return True
                
                # Create new record
                check_in_time = f"{date_str} 09:00:00"
                check_out_time = f"{date_str} {9 + hours}:00:00"
                
                self.db.execute_query(
                    f"""
                    INSERT INTO attendance_records 
                    (employee_id, check_in, check_out, status, total_hours) 
                    VALUES (
                        {employee_id}, 
                        '{check_in_time}', 
                        '{check_out_time}', 
                        '{status}', 
                        {hours}
                    )
                    """
                )
            
            return True
        except Exception as e:
            print(f"Error marking attendance: {str(e)}")
            return False

    def batch_mark_attendance(self, employee_ids, date_str, status="present", hours=8.0):
        """Mark attendance for multiple employees on a specific date
        
        Args:
            employee_ids (list): List of employee IDs
            date_str (str): Date in format 'YYYY-MM-DD'
            status (str): Attendance status (present, absent, late, etc.)
            hours (float): Total hours worked
            
        Returns:
            dict: Dictionary with success count and failed count
        """
        success_count = 0
        failed_count = 0
        
        for employee_id in employee_ids:
            result = self.mark_attendance_for_date(employee_id, date_str, status, hours)
            if result:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            "success_count": success_count,
            "failed_count": failed_count
        }

    def get_attendance_status_for_date(self, employee_id, date_str):
        """Get attendance status for a specific date
        
        Args:
            employee_id (int): ID of the employee
            date_str (str): Date in format 'YYYY-MM-DD'
            
        Returns:
            str: Status ('present', 'absent', 'late')
        """
        query = f"""
            SELECT status
            FROM attendance_records
            WHERE employee_id = {employee_id}
            AND DATE(check_in) = '{date_str}'
        """
        
        record = self.db.fetch_query(query)
        if record:
            return record[0][0]
        return "absent"
        
    def mark_attendance_for_date(self, employee_id, date_str, status="present"):
        """Mark attendance for a specific date
        
        Args:
            employee_id (int): ID of the employee
            date_str (str): Date in format 'YYYY-MM-DD'
            status (str): Status to set ('present', 'absent', 'late')
            
        Returns:
            bool: True if successful
        """
        # Delete any existing record for this date
        self.db.execute_query(
            f"""
            DELETE FROM attendance_records
            WHERE employee_id = {employee_id}
            AND DATE(check_in) = '{date_str}'
            """
        )
        
        if status == "present" or status == "late":
            # Create new record with check-in at start of day
            check_in_time = f"{date_str} 09:00:00"  # Default to 9 AM
            check_out_time = f"{date_str} 17:00:00"  # Default to 5 PM
            total_hours = 8.0
            
            self.db.execute_query(
                f"""
                INSERT INTO attendance_records 
                (employee_id, check_in, check_out, total_hours, status)
                VALUES 
                ({employee_id}, '{check_in_time}', '{check_out_time}', {total_hours}, '{status}')
                """
            )
        
        return True
        
    def get_attendance_data_for_period(self, employee_id, period_id):
        """Get attendance summary for a payroll period
        
        Args:
            employee_id (int): ID of the employee
            period_id (int): ID of the payroll period
            
        Returns:
            dict: Dictionary with present_days, absent_days, late_days
        """
        # Get period dates
        period_query = f"""
            SELECT start_date, end_date
            FROM payroll_periods
            WHERE id = {period_id}
        """
        period = self.db.fetch_query(period_query)
        if not period:
            return None
            
        start_date = period[0][0]
        end_date = period[0][1]
        
        # Get attendance records
        records_query = f"""
            SELECT status, COUNT(*) as count
            FROM attendance_records
            WHERE employee_id = {employee_id}
            AND DATE(check_in) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY status
        """
        records = self.db.fetch_query(records_query)
        
        # Calculate days in period
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        total_days = (end - start).days + 1
        
        # Initialize counters
        present_days = 0
        late_days = 0
        
        # Count days by status
        for record in records:
            status = record[0]
            count = record[1]
            if status == "present":
                present_days = count
            elif status == "late":
                late_days = count
                present_days += count  # Late is still counted as present
                
        # Calculate absent days (total days - present days)
        absent_days = total_days - present_days
        
        return {
            "present_days": present_days,
            "absent_days": absent_days,
            "late_days": late_days,
            "total_days": total_days
        }
        
    def get_attendance_records_for_date(self, employee_ids, date_str):
        """Get attendance records for multiple employees on a specific date
        
        Args:
            employee_ids (list): List of employee IDs
            date_str (str): Date in format 'YYYY-MM-DD'
            
        Returns:
            tuple: (success, records) where records is a list of attendance records
        """
        try:
            # Build query with employee IDs
            employee_ids_str = ','.join(str(id) for id in employee_ids)
            query = f"""
                SELECT id, employee_id, status, total_hours, check_in, check_out
                FROM attendance_records
                WHERE employee_id IN ({employee_ids_str})
                AND DATE(check_in) = '{date_str}'
            """
            
            records = self.db.fetch_query(query)
            
            # Format records
            formatted_records = []
            for record in records:
                formatted_records.append({
                    "id": record[0],
                    "employee_id": record[1],
                    "status": record[2],
                    "total_hours": record[3],
                    "check_in": record[4],
                    "check_out": record[5]
                })
                
            return True, formatted_records
        except Exception as e:
            print(f"Error getting attendance records: {str(e)}")
            return False, []

    def get_attendance_status_for_date(self, employee_id, date_str):
        """Get attendance status for a specific date
        
        Args:
            employee_id (int): ID of the employee
            date_str (str): Date in format 'YYYY-MM-DD'
            
        Returns:
            dict: Attendance status or None if no record
        """
        query = f"""
            SELECT id, status, total_hours, check_in, check_out
            FROM attendance_records
            WHERE employee_id = {employee_id}
            AND DATE(check_in) = '{date_str}'
        """
        
        records = self.db.fetch_query(query)
        
        if records:
            row = records[0]  # Get the first row
            return {
                "id": row[0],
                "status": row[1],
                "total_hours": row[2],
                "check_in": row[3],
                "check_out": row[4]
            }
        else:
            # Check if it's a weekend
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            is_weekend = date_obj.weekday() >= 5  # 5 is Saturday, 6 is Sunday
            
            if is_weekend:
                return {"status": "weekend"}
            elif date_obj > datetime.now():
                return {"status": "future"}
            else:
                return {"status": "absent"}
