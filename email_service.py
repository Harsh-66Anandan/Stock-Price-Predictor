import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL    = "aryanchoudhury95979@gmail.com"
SENDER_PASSWORD = "ljpyptnkvsftcjli"

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(receiver_email, otp):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Stock Predictor OTP Code"
        msg["From"]    = SENDER_EMAIL
        msg["To"]      = receiver_email

        plain = f"Your OTP is: {otp}\nExpires in 10 minutes."
        html  = f"""
<html><body style="font-family:Arial;background:#0f2027;padding:40px;">
<div style="max-width:500px;margin:auto;background:#203a43;
            border-radius:16px;padding:40px;
            border:1px solid rgba(0,201,255,0.2);">
  <h2 style="color:#00C9FF;text-align:center;">Stock Price Predictor</h2>
  <p style="color:#8fc1d4;text-align:center;">Your One-Time Password:</p>
  <div style="background:#0f2027;border:2px solid #00C9FF;
              border-radius:12px;padding:24px;text-align:center;">
    <h1 style="color:#00C9FF;font-size:52px;letter-spacing:14px;
               margin:0;font-family:monospace;">{otp}</h1>
  </div>
  <p style="color:#8fc1d4;font-size:13px;margin-top:20px;">
    ⏱ Expires in 10 minutes<br>
    🔒 Do not share this with anyone
  </p>
</div>
</body></html>
"""
        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())

        print(f"OTP sent to {receiver_email}")
        return {"success": True, "message": f"OTP sent to {receiver_email}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Gmail auth failed. Check App Password."}
    except Exception as e:
        return {"success": False, "message": str(e)}