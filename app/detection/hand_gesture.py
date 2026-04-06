import cv2
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.core.base_options import BaseOptions
import os
from mediapipe import Image, ImageFormat

HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (0, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (0, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (5, 9),
    (9, 13),
    (13, 17),
]


class HandGestureDetector:
    def __init__(self):
        model_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "hand_landmarker.task"
        )
        if not os.path.exists(model_path):
            model_path = "hand_landmarker.task"

        base_options = BaseOptions(model_asset_path=model_path)
        options = HandLandmarkerOptions(base_options=base_options, num_hands=1)
        self.landmarker = HandLandmarker.create_from_options(options)

        self.consecutive_frames = 0
        self.required_frames = 2

        self.fingertip_ids = [8, 12, 16, 20]
        self.knuckle_ids = [5, 9, 13, 17]

    def detect(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect(mp_image)

        detected_this_frame = False

        if result and result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                h, w = frame.shape[:2]

                for i, landmark in enumerate(hand_landmarks):
                    cx, cy = int(landmark.x * w), int(landmark.y * h)
                    cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)

                for start_idx, end_idx in HAND_CONNECTIONS:
                    if start_idx < len(hand_landmarks) and end_idx < len(
                        hand_landmarks
                    ):
                        start = hand_landmarks[start_idx]
                        end = hand_landmarks[end_idx]
                        start_pt = (int(start.x * w), int(start.y * h))
                        end_pt = (int(end.x * w), int(end.y * h))
                        cv2.line(frame, start_pt, end_pt, (0, 255, 0), 1)

                wrist = hand_landmarks[0]
                wrist_y = int(wrist.y * h)
                wrist_x = int(wrist.x * w)

                if wrist_y < h // 2:
                    extended_count = 0
                    for tip_id, knuckle_id in zip(self.fingertip_ids, self.knuckle_ids):
                        fingertip = hand_landmarks[tip_id]
                        knuckle = hand_landmarks[knuckle_id]

                        if fingertip.y < knuckle.y:
                            extended_count += 1

                    print(
                        f"Hand detected: wrist_y={wrist_y}, h/2={h // 2}, extended={extended_count}"
                    )

                    if extended_count >= 3:
                        detected_this_frame = True
                        cv2.putText(
                            frame,
                            "Help Gesture",
                            (wrist_x, wrist_y - 20),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2,
                        )

        if detected_this_frame:
            self.consecutive_frames += 1
        else:
            self.consecutive_frames = 0

        is_help_gesture = self.consecutive_frames >= self.required_frames

        if is_help_gesture:
            self.consecutive_frames = 0

        return frame, is_help_gesture

    def close(self):
        self.landmarker.close()
