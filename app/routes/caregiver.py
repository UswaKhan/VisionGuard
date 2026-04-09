from functools import wraps

from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from app.models import Event, Caregiver
from app.routes.auth import current_user

caregiver = Blueprint("caregiver", __name__, url_prefix="/caregiver")


def caregiver_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.user_type != "caregiver":
            flash("Access denied. Caregiver login required.")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


@caregiver.route("/dashboard")
@caregiver_required
def dashboard():
    cg = Caregiver.query.get(int(current_user.id))
    event_count = Event.query.count()
    return render_template("caregiver/dashboard.html", total_events=event_count, caregiver_name=cg.name if cg else "Caregiver")


@caregiver.route("/livestream")
@caregiver_required
def livestream():
    cg = Caregiver.query.get(int(current_user.id))
    return render_template("caregiver/livestream.html", caregiver_name=cg.name if cg else "Caregiver")


@caregiver.route("/events")
@caregiver_required
def events():
    cg = Caregiver.query.get(int(current_user.id))
    events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template("caregiver/events.html", events=events, caregiver_name=cg.name if cg else "Caregiver")
