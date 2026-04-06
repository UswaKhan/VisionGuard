from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
socketio = SocketIO()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    socketio.init_app(app, async_mode="threading", cors_allowed_origins="*")
    mail.init_app(app)

    from app.routes.auth import login_manager, auth

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from app.routes.admin import admin
    from app.routes.caregiver import caregiver
    from app.routes.stream import stream

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(caregiver)
    app.register_blueprint(stream)

    return socketio, app
