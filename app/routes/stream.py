import cv2
import base64
import os
import time
import threading
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from app import socketio, db
from app.models import Event, Alert
from app.detection.hand_gesture import HandGestureDetector
from app.detection.fall_detection import FallDetector
from app.alerts.email_alert import send_email_alert
from app.alerts.sms_alert import send_sms_alert


stream = Blueprint("stream", __name__, url_prefix="/stream")

camera = None
is_streaming = False
hand_detector = HandGestureDetector()
fall_detector = FallDetector()
event_countdown = 0
current_event_type = None


def generate_frames(app):
    global camera, is_streaming, event_countdown, current_event_type

    camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not camera.isOpened():
        print(">>> Camera failed to open")
        is_streaming = False
        return

    print(">>> Camera opened, warming up...")

    for i in range(20):
        ret, frame = camera.read()
        if ret and frame is not None and frame.mean() > 30:
            print(f">>> Camera ready after {i} frames")
            break

    print(">>> Streaming started")
    frame_counter = 0
    countdown_start = 0

    while is_streaming:
        ret, frame = camera.read()
        if not ret or frame is None:
            time.sleep(0.01)
            continue

        frame = cv2.flip(frame, 1)

        frame_counter += 1
        is_hand_gesture = False
        is_fall = False

        if frame_counter % 5 == 0:
            try:
                frame, is_hand_gesture = hand_detector.detect(frame)
            except Exception as e:
                print(f"Hand detection error: {e}")

        if frame_counter % 10 == 0:
            try:
                frame, is_fall = fall_detector.detect(frame)
            except Exception as e:
                print(f"Fall detection error: {e}")

        if is_hand_gesture and event_countdown == 0:
            current_event_type = "hand_gesture"
            event_countdown = 5
            countdown_start = time.time()
            print(f">>> Hand gesture detected! Countdown started.")
        elif is_fall and event_countdown == 0:
            current_event_type = "fall"
            event_countdown = 5
            countdown_start = time.time()
            print(f">>> Fall detected! Countdown started.")

        if event_countdown > 0:
            remaining = int(event_countdown - (time.time() - countdown_start))
            if remaining > 0:
                cv2.putText(
                    frame,
                    f"Alert in {remaining}s",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
            else:
                if current_event_type:
                    try:
                        with app.app_context():
                            event_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"{current_event_type}_{event_time}.jpg"
                            static_dir = os.path.join(
                                os.path.dirname(os.path.dirname(__file__)),
                                "static",
                                "events",
                            )
                            os.makedirs(static_dir, exist_ok=True)
                            image_path = os.path.join(static_dir, filename)
                            web_path = "/static/events/" + filename

                            cv2.imwrite(image_path, frame)

                            event = Event(
                                event_type=current_event_type, image_path=web_path
                            )
                            db.session.add(event)
                            db.session.commit()

                            try:
                                send_email_alert(current_event_type, image_path)
                                alert = Alert(
                                    event_id=event.id,
                                    message=f"Email alert sent for {current_event_type}",
                                    sent_to="admin + caregivers",
                                )
                                db.session.add(alert)
                                db.session.commit()
                                print(f">>> Email alert sent successfully")
                            except Exception as e:
                                print(f"Email error: {e}")

                            try:
                                send_sms_alert(current_event_type)
                                print(f">>> SMS alert sent")
                            except Exception as e:
                                print(f"SMS error (non-critical): {e}")
                    except Exception as e:
                        print(f"Event save error: {e}")

                event_countdown = 0
                current_event_type = None

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        frame_base64 = base64.b64encode(buffer).decode("utf-8")
        socketio.emit("frame", {"image": frame_base64})
        time.sleep(0.1)

    print(">>> Stopping stream")
    if camera:
        camera.release()
        camera = None
    print(">>> Camera released")


@stream.route("/start", methods=["POST"])
def start_stream():
    global is_streaming

    if is_streaming:
        return jsonify({"message": "Stream already running"}), 400

    is_streaming = True
    app = current_app._get_current_object()
    thread = threading.Thread(target=generate_frames, args=(app,), daemon=True)
    thread.start()

    return jsonify({"message": "Stream started"}), 200


@stream.route("/stop", methods=["POST"])
def stop_stream():
    global is_streaming

    if not is_streaming:
        return jsonify({"message": "Stream not running"}), 400

    is_streaming = False

    return jsonify({"message": "Stream stopped"}), 200


@stream.route("/status", methods=["GET"])
def stream_status():
    return jsonify({"is_streaming": is_streaming}), 200
