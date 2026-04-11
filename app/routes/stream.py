import cv2
import base64
import os
import time
import threading
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from mediapipe.tasks.python.vision.pose_landmarker import (
    PoseLandmarker,
    PoseLandmarkerOptions,
)
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe import Image, ImageFormat
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

POSE_CONNECTIONS = [
    (11, 12),
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),
    (11, 23),
    (12, 24),
    (23, 24),
    (23, 25),
    (25, 27),
    (24, 26),
    (26, 28),
]


def create_pose_landmarker():
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "..", "pose_landmarker.task"
    )
    if not os.path.exists(model_path):
        model_path = "pose_landmarker.task"
    base_options = BaseOptions(model_asset_path=model_path)
    options = PoseLandmarkerOptions(base_options=base_options)
    return PoseLandmarker.create_from_options(options)


def draw_pose(frame, landmarks, h, w):
    for lm in landmarks:
        cx, cy = int(lm.x * w), int(lm.y * h)
        cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
    for start_idx, end_idx in POSE_CONNECTIONS:
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            s = landmarks[start_idx]
            e = landmarks[end_idx]
            cv2.line(
                frame,
                (int(s.x * w), int(s.y * h)),
                (int(e.x * w), int(e.y * h)),
                (0, 200, 0),
                2,
            )


def save_event_and_alert(app, frame, event_type):
    try:
        with app.app_context():
            event_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{event_type}_{event_time}.jpg"
            static_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "static",
                "events",
            )
            os.makedirs(static_dir, exist_ok=True)
            image_path = os.path.join(static_dir, filename)
            web_path = "/static/events/" + filename

            cv2.imwrite(image_path, frame)

            event = Event(event_type=event_type, image_path=web_path)
            db.session.add(event)
            db.session.commit()

            try:
                send_email_alert(event_type, image_path)
                alert = Alert(
                    event_id=event.id,
                    message=f"Email alert sent for {event_type}",
                    sent_to="admin + caregivers",
                )
                db.session.add(alert)
                db.session.commit()
                print(f">>> Email alert sent successfully")
            except Exception as e:
                print(f"Email error: {e}")

            try:
                send_sms_alert(event_type)
                print(f">>> SMS alert sent")
            except Exception as e:
                print(f"SMS error (non-critical): {e}")
    except Exception as e:
        print(f"Event save error: {e}")


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

    pose_landmarker = create_pose_landmarker()
    print(">>> Pose model loaded, streaming started")

    frame_counter = 0
    countdown_start = 0
    cached_landmarks = None
    cached_hand_gesture = False
    cached_fall = False
    recovery_frames = 0
    RECOVERY_THRESHOLD = 3

    while is_streaming:
        ret, frame = camera.read()
        if not ret or frame is None:
            time.sleep(0.01)
            continue

        clean_frame = frame.copy()

        frame_counter += 1
        is_hand_gesture = False
        is_fall = False

        if frame_counter % 3 == 0:
            try:
                h, w = frame.shape[:2]
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)
                result = pose_landmarker.detect(mp_image)

                if result and result.pose_landmarks:
                    cached_landmarks = result.pose_landmarks[0]
                else:
                    cached_landmarks = None

                frame, cached_hand_gesture = hand_detector.detect(
                    frame, cached_landmarks, h, w
                )
                frame, cached_fall = fall_detector.detect(frame, cached_landmarks, h, w)
                is_hand_gesture = cached_hand_gesture
                is_fall = cached_fall
            except Exception as e:
                print(f"Detection error: {e}")
        else:
            h, w = frame.shape[:2]
            if cached_landmarks:
                draw_pose(frame, cached_landmarks, h, w)
            if cached_hand_gesture:
                cv2.putText(
                    frame,
                    "RAISED HAND",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
            if cached_fall:
                cv2.putText(
                    frame,
                    "FALL DETECTED!",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2,
                )

        if is_hand_gesture and event_countdown == 0:
            current_event_type = "hand_gesture"
            event_countdown = 5
            countdown_start = time.time()
            print(f">>> Hand gesture detected! Countdown started.")
        elif is_fall and event_countdown == 0:
            current_event_type = "fall"
            event_countdown = 5
            countdown_start = time.time()
            recovery_frames = 0
            print(f">>> Fall detected! Countdown started.")

        if event_countdown > 0:
            if current_event_type == "hand_gesture" and not cached_hand_gesture:
                event_countdown = 0
                current_event_type = None
                recovery_frames = 0
                print(f">>> Hand lowered — countdown cancelled.")
            elif current_event_type == "fall":
                if not cached_fall:
                    recovery_frames += 1
                    if recovery_frames >= RECOVERY_THRESHOLD:
                        event_countdown = 0
                        current_event_type = None
                        recovery_frames = 0
                        print(f">>> Person recovered — countdown cancelled.")
                else:
                    recovery_frames = 0

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
                    save_frame = clean_frame.copy()
                    evt_type = current_event_type
                    threading.Thread(
                        target=save_event_and_alert,
                        args=(app, save_frame, evt_type),
                        daemon=True,
                    ).start()
                    if evt_type == "fall":
                        fall_detector.start_cooldown()

                event_countdown = 0
                current_event_type = None

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        frame_base64 = base64.b64encode(buffer).decode("utf-8")
        socketio.emit("frame", {"image": frame_base64})
        time.sleep(0.05)

    print(">>> Stopping stream")
    pose_landmarker.close()
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
    socketio.emit("stream_stopped")

    return jsonify({"message": "Stream stopped"}), 200


@stream.route("/status", methods=["GET"])
def stream_status():
    return jsonify({"is_streaming": is_streaming}), 200
