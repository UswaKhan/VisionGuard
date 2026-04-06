from flask import current_app
from app.models import Caregiver


def send_sms_alert(event_type):
    try:
        admin_phone = current_app.config.get("ADMIN_PHONE")

        caregivers = Caregiver.query.filter_by(is_active=True).all()
        phone_numbers = []

        if admin_phone:
            phone_numbers.append(admin_phone)

        phone_numbers.extend([cg.phone for cg in caregivers])

        if event_type == "hand_gesture":
            message_text = "VisionGuard Alert: Help gesture detected! Immediate attention required."
        else:
            message_text = (
                "VisionGuard Alert: Fall detected! Immediate attention required."
            )

        for phone in phone_numbers:
            print(f">>> SMS to {phone}: {message_text}")

    except Exception as e:
        print(f"Error in SMS alert: {e}")
