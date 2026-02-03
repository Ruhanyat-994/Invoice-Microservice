import smtplib, os, json
from email.message import EmailMessage

def notification(body):
    try:
        message = json.loads(body)
        processed_fid = message["processed_fid"]
        receiver_address = message["username"]

        sender_address = os.environ.get("EMAIL_SENDER")
        sender_password = os.environ.get("EMAIL_PASSWORD")

        msg = EmailMessage()
        msg.set_content(f"Your invoice is ready! Download it using ID: {processed_fid}")
        msg["Subject"] = "Invoice Ready for Download"
        msg["From"] = sender_address
        msg["To"] = receiver_address

        session = smtplib.SMTP("smtp.gmail.com", 587)
        session.starttls()
        session.login(sender_address, sender_password)
        session.send_message(msg)
        session.quit()
        print("Mail Sent")
    except Exception as e:
        print(f"Error sending email: {e}")
        return e
