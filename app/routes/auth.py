from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from app import db
from app.models import Caregiver
from app.verification import confirm_verification_token
from config import Config

auth = Blueprint("auth", __name__)
login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, id, email, user_type, is_active=True):
        self.id = id
        self.email = email
        self.user_type = user_type
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active


@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("admin_"):
        admin_email = user_id.replace("admin_", "")
        if admin_email == Config.ADMIN_EMAIL:
            return User("admin_" + admin_email, admin_email, "admin")
    else:
        caregiver = Caregiver.query.get(int(user_id))
        if caregiver:
            return User(
                str(caregiver.id), caregiver.email, "caregiver", caregiver.is_active
            )
    return None


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == Config.ADMIN_EMAIL and password == Config.ADMIN_PASSWORD:
            user = User("admin_" + email, email, "admin")
            login_user(user)
            return redirect(url_for("admin.dashboard"))

        caregiver = Caregiver.query.filter_by(email=email, password=password).first()
        if caregiver and not caregiver.is_verified:
            flash(
                "Please verify your email first. Check your inbox for the verification link."
            )
        elif caregiver:
            user = User(
                str(caregiver.id), caregiver.email, "caregiver", caregiver.is_active
            )
            login_user(user)
            return redirect(url_for("caregiver.dashboard"))
        else:
            flash("Invalid email or password")

    return render_template("login.html")


@auth.route("/verify-email/<token>")
def verify_email(token):
    caregiver, error = confirm_verification_token(token)
    if error:
        return render_template("verify_email.html", status=error)

    if caregiver.is_verified:
        return render_template("verify_email.html", status="already")

    caregiver.is_verified = True
    db.session.commit()
    return render_template("verify_email.html", status="success")


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
