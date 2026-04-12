import vonage
from vonage_sms.requests import SmsMessage
from flask import current_app
from app.models import Caregiver


def send_sms_alert(event_type):
    try:
        api_key = current_app.config.get("VONAGE_API_KEY")
        api_secret = current_app.config.get("VONAGE_API_SECRET")
        from_number = current_app.config.get("VONAGE_FROM_NUMBER")

        if not api_key or not api_secret or not from_number:
            print(">>> SMS skipped: Vonage credentials not configured")
            return

        client = vonage.Auth(api_key=api_key, api_secret=api_secret)
        vonage_client = vonage.Vonage(auth=client)

        admin_phone = current_app.config.get("ADMIN_PHONE")
        caregivers = Caregiver.query.filter_by(is_active=True).all()
        phone_numbers = []

        if admin_phone:
            phone_numbers.append(admin_phone)

        phone_numbers.extend([cg.phone for cg in caregivers if cg.phone])

        # Convert local Pakistani numbers (03xx) to international format (923xx)
        phone_numbers = [
            "92" + p[1:] if p.startswith("0") else p
            for p in phone_numbers
        ]

        if event_type == "hand_gesture":
            message_text = "VisionGuard Alert: Help gesture detected! Immediate attention required."
        else:
            message_text = "VisionGuard Alert: Fall detected! Immediate attention required."

        for phone in phone_numbers:
            try:
                vonage_client.sms.send(
                    SmsMessage(
                        from_=from_number,
                        to=phone,
                        text=message_text,
                    )
                )
                print(f">>> SMS sent to {phone}")
            except Exception as e:
                print(f">>> SMS failed for {phone}: {e}")

    except Exception as e:
        print(f"Error in SMS alert: {e}")
