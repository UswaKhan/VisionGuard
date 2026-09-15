from flask import current_app, url_for
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from markupsafe import escape

from app import mail
from app.models import Caregiver

TOKEN_SALT = "caregiver-email-verify"
TOKEN_MAX_AGE = 24 * 60 * 60  # link stays valid for 24 hours


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_verification_token(caregiver):
    return _serializer().dumps(
        {"id": caregiver.id, "email": caregiver.email}, salt=TOKEN_SALT
    )


def confirm_verification_token(token):
    """Return (caregiver, error). error is None, "expired" or "invalid"."""
    try:
        data = _serializer().loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"

    caregiver = Caregiver.query.get(data.get("id"))
    # The email check stops an old link from verifying a re-added account.
    if caregiver is None or caregiver.email != data.get("email"):
        return None, "invalid"
    return caregiver, None


def build_verification_link(token):
    # BASE_URL is the address caregivers can reach (Wi-Fi IP or tunnel link).
    base_url = current_app.config.get("BASE_URL")
    if base_url:
        return base_url.rstrip("/") + url_for("auth.verify_email", token=token)
    return url_for("auth.verify_email", token=token, _external=True)


def send_verification_email(caregiver):
    link = build_verification_link(generate_verification_token(caregiver))
    name = escape(caregiver.name)

    msg = Message(
        subject="VisionGuard: Please verify your email",
        recipients=[caregiver.email],
    )

    msg.body = f"""Hello {caregiver.name},

You have been added as a caregiver on VisionGuard. Before you can sign in and receive alerts, please verify your email address by opening the link below:

{link}

This link will expire in 24 hours. If you were not expecting this email, you can ignore it.

VisionGuard Monitoring System
"""

    msg.html = f"""
<div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 520px; margin: 0 auto; color: #1a1f2e;">
  <h2 style="color: #4361ee; margin-bottom: 16px;">VisionGuard</h2>
  <p>Hello {name},</p>
  <p>You have been added as a caregiver on VisionGuard. Before you can sign in and receive alerts, please verify your email address.</p>
  <p style="margin: 28px 0;">
    <a href="{link}" style="background: #4361ee; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block;">Verify my email</a>
  </p>
  <p style="font-size: 13px; color: #6c757d;">If the button does not work, copy this link into your browser:<br>
    <a href="{link}" style="color: #4361ee; word-break: break-all;">{link}</a></p>
  <p style="font-size: 13px; color: #6c757d;">This link will expire in 24 hours. If you were not expecting this email, you can ignore it.</p>
</div>
"""

    mail.send(msg)
