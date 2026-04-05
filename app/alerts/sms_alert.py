from flask_mail import Message
from flask import current_app
from app import mail, db
from app.models import Caregiver


def detect_carrier(phone_number):
    if not phone_number:
        return None

    prefix = phone_number[:4]

    jazz_prefixes = ["0300", "0301", "0302", "0303", "0304", "0305"]
    zong_prefixes = ["0310", "0311", "0312", "0313", "0314", "0315"]
    telenor_prefixes = ["0340", "0341", "0342", "0343", "0344", "0345"]
    ufone_prefixes = ["0333", "0331", "0332", "0334", "0335"]

    if prefix in jazz_prefixes:
        return "jazz"
    elif prefix in zong_prefixes:
        return "zong"
    elif prefix in telenor_prefixes:
        return "telenor"
    elif prefix in ufone_prefixes:
        return "ufone"

    return None


def get_sms_gateway(phone_number):
    carrier = detect_carrier(phone_number)

    gateways = {
        "jazz": "jazz.com.pk",
        "zong": "zong.com.pk",
        "telenor": "telenor.com.pk",
        "ufone": "ufone.com.pk",
    }

    if carrier and carrier in gateways:
        return f"{phone_number}@{gateways[carrier]}"

    return None


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
            try:
                sms_gateway = get_sms_gateway(phone)

                if sms_gateway:
                    msg = Message(
                        subject="VisionGuard Alert",
                        recipients=[sms_gateway],
                        body=message_text,
                    )
                    mail.send(msg)

            except Exception as e:
                print(f"Error sending SMS to {phone}: {e}")
                continue

    except Exception as e:
        print(f"Error sending SMS alert: {e}")
