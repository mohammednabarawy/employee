import sqlite3

class CompanyInfo:
    """Utility class for retrieving company information"""
    
    @staticmethod
    def get_company_info(db_file):
        """Get company information from the database"""
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Check if company_info table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='company_info'")
            if not cursor.fetchone():
                conn.close()
                return None
            
            # Get company info
            cursor.execute("SELECT * FROM company_info LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                # Get column names
                column_names = [description[0] for description in cursor.description]
                company_info = dict(zip(column_names, row))
                conn.close()
                return company_info
            
            conn.close()
            return None
        except Exception as e:
            print(f"Error retrieving company info: {str(e)}")
            return None
    
    @staticmethod
    def get_company_name(db_file):
        """Get company name from the database"""
        company_info = CompanyInfo.get_company_info(db_file)
        if company_info:
            return company_info.get('company_name', '')
        return ''
    
    @staticmethod
    def get_commercial_register(db_file):
        """Get commercial register number from the database"""
        company_info = CompanyInfo.get_company_info(db_file)
        if company_info:
            return company_info.get('commercial_register_number', '')
        return ''
    
    @staticmethod
    def get_social_insurance(db_file):
        """Get social insurance number from the database"""
        company_info = CompanyInfo.get_company_info(db_file)
        if company_info:
            return company_info.get('social_insurance_number', '')
        return ''
    
    @staticmethod
    def get_tax_number(db_file):
        """Get tax number from the database"""
        company_info = CompanyInfo.get_company_info(db_file)
        if company_info:
            return company_info.get('tax_number', '')
        return ''
    
    @staticmethod
    def get_logo(db_file):
        """Get company logo from the database"""
        company_info = CompanyInfo.get_company_info(db_file)
        if company_info:
            return company_info.get('logo_data'), company_info.get('logo_mime_type')
        return None, None
