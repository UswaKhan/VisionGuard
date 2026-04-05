import cv2
import base64
import os
import threading
from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_socketio import emit
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
streaming_thread = None


def generate_frames():
    global camera, is_streaming, event_countdown, current_event_type

    camera = cv2.VideoCapture(0)

    while is_streaming:
        ret, frame = camera.read()
        if not ret:
            break

        frame, is_hand_gesture = hand_detector.detect(frame)
        frame, is_fall = fall_detector.detect(frame)

        if is_hand_gesture:
            current_event_type = "hand_gesture"
            event_countdown = 5
        elif is_fall:
            current_event_type = "fall"
            event_countdown = 5

        if event_countdown > 0:
            cv2.putText(
                frame,
                f"Alert in {event_countdown}s",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )
            event_countdown -= 1

            if event_countdown == 0 and current_event_type:
                event_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{current_event_type}_{event_time}.jpg"
                static_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)), "static", "events"
                )
                os.makedirs(static_dir, exist_ok=True)
                image_path = os.path.join(static_dir, filename)

                cv2.imwrite(image_path, frame)

                event = Event(event_type=current_event_type, image_path=image_path)
                db.session.add(event)
                db.session.commit()

                try:
                    send_email_alert(current_event_type, image_path)
                except Exception as e:
                    print(f"Error sending email: {e}")

                try:
                    send_sms_alert(current_event_type)
                except Exception as e:
                    print(f"Error sending SMS: {e}")

                current_event_type = None

        ret, buffer = cv2.imencode(".jpg", frame)
        frame_base64 = base64.b64encode(buffer).decode("utf-8")

        socketio.emit("video_frame", {"frame": frame_base64})

    if camera:
        camera.release()
    hand_detector.close()
    fall_detector.close()


@stream.route("/start", methods=["POST"])
def start_stream():
    global is_streaming, streaming_thread

    if is_streaming:
        return jsonify({"message": "Stream already running"}), 400

    is_streaming = True
    streaming_thread = threading.Thread(target=generate_frames)
    streaming_thread.daemon = True
    streaming_thread.start()

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
