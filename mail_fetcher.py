import imaplib
import email
import os
import datetime
from email.header import decode_header
from dotenv import load_dotenv
from excel_to_sqlite import process_excel_files

# Load environment variables
load_dotenv()

# Configuration
IMAP_SERVER = os.getenv('MAIL_SERVER', 'imap.gmail.com')
maill_port_str = os.getenv('MAIL_PORT', '993')
try:
    IMAP_PORT = int(maill_port_str)
except ValueError:
    IMAP_PORT = 993

EMAIL_USER = os.getenv('MAIL_USERNAME')
EMAIL_PASS = os.getenv('MAIL_PASSWORD')
ALLOWED_SENDER = os.getenv('MAIL_SENDER_FILTER')

UPLOAD_FOLDER = os.path.dirname(os.path.abspath(__file__))

def clean_filename(filename):
    """Sanitize filename to prevent directory traversal"""
    return "".join([c for c in filename if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).rstrip()

def fetch_email_attachments():
    """
    Connects to email, finds unread messages from allowed sender,
    downloads Excel attachments, and processes them.
    """
    if not EMAIL_USER or not EMAIL_PASS:
        return {
            'status': 'error',
            'message': 'Email configuration missing in .env file (MAIL_USERNAME/MAIL_PASSWORD)'
        }

    try:
        # 1. Connect to IMAP
        print(f"[INFO] Connecting to {IMAP_SERVER}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # 2. Search for emails
        # Criteria: UNSEEN
        print(f"[INFO] Searching for UNREAD emails...")
        status, messages = mail.search(None, '(UNSEEN)')
        
        if status != "OK":
            return {'status': 'error', 'message': 'Failed to search emails'}

        email_ids = messages[0].split()
        
        if not email_ids:
            return {'status': 'success', 'message': 'No new emails found', 'processed_files': []}

        print(f"[INFO] Found {len(email_ids)} unread emails. Filtering by sender...")
        
        # Parse allowed senders
        allowed_senders = []
        if ALLOWED_SENDER:
            allowed_senders = [s.strip().lower() for s in ALLOWED_SENDER.split(',') if s.strip()]

        downloaded_files = []

        for e_id in email_ids:
            # Fetch the email body
            res, msg = mail.fetch(e_id, "(RFC822)")
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    sender_header, encoding = decode_header(msg.get("From"))[0]
                    if isinstance(sender_header, bytes):
                        sender_header = sender_header.decode(encoding if encoding else "utf-8")
                    
                    # Extract email from "Name <email>" or just "email"
                    sender_email = sender_header
                    if '<' in sender_header and '>' in sender_header:
                        sender_email = sender_header.split('<')[1].split('>')[0]
                    
                    sender_email = sender_email.strip().lower()
                    
                    # Filter check
                    if allowed_senders:
                        if sender_email not in allowed_senders:
                            print(f"[SKIP] Email from {sender_email} is not in allowed list.")
                            continue

                    print(f"[INFO] Processing Email: {subject} from {sender_email}")

                    # Walk through multipart email
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_disposition = str(part.get("Content-Disposition"))
                            
                            if "attachment" in content_disposition:
                                filename = part.get_filename()
                                if filename:
                                    # Decode filename
                                    decoded_filename_parts = decode_header(filename)
                                    filename_fragments = []
                                    for f_part, f_enc in decoded_filename_parts:
                                        if isinstance(f_part, bytes):
                                            if f_enc:
                                                filename_fragments.append(f_part.decode(f_enc))
                                            else:
                                                filename_fragments.append(f_part.decode('utf-8', errors='ignore'))
                                        else:
                                            filename_fragments.append(str(f_part))
                                    
                                    filename = "".join(filename_fragments)
                                    
                                    # Check extension
                                    if filename.lower().endswith(('.xls', '.xlsx', '.csv')):
                                        # Rename with timestamp
                                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_")
                                        safe_filename = clean_filename(filename)
                                        new_filename = f"{timestamp}{safe_filename}"
                                        
                                        filepath = os.path.join(UPLOAD_FOLDER, new_filename)
                                        
                                        # Save file
                                        with open(filepath, "wb") as f:
                                            f.write(part.get_payload(decode=True))
                                            
                                        print(f"[INFO] Downloaded: {new_filename}")
                                        downloaded_files.append(new_filename)

        mail.close()
        mail.logout()

        if not downloaded_files:
            return {'status': 'success', 'message': 'Emails found but no Excel attachments'}

        # 3. Process the files
        print(f"[INFO] Starting processing for {len(downloaded_files)} files...")
        process_result = process_excel_files(custom_directory=UPLOAD_FOLDER)
        
        return {
            'status': 'success',
            'message': f'Downloaded {len(downloaded_files)} files. Processing result: {process_result["processed"]} processed, {process_result["failed"]} failed.',
            'details': process_result
        }

    except Exception as e:
        print(f"[ERROR] Email fetch error: {str(e)}")
        return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    result = fetch_email_attachments()
    print(result)
