from app import create_app, db, socketio

socketio, app = create_app()

with app.app_context():
    db.create_all()

socketio.run(
    app,
    host="0.0.0.0",
    port=5000,
    debug=True,
    use_reloader=False,
    allow_unsafe_werkzeug=True,
)
