# email_utils.py
import os
import pythoncom
import win32com.client as win32
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime

# ===== EMAIL CONFIGURATION =====
# Bạn cần cập nhật các thông tin này
EMAIL = "huy.nguyen@hellohealthgroup.com"
APP_PASSWORD = ""  # Thay bằng mật khẩu ứng dụng Gmail của bạn
TEMP_DIR = r"D:\HHG\UI\temp"

# Tạo thư mục temp nếu chưa có
os.makedirs(TEMP_DIR, exist_ok=True)

def protect_excel(input_path, output_path, password):
    """Protect Excel file with password"""
    try:
        pythoncom.CoInitialize()
        excel = win32.DispatchEx("Excel.Application")
        excel.DisplayAlerts = False
        wb = excel.Workbooks.Open(os.path.abspath(input_path))
        wb.SaveAs(
            os.path.abspath(output_path),
            FileFormat=51,
            Password=password
        )
        wb.Close(SaveChanges=False)
    except Exception as e:
        # Fallback: copy without password if protection fails
        import shutil
        shutil.copy2(input_path, output_path)
        raise e
    finally:
        try:
            excel.Quit()
        except:
            pass
        pythoncom.CoUninitialize()

def send_email(to, cc, subject, body, attachment_path, original_message_id=None):
    """Send email with attachment"""
    if not APP_PASSWORD:
        raise ValueError("APP_PASSWORD not set in config")
    
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to
    msg["Cc"] = cc
    
    if original_message_id:
        msg["Subject"] = subject.strip() if subject else ""
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id
    else:
        msg["Subject"] = subject.strip() if subject else ""
    
    msg.attach(MIMEText(body, "plain"))
    
    with open(attachment_path, "rb") as f:
        part = MIMEBase("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(attachment_path)}"
        )
        msg.attach(part)
    
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, APP_PASSWORD)
    all_emails = [e.strip() for e in to.split(",") if e.strip()] + \
                 [e.strip() for e in cc.split(",") if e.strip()]
    server.sendmail(EMAIL, all_emails, msg.as_string())
    server.quit()

def create_excel_file(leads_df, project_config, batch_number):
    """Create protected Excel file from leads data"""
    temp_file = os.path.join(TEMP_DIR, f"_tmp_{project_config.get('country', '')}_{project_config.get('brand', '')}.xlsx")
    leads_df.to_excel(temp_file, index=False, header=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = project_config.get('file_name_template', 'leads_{current_date}_Batch{batch_number}.xlsx').format(
        country=project_config.get('country', ''),
        brand=project_config.get('brand', ''),
        current_date=date_str,
        batch_number=batch_number
    )
    output_path = os.path.join(TEMP_DIR, filename)
    
    try:
        protect_excel(temp_file, output_path, project_config.get('password', ''))
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    return output_path, filename

def format_email_body(project_config, batch_number, count_rows, custom_body=None):
    """Format email body with placeholders"""
    current_date = datetime.now().strftime("%d/%m/%Y")
    
    body_template = custom_body if custom_body else project_config.get('email_body', '')
    
    return body_template.format(
        brand=project_config.get('brand', ''),
        country=project_config.get('country', ''),
        batch_number=batch_number,
        current_date=current_date,
        count_rows=count_rows
    )

def get_email_subject(project_config, batch_number, send_as_reply):
    """Get email subject based on reply mode"""
    if send_as_reply and project_config.get("original_subject"):
        return project_config["original_subject"].strip()
    return f"Lead Transfer - {project_config.get('brand', '')} {project_config.get('country', '')} 2025 (Batch #{batch_number})".strip()