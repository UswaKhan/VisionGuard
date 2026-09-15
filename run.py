from sqlalchemy import text

from app import create_app, db, socketio

socketio, app = create_app()

with app.app_context():
    db.create_all()
    # Databases made before email verification lack this column. Add it once;
    # caregivers who already existed are treated as verified.
    db.session.execute(text(
        "ALTER TABLE caregiver ADD COLUMN IF NOT EXISTS "
        "is_verified BOOLEAN NOT NULL DEFAULT TRUE"
    ))
    db.session.execute(text(
        "ALTER TABLE caregiver ALTER COLUMN is_verified SET DEFAULT FALSE"
    ))
    db.session.commit()

socketio.run(
    app,
    host="0.0.0.0",
    port=5000,
    debug=True,
    use_reloader=False,
    allow_unsafe_werkzeug=True,
)
