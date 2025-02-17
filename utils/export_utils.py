import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

class ExportUtils:
    @staticmethod
    def export_to_excel(data, filename, sheet_name='Sheet1'):
        """Export data to Excel file"""
        try:
            df = pd.DataFrame(data)
            df.to_excel(filename, sheet_name=sheet_name, index=False)
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def generate_payslip_pdf(employee_data, salary_data, payment_data, filename):
        """Generate PDF payslip"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title = Paragraph(f"Payslip - {employee_data['name']}", styles['Title'])
            elements.append(title)
            elements.append(Paragraph("<br/><br/>", styles['Normal']))

            # Employee Details
            employee_details = [
                ["Employee Details", ""],
                ["Name", employee_data['name']],
                ["ID", str(employee_data['id'])],
                ["Department", employee_data['department']],
                ["Position", employee_data['position']]
            ]

            # Salary Details
            salary_details = [
                ["Salary Details", "Amount"],
                ["Base Salary", f"${salary_data['base_salary']:.2f}"],
                ["Bonuses", f"${salary_data['bonuses']:.2f}"],
                ["Overtime Pay", f"${salary_data['overtime_pay']:.2f}"],
                ["Deductions", f"${salary_data['deductions']:.2f}"],
                ["Total Salary", f"${salary_data['total_salary']:.2f}"]
            ]

            # Payment Details
            payment_details = [
                ["Payment Details", ""],
                ["Payment Date", payment_data['payment_date']],
                ["Payment Mode", payment_data['payment_mode']],
                ["Amount Paid", f"${payment_data['amount_paid']:.2f}"],
                ["Status", payment_data['status']]
            ]

            # Create tables with styles
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])

            # Add tables to elements
            for details in [employee_details, salary_details, payment_details]:
                table = Table(details)
                table.setStyle(table_style)
                elements.append(table)
                elements.append(Paragraph("<br/><br/>", styles['Normal']))

            # Build PDF
            doc.build(elements)
            return True, None
        except Exception as e:
            return False, str(e)

    @staticmethod
    def generate_department_report(department_data, filename):
        """Generate PDF department report"""
        try:
            doc = SimpleDocTemplate(filename, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title = Paragraph(f"Department Report - {datetime.now().strftime('%B %Y')}", styles['Title'])
            elements.append(title)
            elements.append(Paragraph("<br/><br/>", styles['Normal']))

            # Create table data
            table_data = [
                ["Department", "Employee Count", "Total Payroll", "Total Bonuses", "Total Deductions"]
            ]

            for dept in department_data:
                table_data.append([
                    dept['department'],
                    str(dept['employee_count']),
                    f"${dept['total_payroll']:.2f}",
                    f"${dept['total_bonuses']:.2f}",
                    f"${dept['total_deductions']:.2f}"
                ])

            # Create table with style
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ])

            table = Table(table_data)
            table.setStyle(table_style)
            elements.append(table)

            # Build PDF
            doc.build(elements)
            return True, None
        except Exception as e:
            return False, str(e)
