"""
Payslip template for printing employee payslips
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGridLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QPainter, QTextDocument
from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrinter
import qtawesome as qta
from datetime import datetime
from utils.company_info import CompanyInfo

class PayslipTemplate:
    """Class to generate HTML payslip template for printing"""
    
    @staticmethod
    def generate_html(payslip_data):
        """
        Generate HTML template for a payslip
        
        Args:
            payslip_data: Dictionary containing payslip information
            
        Returns:
            str: HTML template for the payslip
        """
        # Get company information
        db_file = payslip_data.get('db_file', None)
        company_name = "شركة"  # Default company name
        commercial_register = ""
        social_insurance = ""
        tax_number = ""
        
        if db_file:
            company_name = CompanyInfo.get_company_name(db_file) or company_name
            commercial_register = CompanyInfo.get_commercial_register(db_file) or ""
            social_insurance = CompanyInfo.get_social_insurance(db_file) or ""
            tax_number = CompanyInfo.get_tax_number(db_file) or ""
        
        # Get Arabic month name
        month_names = [
            "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
            "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
        ]
        
        # Handle missing fields gracefully
        period_month = payslip_data.get('period_month', 1)
        try:
            period_month = int(period_month)
            if period_month < 1 or period_month > 12:
                period_month = 1
        except (ValueError, TypeError):
            period_month = 1
            
        month_name = month_names[period_month - 1]
        
        # Format dates
        start_date = payslip_data.get('start_date', '')
        end_date = payslip_data.get('end_date', '')
        payment_date = payslip_data.get('payment_date', '')
        
        # Handle date formatting safely
        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y/%m/%d')
        except (ValueError, TypeError):
            start_date = ''
        
        try:
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y/%m/%d')
        except (ValueError, TypeError):
            end_date = ''
            
        try:
            if payment_date:
                payment_date = datetime.strptime(payment_date, '%Y-%m-%d').strftime('%Y/%m/%d')
        except (ValueError, TypeError):
            payment_date = ''
        
        # Create conditional HTML for company info
        commercial_register_html = f'<div class="company-info">السجل التجاري: {commercial_register}</div>' if commercial_register else ''
        social_insurance_html = f'<div class="company-info">رقم التأمينات الاجتماعية: {social_insurance}</div>' if social_insurance else ''
        tax_number_html = f'<div class="company-info">الرقم الضريبي: {tax_number}</div>' if tax_number else ''
        
        # Employee info
        employee_name = payslip_data.get('employee_name_ar', payslip_data.get('employee_name', 'موظف'))
        employee_id = payslip_data.get('employee_id', '')
        department = payslip_data.get('department_name', '')
        position = payslip_data.get('position_title', '')
        
        # Salary info
        basic_salary = payslip_data.get('basic_salary', 0)
        total_allowances = payslip_data.get('total_allowances', 0)
        total_deductions = payslip_data.get('total_deductions', 0)
        total_adjustments = payslip_data.get('total_adjustments', 0)
        net_salary = payslip_data.get('net_salary', 0)
        
        # Bank info
        bank_name = payslip_data.get('bank_name', '')
        bank_account = payslip_data.get('bank_account', '')
        iban = payslip_data.get('iban', '')
        
        # Payment method
        payment_method = payslip_data.get('payment_method_name', '')
        payment_status = payslip_data.get('payment_status', '')
        
        # Translate payment status
        payment_status_ar = {
            'pending': 'معلق',
            'paid': 'مدفوع',
            'failed': 'فشل'
        }.get(payment_status, payment_status)
        
        # Components
        components = payslip_data.get('components', [])
        allowances = [c for c in components if c.get('type') == 'allowance']
        deductions = [c for c in components if c.get('type') == 'deduction']
        
        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    direction: rtl;
                }}
                .payslip {{
                    border: 1px solid #000;
                    padding: 20px;
                    max-width: 800px;
                    margin: 0 auto;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #000;
                    padding-bottom: 10px;
                }}
                .company-name {{
                    font-size: 20px;
                    font-weight: bold;
                    margin-bottom: 5px;
                    color: #2c3e50;
                }}
                .company-info {{
                    font-size: 12px;
                    color: #7f8c8d;
                    margin-bottom: 10px;
                }}
                .payslip-title {{
                    font-size: 18px;
                    margin: 10px 0;
                }}
                .period {{
                    font-size: 16px;
                    margin-bottom: 10px;
                }}
                .employee-info {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                }}
                .info-group {{
                    width: 48%;
                }}
                .info-row {{
                    display: flex;
                    margin-bottom: 5px;
                }}
                .info-label {{
                    font-weight: bold;
                    width: 40%;
                }}
                .info-value {{
                    width: 60%;
                }}
                .salary-details {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                .salary-details th, .salary-details td {{
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: right;
                }}
                .salary-details th {{
                    background-color: #f2f2f2;
                }}
                .summary {{
                    display: flex;
                    justify-content: flex-end;
                    margin-top: 20px;
                }}
                .total-box {{
                    border: 2px solid #000;
                    padding: 10px;
                    width: 200px;
                    text-align: center;
                }}
                .total-label {{
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .total-value {{
                    font-size: 18px;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="payslip">
                <div class="header">
                    <div class="company-name">{company_name}</div>
                    {commercial_register_html}
                    {social_insurance_html}
                    {tax_number_html}
                    <div class="payslip-title">قسيمة الراتب</div>
                    <div class="period">الفترة: {month_name} {payslip_data.get('period_year', '')}</div>
                </div>
                
                <div class="employee-info">
                    <div class="info-group">
                        <div class="info-row">
                            <div class="info-label">اسم الموظف:</div>
                            <div class="info-value">{employee_name}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">الرقم الوظيفي:</div>
                            <div class="info-value">{employee_id}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">القسم:</div>
                            <div class="info-value">{department}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">المسمى الوظيفي:</div>
                            <div class="info-value">{position}</div>
                        </div>
                    </div>
                    
                    <div class="info-group">
                        <div class="info-row">
                            <div class="info-label">تاريخ البدء:</div>
                            <div class="info-value">{start_date}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">تاريخ الانتهاء:</div>
                            <div class="info-value">{end_date}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">تاريخ الدفع:</div>
                            <div class="info-value">{payment_date}</div>
                        </div>
                    </div>
                </div>
                
                <table class="salary-details">
                    <tr>
                        <th>البند</th>
                        <th>المبلغ</th>
                    </tr>
                    <tr>
                        <td>الراتب الأساسي</td>
                        <td>{float(basic_salary):,.2f}</td>
                    </tr>
        """
        
        # Add allowances
        allowances_total = 0
        for component in allowances:
            amount = float(component.get('amount', 0))
            allowances_total += amount
            html += f"""
                <tr>
                    <td>{component.get('name_ar', '')}</td>
                    <td>{amount:,.2f}</td>
                </tr>
            """
        
        # Add deductions
        deductions_total = 0
        for component in deductions:
            amount = float(component.get('amount', 0))
            deductions_total += amount
            html += f"""
                <tr>
                    <td>{component.get('name_ar', '')}</td>
                    <td>({amount:,.2f})</td>
                </tr>
            """
        
        # Calculate net salary
        net_salary = float(basic_salary) + allowances_total - deductions_total
        
        html += f"""
                </table>
                
                <div class="summary">
                    <div class="total-box">
                        <div class="total-label">صافي الراتب</div>
                        <div class="total-value">{net_salary:,.2f}</div>
                    </div>
                </div>
                
                <div class="footer">
                    <p>هذه القسيمة تم إنشاؤها بواسطة نظام إدارة الموظفين</p>
                    <p>تاريخ الطباعة: {datetime.now().strftime('%Y/%m/%d')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html


class PayslipPrinter:
    """Class to handle printing of payslips"""
    
    @staticmethod
    def print_payslip(parent, payslip_data):
        """
        Print a single payslip
        
        Args:
            parent: Parent widget
            payslip_data: Dictionary containing payslip information
        """
        html = PayslipTemplate.generate_html(payslip_data)
        document = QTextDocument()
        document.setHtml(html)
        
        preview = QPrintPreviewDialog()
        preview.paintRequested.connect(lambda printer: document.print_(printer))
        preview.exec_()
    
    @staticmethod
    def print_multiple_payslips(parent, payslips_data):
        """
        Print multiple payslips
        
        Args:
            parent: Parent widget
            payslips_data: List of dictionaries containing payslip information
        """
        if not payslips_data:
            QMessageBox.warning(parent, "خطأ", "لا توجد بيانات للطباعة")
            return
            
        # Create a single document with all payslips
        html = "<!DOCTYPE html><html><body>"
        
        for i, payslip_data in enumerate(payslips_data):
            html += PayslipTemplate.generate_html(payslip_data)
            if i < len(payslips_data) - 1:
                html += "<div style='page-break-after: always;'></div>"
                
        html += "</body></html>"
        
        document = QTextDocument()
        document.setHtml(html)
        
        preview = QPrintPreviewDialog()
        preview.paintRequested.connect(lambda printer: document.print_(printer))
        preview.exec_()
