import cv2
from mediapipe.tasks.python.vision.pose_landmarker import (
    PoseLandmarker,
    PoseLandmarkerOptions,
)
from mediapipe.tasks.python.core.base_options import BaseOptions
import os
import time
from mediapipe import Image, ImageFormat

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


class FallDetector:
    def __init__(self):
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "pose_landmarker.task"
        )
        if not os.path.exists(model_path):
            model_path = "pose_landmarker.task"

        base_options = BaseOptions(model_asset_path=model_path)
        options = PoseLandmarkerOptions(base_options=base_options)
        self.landmarker = PoseLandmarker.create_from_options(options)

        self.consecutive_frames = 0
        self.required_frames = 4
        self.cooldown_duration = 30
        self.last_fall_time = None

    def detect(self, frame):
        if self.last_fall_time is not None:
            elapsed = time.time() - self.last_fall_time
            if elapsed < self.cooldown_duration:
                return frame, False

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect(mp_image)

        detected_this_frame = False

        if result and result.pose_landmarks:
            landmarks = result.pose_landmarks[0]

            h, w = frame.shape[:2]

            for i, landmark in enumerate(landmarks):
                cx, cy = int(landmark.x * w), int(landmark.y * h)
                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)

            for start_idx, end_idx in POSE_CONNECTIONS:
                if start_idx < len(landmarks) and end_idx < len(landmarks):
                    start = landmarks[start_idx]
                    end = landmarks[end_idx]
                    start_pt = (int(start.x * w), int(start.y * h))
                    end_pt = (int(end.x * w), int(end.y * h))
                    cv2.line(frame, start_pt, end_pt, (0, 255, 0), 1)

            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            left_hip = landmarks[23]
            right_hip = landmarks[24]

            if (
                left_shoulder.visibility > 0.5
                and right_shoulder.visibility > 0.5
                and left_hip.visibility > 0.5
                and right_hip.visibility > 0.5
            ):
                avg_shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
                avg_hip_y = (left_hip.y + right_hip.y) / 2
                avg_shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
                avg_hip_x = (left_hip.x + right_hip.x) / 2

                shoulder_hip_y_diff = abs(avg_shoulder_y - avg_hip_y)
                shoulder_hip_x_diff = abs(avg_shoulder_x - avg_hip_x)

                shoulder_hip_y_pixel = shoulder_hip_y_diff * h
                shoulder_hip_x_pixel = shoulder_hip_x_diff * w

                if shoulder_hip_x_pixel > 0:
                    ratio = shoulder_hip_y_pixel / shoulder_hip_x_pixel

                    if ratio < 0.35:
                        detected_this_frame = True
                        center_x = int(avg_shoulder_x * w)
                        center_y = int(avg_shoulder_y * h)
                        cv2.putText(
                            frame,
                            "FALL DETECTED!",
                            (center_x - 80, center_y - 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                        )

        if detected_this_frame:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0

        is_fall = self.consecutive_frames >= self.required_frames

        if is_fall:
            self.consecutive_frames = 0
            self.last_fall_time = time.time()

        return frame, is_fall

    def close(self):
        self.landmarker.close()
