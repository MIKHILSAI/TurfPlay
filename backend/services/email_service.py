import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    to_email,
    subject,
    body,
    html=False
):
    """
    Send an email via SMTP.

    For Gmail:
    - Enable 2FA
    - Generate an App Password at
      https://myaccount.google.com/apppasswords
    - Use the app password (NOT your real password)
    """

    # --------------------------------------------------------
    # 1. Validate SMTP configuration
    # --------------------------------------------------------

    if not SMTP_USER or not SMTP_PASS:
        return {
            "success": False,
            "error_code": "EMAIL_NOT_CONFIGURED",
            "message": (
                "SMTP credentials are not configured. "
                "Please set SMTP_USER and SMTP_PASS in .env"
            )
        }

    # --------------------------------------------------------
    # 2. Validate recipient
    # --------------------------------------------------------

    if not to_email:
        return {
            "success": False,
            "error_code": "RECIPIENT_REQUIRED",
            "message": "Recipient email is required."
        }

    # --------------------------------------------------------
    # 3. Build message
    # --------------------------------------------------------

    try:

        msg = MIMEMultipart()

        msg["From"] = SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "html" if html else "plain",
                "utf-8"
            )
        )

    except Exception as e:

        return {
            "success": False,
            "error_code": "EMAIL_BUILD_FAILED",
            "message": f"Unable to build email: {str(e)}"
        }

    # --------------------------------------------------------
    # 4. Send via SMTP
    # --------------------------------------------------------

    try:

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=15
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASS
            )

            server.send_message(msg)

    except smtplib.SMTPAuthenticationError:

        return {
            "success": False,
            "error_code": "SMTP_AUTH_FAILED",
            "message": (
                "SMTP authentication failed. "
                "Check your app password."
            )
        }

    except smtplib.SMTPRecipientsRefused:

        return {
            "success": False,
            "error_code": "INVALID_RECIPIENT",
            "message": (
                f"The recipient '{to_email}' "
                "was rejected by the mail server."
            )
        }

    except smtplib.SMTPException as e:

        return {
            "success": False,
            "error_code": "SMTP_ERROR",
            "message": f"SMTP error: {str(e)}"
        }

    except Exception as e:

        return {
            "success": False,
            "error_code": "EMAIL_SEND_FAILED",
            "message": f"Unable to send email: {str(e)}"
        }

    # --------------------------------------------------------
    # 5. Success
    # --------------------------------------------------------

    return {
        "success": True,
        "message": "Email sent successfully.",
        "to": to_email,
        "subject": subject
    }