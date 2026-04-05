import os
from flask_mail import Message
from flask import current_app
from app import mail, db
from app.models import Caregiver
from datetime import datetime


def send_email_alert(event_type, image_path):
    try:
        admin_email = current_app.config.get("MAIL_DEFAULT_SENDER")

        caregivers = Caregiver.query.filter_by(is_active=True).all()
        recipient_emails = [admin_email] if admin_email else []
        recipient_emails.extend([cg.email for cg in caregivers])

        if event_type == "hand_gesture":
            subject = "VisionGuard Alert: Help Gesture Detected"
            event_description = "A help hand gesture was detected"
        else:
            subject = "VisionGuard Alert: Fall Detected"
            event_description = "A fall event was detected"

        detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        body = f"""VisionGuard Alert

{event_description} at {detection_time}.

Immediate attention may be required. Please check on the patient as soon as possible.

This is an automated alert from the VisionGuard monitoring system.
"""

        msg = Message(subject=subject, recipients=recipient_emails, body=body)

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                msg.attach(
                    filename=os.path.basename(image_path),
                    content_type="image/jpeg",
                    data=f.read(),
                )

        mail.send(msg)

    except Exception as e:
        print(f"Error sending email alert: {e}")
