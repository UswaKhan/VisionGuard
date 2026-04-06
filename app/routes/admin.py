import os
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
    request,
)
from flask_login import current_user

from app import db
from app.models import Event, Alert, Caregiver

admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != "admin":
            flash("Access denied. Admin login required.")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@admin.route("/dashboard")
@admin_required
def dashboard():
    event_count = Event.query.count()
    alert_count = Alert.query.count()
    caregiver_count = Caregiver.query.count()
    return render_template(
        "admin/dashboard.html",
        total_events=event_count,
        total_alerts=alert_count,
        total_caregivers=caregiver_count,
    )


@admin.route("/livestream")
@admin_required
def livestream():
    return render_template("admin/livestream.html")


@admin.route("/events")
@admin_required
def events():
    invalid_events = Event.query.filter(
        Event.image_path.isnot(None), ~Event.image_path.startswith("/static/")
    ).all()

    for event in invalid_events:
        try:
            if os.path.isabs(event.image_path) and os.path.exists(event.image_path):
                os.remove(event.image_path)
        except:
            pass
        db.session.delete(event)

    if invalid_events:
        db.session.commit()

    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("admin/events.html", events=events)


@admin.route("/alerts")
@admin_required
def alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template("admin/alerts.html", alerts=alerts)


@admin.route("/caregivers")
@admin_required
def caregivers():
    caregivers = Caregiver.query.all()
    return render_template("admin/caregivers.html", caregivers=caregivers)


@admin.route("/caregivers/add", methods=["POST"])
@admin_required
def add_caregiver():
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    password = request.form.get("password")

    if Caregiver.query.filter_by(email=email).first():
        flash("A caregiver with this email already exists.")
        return redirect(url_for("admin.caregivers"))

    caregiver = Caregiver(name=name, email=email, phone=phone, password=password)
    db.session.add(caregiver)
    db.session.commit()

    flash("Caregiver added successfully.")
    return redirect(url_for("admin.caregivers"))


@admin.route("/caregivers/delete/<int:id>", methods=["POST"])
@admin_required
def delete_caregiver(id):
    caregiver = Caregiver.query.get_or_404(id)
    db.session.delete(caregiver)
    db.session.commit()

    flash("Caregiver deleted successfully.")
    return redirect(url_for("admin.caregivers"))


@admin.route("/events/delete/<int:id>", methods=["POST"])
@admin_required
def delete_event(id):
    event = Event.query.get_or_404(id)

    if event.image_path:
        image_path = os.path.join(
            current_app.root_path, "static", event.image_path.lstrip("/")
        )
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(event)
    db.session.commit()

    flash("Event deleted successfully.")
    return redirect(url_for("admin.events"))


@admin.route("/events/delete-all", methods=["POST"])
@admin_required
def delete_all_events():
    events = Event.query.all()

    for event in events:
        if event.image_path:
            image_path = os.path.join(
                current_app.root_path, "static", event.image_path.lstrip("/")
            )
            if os.path.exists(image_path):
                os.remove(image_path)

    Event.query.delete()
    db.session.commit()

    flash("All events deleted successfully.")
    return redirect(url_for("admin.events"))


@admin.route("/alerts/delete/<int:id>", methods=["POST"])
@admin_required
def delete_alert(id):
    alert = Alert.query.get_or_404(id)
    db.session.delete(alert)
    db.session.commit()

    flash("Alert deleted successfully.")
    return redirect(url_for("admin.alerts"))


@admin.route("/alerts/delete-all", methods=["POST"])
@admin_required
def delete_all_alerts():
    Alert.query.delete()
    db.session.commit()

    flash("All alerts deleted successfully.")
    return redirect(url_for("admin.alerts"))
