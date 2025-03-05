import sqlite3
from datetime import datetime, timedelta

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
        employee = self.db.execute_query(
            f"SELECT id FROM employees WHERE id = {employee_id}"
        )
        if not employee:
            raise Exception(f"Employee with ID {employee_id} not found")
        
        # Check if employee already checked in today
        today = datetime.now().strftime('%Y-%m-%d')
        existing_record = self.db.execute_query(
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
        shift = self.db.execute_query(shift_query)
        
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
        self.db.execute(
            f"""
            INSERT INTO attendance_records 
            (employee_id, check_in, status) 
            VALUES ({employee_id}, '{check_in_time}', '{status}')
            """
        )
        
        record_id = self.db.last_insert_rowid()
        
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
        record = self.db.execute_query(
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
        self.db.execute(
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
        
        records = self.db.execute_query(query)
        
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
        shift = self.db.execute_query(shift_query)
        
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
