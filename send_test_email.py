import os
import django
from django.core.mail import send_mail
from django.conf import settings
import smtplib

# 1️Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alx_travel_app.settings")
django.setup()

# 2️Debug print: confirm email settings
print("Host:", settings.EMAIL_HOST)
print("Port:", settings.EMAIL_PORT)
print("User:", settings.EMAIL_HOST_USER)
print("From:", settings.DEFAULT_FROM_EMAIL)

# 3️Test SMTP connection (strip hostname to avoid trailing spaces)
try:
    server = smtplib.SMTP(settings.EMAIL_HOST.strip(), settings.EMAIL_PORT)
    server.starttls()
    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    print("✅ SMTP login successful")
    server.quit()
except Exception as e:
    print("❌ SMTP connection failed:", e)
    exit(1)  # Stop script if login fails

# 4️Send test email via Django
def main():
    try:
        send_mail(
            subject="Test Email from Django",
            message="Hello! This is a test email to confirm your SMTP settings are working.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["emuhombe@gmail.com"],  # replace with your email
        )
        print("✅ Test email sent!")
    except Exception as e:
        print("❌ Sending email failed:", e)

if __name__ == "__main__":
    main()
