"""
Migration script to add approval and processing timestamp columns to payroll_periods table
"""

def run_migration(db):
    """
    Add approved_at and processed_at columns to payroll_periods table
    
    Args:
        db: Database connection object
    
    Returns:
        bool: True if migration was successful, False otherwise
        str: Success message or error message
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(payroll_periods)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add approved_at column if it doesn't exist
        if 'approved_at' not in columns:
            cursor.execute("""
                ALTER TABLE payroll_periods
                ADD COLUMN approved_at TIMESTAMP
            """)
        
        # Add processed_at column if it doesn't exist
        if 'processed_at' not in columns:
            cursor.execute("""
                ALTER TABLE payroll_periods
                ADD COLUMN processed_at TIMESTAMP
            """)
            
        # Add processed_by column if it doesn't exist
        if 'processed_by' not in columns:
            cursor.execute("""
                ALTER TABLE payroll_periods
                ADD COLUMN processed_by INTEGER REFERENCES users(id)
            """)
        
        conn.commit()
        return True, "تم إضافة أعمدة التواريخ بنجاح"
    
    except Exception as e:
        return False, f"خطأ في تنفيذ الترحيل: {str(e)}"
    
    finally:
        conn.close()
